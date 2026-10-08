#!/usr/bin/env python3
"""Publish the original Release archive without replacing an existing version."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

import yaml

BASE_URL = "https://chickenlj.github.io/helm-charts"


def publish(archive, version, docs):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError("Expected a Chart version without the v prefix")
    filename = f"agentscope-service-{version}.tgz"
    if archive.name != filename:
        raise ValueError("Archive filename does not match the requested version")
    with tarfile.open(archive, "r:gz") as bundle:
        metadata = yaml.safe_load(bundle.extractfile("agentscope-service/Chart.yaml"))
    if (metadata.get("name"), metadata.get("version"), metadata.get("appVersion")) != (
        "agentscope-service", version, version
    ):
        raise ValueError("Chart name, version or appVersion does not match")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    docs.mkdir(parents=True, exist_ok=True)
    index = docs / "index.yaml"
    existing = yaml.safe_load(index.read_text()) if index.exists() else {"entries": {}}
    previous = next((entry for entry in existing.get("entries", {}).get("agentscope-service", [])
                     if entry["version"] == version), None)
    target = docs / filename
    if previous and previous["digest"] != digest:
        raise ValueError("Refusing to overwrite a published version")
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
        raise ValueError("Refusing to replace an existing archive")
    if previous and target.exists():
        print(f"{filename} already published: {digest}")
        return
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        shutil.copyfile(archive, staging / filename)
        command = ["helm", "repo", "index", str(staging), "--url", BASE_URL]
        if index.exists():
            command += ["--merge", str(index.resolve())]
        subprocess.run(command, check=True)
        generated = yaml.safe_load((staging / "index.yaml").read_text())
        entry = next(e for e in generated["entries"]["agentscope-service"] if e["version"] == version)
        if entry["digest"] != digest or entry["urls"] != [f"{BASE_URL}/{filename}"]:
            raise ValueError("Generated index does not match archive")
        shutil.copyfile(archive, target)
        shutil.copyfile(staging / "index.yaml", index)
    print(f"Published {filename}: {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    args = parser.parse_args()
    publish(args.archive, args.version, args.docs)

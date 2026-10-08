import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

import yaml
from publish import publish


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"

    def archive(self, version, description="test", app_version=None):
        archive = self.root / f"agentscope-service-{version}.tgz"
        metadata = yaml.safe_dump({"apiVersion": "v2", "name": "agentscope-service",
                                   "version": version, "appVersion": app_version or version,
                                   "description": description}).encode()
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("agentscope-service/Chart.yaml")
            member.size = len(metadata)
            bundle.addfile(member, io.BytesIO(metadata))
        return archive

    def test_preserves_history_and_idempotent_republication(self):
        archive = self.archive("2.1.0-BETA1")
        publish(archive, "2.1.0-BETA1", self.docs)
        original = (self.docs / "index.yaml").read_bytes()
        publish(archive, "2.1.0-BETA1", self.docs)
        self.assertEqual((self.docs / "index.yaml").read_bytes(), original)
        publish(self.archive("2.1.0-BETA2"), "2.1.0-BETA2", self.docs)
        entries = yaml.safe_load((self.docs / "index.yaml").read_text())["entries"]["agentscope-service"]
        self.assertEqual({e["version"] for e in entries}, {"2.1.0-BETA1", "2.1.0-BETA2"})
        previous = next(e for e in entries if e["version"] == "2.1.0-BETA1")
        self.assertEqual(previous["digest"], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertTrue((self.docs / archive.name).exists())

    def test_rejects_changed_bytes_for_published_version(self):
        publish(self.archive("2.1.0-BETA1"), "2.1.0-BETA1", self.docs)
        original = (self.docs / "index.yaml").read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            publish(self.archive("2.1.0-BETA1", "changed"), "2.1.0-BETA1", self.docs)
        self.assertEqual((self.docs / "index.yaml").read_bytes(), original)

    def test_rejects_mismatched_app_version(self):
        with self.assertRaisesRegex(ValueError, "appVersion"):
            publish(self.archive("2.1.0-BETA1", app_version="2.0.0"), "2.1.0-BETA1", self.docs)
        self.assertFalse((self.docs / "index.yaml").exists())


if __name__ == "__main__":
    unittest.main()

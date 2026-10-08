# AgentScope Helm repository

Public Helm Charts for [AgentScope Service](https://github.com/agentscope-ai/agentscope-java).
Chart archives are copied unchanged from the upstream GitHub Release. Existing
versions are immutable and previous index entries are retained.

```bash
helm repo add agentscope https://chickenlj.github.io/helm-charts
helm repo update agentscope
helm search repo agentscope/agentscope-service --versions --devel
```

After preparing PostgreSQL, shared RWX storage and the `agentscope-service` Secret:

```bash
helm upgrade --install service agentscope/agentscope-service \
  --version 2.1.0-BETA1 --namespace agentscope \
  --set imageRepository=sca-registry.cn-hangzhou.cr.aliyuncs.com/agentscope \
  --set existingSecret=agentscope-service \
  -f production-values.yaml --wait --timeout 10m
```

The repository needs no registry authentication. Private container images still
require Kubernetes `imagePullSecrets`. Database, storage, credentials and TLS are
operated by the installer; this command alone does not provision them.
See the [installation guide](https://java.agentscope.io/v2/en/service/kubernetes).
Versioned [environment and SQL examples](docs/examples/2.1.0-BETA1/) contain placeholders only.

## Publish another release

First publish `agentscope-service-VERSION.tgz` in the upstream `vVERSION` Release.
Then run **Actions → Publish Helm repository → Run workflow**, on `main`, with
`version` set to the Chart version without the `v` prefix. Or:

```bash
gh workflow run publish.yml --repo chickenlj/helm-charts --ref main \
  -f version=2.1.0-BETA1
```

The workflow checks the upstream SHA256 and Chart metadata, refuses to overwrite
different bytes under an existing version, merges the index, commits new files,
and deploys GitHub Pages in the same run. No additional secret or account is needed.
For a new version, add matching placeholder files under `docs/examples/VERSION/`
if deployment configuration changes. Do not put private environment files here.

Local publication requires Python with `PyYAML==6.0.3` and Helm:

```bash
python scripts/publish.py /path/agentscope-service-2.1.0-BETA1.tgz --version 2.1.0-BETA1
```

GitHub Pages serves `docs/` through the workflow, with HTTPS. Archive URLs in
`index.yaml` are absolute, so the official website can redirect only
`/helm/index.yaml` to the Pages index without proxying individual archives.

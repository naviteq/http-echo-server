# http-echo-server

A simple HTTP server that echoes request details and exposes Kubernetes Downward API data. Useful for debugging, demos, and testing ingress/proxy behavior. Packaged as a Docker image and a Helm chart that consumes [`naviteq/helm-library`](https://github.com/naviteq/helm-library).

[![CI](https://github.com/naviteq/http-echo-server/actions/workflows/pullrequest.yaml/badge.svg)](https://github.com/naviteq/http-echo-server/actions/workflows/pullrequest.yaml)
[![Helm](https://img.shields.io/badge/Helm-%E2%89%A53.12-0F1689?logo=helm&logoColor=white)](https://helm.sh)
[![Image](https://img.shields.io/badge/image-ghcr.io%2Fnaviteq%2Fhttp--echo--server-blue?logo=github)](https://github.com/naviteq/http-echo-server/pkgs/container/http-echo-server)

> [!NOTE]
> **For debugging, demos, and testing only.** This server echoes request details — it is not meant to handle production traffic.

## Features

- **Request echo** — Returns method, headers, query params, JSON body, and form data
- **Client IP & geo** — Resolves client IP (including `X-Forwarded-For`) and optional geo info via [ip-api.com](http://ip-api.com)
- **Kubernetes Downward API** — Exposes pod metadata (name, namespace, labels, annotations, resource limits/requests) when run in Kubernetes
- **JSON logging** — Structured JSON logs to stdout

## Requirements

- Python 3.11+ (for local run) or Docker
- For Kubernetes: Helm 3, cluster with optional Ingress and cert-manager

## Quick start (local)

### Using Docker

```bash
docker build -t http-echo-server ./app
docker run -p 5000:5000 http-echo-server
```

Then open `http://localhost:5000`.

### Using Python

```bash
cd app
pip install -r requirements.txt
python app.py
```

Default: `http://0.0.0.0:5000`. Override with:

- `SERVER_HOST` — bind address (default: `0.0.0.0`)
- `SERVER_PORT` — port (default: `5000`)
- `DOWNWARD_PATH` — path to Downward API files (default: `/etc/k8s`; only used when files exist)

---

## Install on Kubernetes (Helm)

The chart is published as an OCI artifact to GitHub Container Registry.

### Add the Helm OCI registry (optional)

```bash
helm registry login ghcr.io
# Use a GitHub Personal Access Token with read:packages when prompted
```

### Install from OCI

```bash
helm install echo-server oci://ghcr.io/naviteq/http-echo-server/http-echo-server \
  --namespace echo-server \
  --create-namespace 
```

### Access the app

- **ClusterIP (default):**  
  `kubectl port-forward -n echo-server svc/echo-server-http-echo-server 8080:5000`  
  Then open `http://127.0.0.1:8080`.
- **With Ingress:** use the host you configured (e.g. `https://echo.example.com`).

### Verify the install

```bash
helm test echo-server -n echo-server
```

Runs a one-shot Pod that wgets the service to confirm reachability. Pass = service routes traffic correctly.

---

## Helm values

This chart consumes `naviteq/helm-library` via `import-values: [defaults]` and only documents the values **this chart sets or overrides**. For the full inherited schema (sidecars, scheduling, security contexts, probes, etc.) see the [helm-library values reference](https://github.com/naviteq/helm-library/blob/main/chart/README.md).

| Key | Default | Description |
|---|---|---|
| `image.registry` | `ghcr.io` | Container registry |
| `image.repository` | `naviteq/http-echo-server` | Image path |
| `image.tag` | `""` (falls back to `appVersion`) | Image tag |
| `image.pullPolicy` | `IfNotPresent` | Image pull policy |
| `ports[0].containerPort` | `5000` | Container port the app listens on (library default is `8080`) |
| `service.type` | `ClusterIP` | Service type |
| `service.ports[0].port` / `targetPort` | `5000` / `http` | Service port mapping |
| `ingress.enabled` | `false` | Enable Ingress (uses `hostname` + `extraHosts[]`, not list-of-hosts) |
| `ingress.hostname` | `chart-example.local` | Primary host when ingress is enabled |
| `livenessProbe` / `readinessProbe` | `enabled: true`, `httpGet /` on `http` | HTTP probes against `/` |
| `resources.requests.cpu` / `memory` | `100m` / `128Mi` | Resource requests |
| `resources.limits.memory` | `128Mi` | Memory limit |
| `autoscaling.enabled` | `true` | Enable HPA |
| `autoscaling.minReplicas` / `maxReplicas` | `1` / `3` | HPA replica range |
| `autoscaling.targetCPU` / `targetMemory` | `80` / `80` | HPA target utilization (%) |
| `pdb.create` | `false` | PodDisruptionBudget rendering is suppressed |
| `serviceAccount.create` | `false` | Create a dedicated ServiceAccount |
| `envVars` (map) | `DOWNWARD_PATH: /etc/k8s`, `SERVER_PORT: "5000"` | App environment (note: map form, not the K8s list-of-{name,value} form) |
| `extraVolumes` / `extraVolumeMounts` | Downward API volume mounted at `/etc/k8s` | 14 paths covering pod metadata, resource requests/limits, hugepages, ephemeral storage |

---

## Configuration

| Environment variable | Description                    | Default     |
| -------------------- | ------------------------------ | ----------- |
| `SERVER_HOST`        | Bind address                   | `0.0.0.0`   |
| `SERVER_PORT`        | HTTP port                      | `5000`      |
| `DOWNWARD_PATH`      | Path to Downward API files     | `/etc/k8s`  |

---

## API

- **`GET|POST|PUT|PATCH|DELETE /`** — Returns JSON with:
  - `method`, `headers`, `query_params`, `json_body`, `form_data`
  - `server_ip`, `original_ip` (from `X-Forwarded-For`), `geo_info`
  - `kubernetes` — Downward API data when running in K8s (pod name, namespace, labels, annotations, resource limits/requests)

---

## Image distribution

The container image is published to **GitHub Container Registry (GHCR)** on every release.

| Detail | Value |
|---|---|
| Registry | `ghcr.io` |
| Image | `ghcr.io/naviteq/http-echo-server` |
| Tag format | `vMAJOR.MINOR.PATCH` (image tag drops the `v` prefix that git tags carry) |
| Available tags | See [GHCR package page](https://github.com/naviteq/http-echo-server/pkgs/container/http-echo-server) |

Releases are automated: merges to `main` with Conventional Commits accumulate, then a release PR bumps `Chart.yaml`'s `version` / `appVersion` and tags `vX.Y.Z`. The tag triggers [`.github/workflows/release.yaml`](./.github/workflows/release.yaml), which builds and pushes the image to GHCR and the Helm chart to `oci://ghcr.io/naviteq/http-echo-server/http-echo-server`.

### Consuming the Helm chart

```yaml
# In your Chart.yaml
dependencies:
  - name: http-echo-server
    version: 0.6.1
    repository: oci://ghcr.io/naviteq/http-echo-server
```

Or install directly:

```bash
helm install <release> \
  oci://ghcr.io/naviteq/http-echo-server/http-echo-server \
  --version 0.6.1
```

---

## Troubleshooting / known limits

- **Image pull errors with `:vX.Y.Z` tag** — Docker image tags do **not** include the `v` prefix even though git tags do (`v0.6.1` git tag → `0.6.1` image). Set `image.tag: "0.6.1"` explicitly (without the `v`). Leaving `image.tag: ""` falls back to `appVersion` which currently still carries the `v` and will fail to pull.
- **Helm 4 OCI mediatype error** — Helm 4 cannot read charts pushed by Helm 3. Use Helm 3 (≥ 3.12) to install this chart.
- **OCI install URL** — the chart-name suffix is required: `oci://ghcr.io/naviteq/http-echo-server/http-echo-server`. Omitting the trailing `http-echo-server` returns a mediatype error.
- **Ingress hostname schema** — the chart consumes `naviteq/helm-library`, whose ingress takes a single `hostname` + optional `extraHosts[]` / `extraTls[]`, not the older `hosts[].paths[]` array form. Override `ingress.hostname` to set the primary host.

---

## Development

- **Lint / hooks:** `.pre-commit-config.yaml`
- **CI:** GitHub Actions build the Docker image and publish the Helm chart (see `.github/workflows/`). Releases are created on version tags (`v*.*.*`). Actions are pinned by 40-char commit SHA; updates are managed by Renovate (see `renovate.json`).

## Contributing

Contributions welcome via pull request. The chart is a thin consumer of [`naviteq/helm-library`](https://github.com/naviteq/helm-library) — any chart-level changes (resource types, defaults, value names) should generally land there, not here.

## License

See [LICENSE](LICENSE).

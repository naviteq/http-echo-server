# http-echo-server

A simple HTTP server that echoes request details and exposes Kubernetes Downward API data. Useful for debugging, demos, and testing ingress/proxy behavior.

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

## Configuration

| Environment variable | Description                    | Default     |
| -------------------- | ------------------------------ | ----------- |
| `SERVER_HOST`        | Bind address                   | `0.0.0.0`   |
| `SERVER_PORT`        | HTTP port                      | `5000`      |
| `DOWNWARD_PATH`      | Path to Downward API files     | `/etc/k8s`  |

Helm values (see `helm/values.yaml`): replica count, image, resources, ingress, autoscaling (HPA), and Downward API volume mounts.

## API

- **`GET|POST|PUT|PATCH|DELETE /`** — Returns JSON with:
  - `method`, `headers`, `query_params`, `json_body`, `form_data`
  - `server_ip`, `original_ip` (from `X-Forwarded-For`), `geo_info`
  - `kubernetes` — Downward API data when running in K8s (pod name, namespace, labels, annotations, resource limits/requests)

## Development

- **Lint / hooks:** `.pre-commit-config.yaml`
- **CI:** GitHub Actions build the Docker image and publish the Helm chart (see `.github/workflows/`). Releases are created on version tags (`v*.*.*`).

## License

See [LICENSE](LICENSE).

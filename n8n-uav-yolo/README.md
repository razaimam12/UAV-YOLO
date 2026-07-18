# n8n UAV YOLO

Importable **n8n** workflows for UAV surveillance detection. They call the Python YOLO detector over HTTP (no Python runtime inside n8n).

## Workflows

| File | Purpose |
|------|---------|
| [`workflow/UAV-Surveillance-Agent.json`](workflow/UAV-Surveillance-Agent.json) | Webhook → YOLO `/predict` → alert JSON |
| [`workflow/UAV-Surveillance-Agent-Python-Touch.json`](workflow/UAV-Surveillance-Agent-Python-Touch.json) | Same flow + `POST /enrich` risk scoring on the detector |

## Prerequisites

1. **Detector running** from [`../python-uav-yolo`](../python-uav-yolo/) on Docker network `uav-net` (hostname `detector`, port `8000`).
2. **n8n** on the same network:

```bash
docker network create uav-net
# ensure n8n container is connected:
docker network connect uav-net n8n
```

3. From n8n, the detector URL is `http://detector:8000` (not `localhost`).

## Import

1. Open n8n → **Workflows** → **Import from File**.
2. Choose one of the JSON files under `workflow/`.
3. Activate the workflow.
4. Test:

```bash
curl -X POST "http://localhost:5678/webhook/uav-detect" \
  -F "file=@../python-uav-yolo/samples/street.jpg"
```

## Endpoints used

| Detector | Method | Role |
|----------|--------|------|
| `/health` | GET | Liveness |
| `/predict` | POST (multipart file) | YOLO detections |
| `/enrich` | POST (JSON) | Python risk enrichment (Python-Touch workflow) |

## Notes

- Official n8n images typically **do not include Python**, so native Python Code nodes are not used.
- The “Python touch” is the HTTP call to the detector’s `/enrich` endpoint.

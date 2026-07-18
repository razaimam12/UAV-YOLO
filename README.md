# UAV YOLO — Dual Method Repository

Real-time UAV / aerial surveillance object detection with **YOLOv8**, exposed two ways:

| Folder | Method | What it contains |
|--------|--------|------------------|
| [`python-uav-yolo/`](python-uav-yolo/) | Python API | FastAPI + YOLOv8 detector, Docker, SOC dashboard samples, risk rules |
| [`n8n-uav-yolo/`](n8n-uav-yolo/) | n8n workflow | Importable n8n agent workflows that call the detector over HTTP |

Use **Python** for the inference service. Use **n8n** for no-code orchestration, webhooks, and alerts.

## Architecture

```
Image / webhook
      │
      ▼
┌─────────────────┐     POST /predict      ┌──────────────────┐
│  n8n workflow   │ ─────────────────────► │  Python detector │
│  (optional)     │     POST /enrich       │  FastAPI + YOLO  │
└─────────────────┘ ◄───────────────────── └──────────────────┘
      │                                            │
      ▼                                            ▼
  Alert JSON                              SOC dashboard (samples/)
```

## Quick start

### 1) Python detector

```bash
cd python-uav-yolo
# Download weights (once):
# https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
# save as weights/yolov8n.pt

docker network create uav-net   # once, if using n8n on the same network
docker compose -f docker-compose.cpu.yml up --build -d
```

API: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2) n8n workflows

1. Run [n8n](https://n8n.io/) (Docker recommended) on the same `uav-net` network.
2. Import a JSON from `n8n-uav-yolo/workflow/`.
3. Activate the workflow and `POST` an image to `/webhook/uav-detect`.

See [`n8n-uav-yolo/README.md`](n8n-uav-yolo/README.md) for details.

### 3) SOC dashboard (optional)

From `python-uav-yolo/samples/`:

```bash
python -m http.server 8765
# open http://127.0.0.1:8765/uav-detect-result.html
```

## License

MIT — see [`python-uav-yolo/LICENSE`](python-uav-yolo/LICENSE).

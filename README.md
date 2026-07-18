# UAV YOLO Surveillance Agent

An AI-powered **UAV / aerial surveillance** demo that runs **real-time multi-object detection** (YOLOv8) and returns structured alerts with latency/FPS, risk scoring, and an optional SOC-style dashboard. It ships as **n8n workflow + Python FastAPI** implementations — the same dual-method pattern as the EMR SOAP Draft Agent.

> **Research / demo disclaimer:** This is a systems demo for real-time detection pipelines (model → API → orchestration → UI). It is not a production security product. Always validate detections before operational use.

---

## Repository structure (two methods)

This repository ships **two complementary ways** to run UAV YOLO detection. You can use either or both together (n8n calls the Python detector over HTTP).

| Folder | Method | Technology stack | Best for |
| --- | --- | --- | --- |
| [`n8n-uav-yolo/`](./n8n-uav-yolo) | **Method A — n8n** | n8n (low-code workflow), webhook upload, HTTP to detector, alert JSON | Visual automation, webhook alerts, Docker self-hosting with n8n |
| [`python-uav-yolo/`](./python-uav-yolo) | **Method B — Python** | **FastAPI** (not Flask), Uvicorn, Ultralytics YOLOv8, PyTorch, risk rules, Docker, SOC UI samples | Standalone inference API, enrich endpoint, live WebSocket stream, local demos |

Default detector model: **YOLOv8n** (Ultralytics). Download weights once into `python-uav-yolo/weights/yolov8n.pt` (gitignored).

---

## Features (both methods)

- YOLOv8 multi-object detection on uploaded UAV / street frames
- Structured JSON output: class, confidence, bounding box, count
- Per-frame **latency (ms)** and **FPS** instrumentation
- Priority / alert summary from detections (e.g. person → HIGH)
- Python **risk enrichment** (`/enrich`) for Critical / Elevated / Moderate scoring
- n8n webhook orchestration (`POST /webhook/uav-detect`)
- Optional **SOC dashboard** (live WebSocket stream, tracks, alerts, export)
- Docker Compose CPU stack on shared network `uav-net` with n8n
- Health check + OpenAPI docs at `/docs`

---

## Architecture

```
Image upload / webhook
        │
        ▼
┌───────────────────┐     POST /predict      ┌─────────────────────┐
│  Method A — n8n   │ ─────────────────────► │  Method B — Python  │
│  UAV workflow     │     POST /enrich       │  FastAPI + YOLOv8   │
└───────────────────┘ ◄───────────────────── └─────────────────────┘
        │                                              │
        ▼                                              ▼
   Alert JSON                                 SOC dashboard (samples/)
```

n8n does **not** run Python inside Code nodes. The “Python touch” is an HTTP call to the FastAPI detector (`/predict`, `/enrich`).

---

## Prerequisites (both methods)

1. **Docker Desktop** (recommended) **or** Python 3.10+
2. YOLOv8n weights file (`yolov8n.pt`) — see Method B Step 2
3. For Method A: n8n container on Docker network `uav-net`
4. Browser: Chrome or Edge (for the SOC dashboard)

Never commit large weight files or secrets. Weights are gitignored.

---

# Method A — n8n folder (step by step)

**Folder:** `n8n-uav-yolo/`  
**What it is:** An n8n workflow that accepts an image on a webhook, calls the Python YOLO detector, and returns an alert JSON. Optional “Python Touch” workflow also calls `/enrich` for risk scoring.

### Step 1 — Start the Python detector (required)

n8n calls `http://detector:8000`. Start Method B first (see below), or at minimum:

```bash
cd python-uav-yolo
docker network create uav-net
docker compose -f docker-compose.cpu.yml up --build -d
```

### Step 2 — Start n8n with Docker

```bash
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

Connect n8n to the same network:

```bash
docker network connect uav-net n8n
```

Open <http://localhost:5678> and create your n8n owner account.

### Step 3 — Import the workflow

1. Open **Workflows → ⋮ → Import from File**
2. Select one of:
   - `n8n-uav-yolo/workflow/UAV-Surveillance-Agent.json`
   - `n8n-uav-yolo/workflow/UAV-Surveillance-Agent-Python-Touch.json` (includes `/enrich`)
3. Toggle the workflow **Active**

### Step 4 — Test the webhook

```bash
curl -X POST "http://localhost:5678/webhook/uav-detect" \
  -F "file=@python-uav-yolo/samples/street.jpg"
```

### n8n API endpoints

| Method + Path | Purpose |
| --- | --- |
| `POST /webhook/uav-detect` | Upload image → YOLO detect → alert JSON |

More detail: [`n8n-uav-yolo/README.md`](./n8n-uav-yolo/README.md)

---

# Method B — Python folder (step by step)

**Folder:** `python-uav-yolo/`  
**What it is:** A standalone **FastAPI** inference service (this project does **not** use Flask).

### Tech stack used in the Python folder

| Package / tool | Role |
| --- | --- |
| **FastAPI** | Main web framework (REST + WebSocket) |
| **Uvicorn** | ASGI server that runs the FastAPI app |
| **Ultralytics YOLOv8** | Object detection model |
| **PyTorch** | Model runtime |
| **Pillow / NumPy** | Image loading and arrays |
| **Docker / docker-compose** | One-command detector deploy |
| **pytest** | Unit tests for risk rules (`tests/`) |
| **HTML / JavaScript** | Optional SOC dashboard under `samples/` |

### Step 1 — Open the folder

```bash
cd python-uav-yolo
```

### Step 2 — Download YOLOv8n weights

```bash
mkdir -p weights
curl -L -o weights/yolov8n.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
```

### Step 3 — Run with Docker (recommended)

```bash
docker network create uav-net
docker compose -f docker-compose.cpu.yml up --build -d
```

API docs: <http://localhost:8000/docs>  
Health: <http://localhost:8000/health>

### Step 4 — Or run locally with Python

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### Step 5 — Call the API

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@samples/street.jpg"
```

CLI detect with FPS:

```bash
python src/detect.py --source samples/street.jpg --show-fps
```

### Step 6 — Open the SOC dashboard (optional)

```bash
cd samples
python -m http.server 8765
```

Open: <http://127.0.0.1:8765/uav-detect-result.html>

### Python API endpoints

| Method + Path | Purpose |
| --- | --- |
| `GET  /health` | Liveness / readiness |
| `GET  /api/meta` | Model metadata for SOC UI |
| `POST /predict` | Image upload → detections JSON |
| `POST /enrich` | Risk scoring on detection payload |
| `WS   /ws/stream` | Live detection stream for the dashboard |

More detail: [`python-uav-yolo/README.md`](./python-uav-yolo/README.md)

---

## Quick comparison

| | Method A (n8n) | Method B (Python) |
| --- | --- | --- |
| Entry point | Webhook `/webhook/uav-detect` | FastAPI `:8000` |
| Runs YOLO | No (calls detector) | Yes |
| Risk enrich | Optional (Python-Touch workflow) | Built-in `/enrich` |
| Best demo | Automation + alerts | Inference API + SOC UI |

---

## License

MIT — see [`python-uav-yolo/LICENSE`](./python-uav-yolo/LICENSE).

---

*Author: Raza — MS Information Technology, RHCSA. 18 years in server/platform management, containers, orchestration, and networking.*

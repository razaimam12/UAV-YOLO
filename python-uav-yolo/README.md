# UAV YOLO Surveillance Agent — Python (FastAPI) Method

Standalone **Python** implementation of the UAV YOLO Surveillance Agent.

> This project uses **FastAPI** (with **Uvicorn**). It does **not** use Flask.

> **Disclaimer:** Demo / research use. Validate detections before any operational decision.

---

## Technology stack

| Component | What we use | Why |
| --- | --- | --- |
| Web framework | **FastAPI** | Modern async Python API + WebSocket |
| Server | **Uvicorn** | Runs the FastAPI ASGI app |
| Detection | **Ultralytics YOLOv8** | Real-time multi-object detection |
| Runtime | **PyTorch** | Model inference |
| Imaging | **Pillow**, **NumPy** | Load and process frames |
| Risk logic | **`risk_rules.py`** | Critical / Elevated / Moderate scoring |
| Containers | **Docker / docker-compose** | Reproducible CPU (or GPU) deploy |
| Tests | **pytest** | Risk-rule unit tests |
| Dashboard | **HTML + JavaScript** | Optional SOC UI in `samples/` |

---

## Project layout

```
python-uav-yolo/
├── src/
│   ├── app.py              # FastAPI: /predict, /enrich, /ws/stream
│   ├── detect.py           # CLI detection + FPS
│   └── risk_rules.py       # Risk scoring helpers
├── samples/
│   ├── street.jpg          # Sample frame
│   ├── uav-detect-result.html
│   └── soc-engine.js       # SOC dashboard engine
├── tests/
│   └── test_risk_rules.py
├── weights/                # Put yolov8n.pt here (gitignored)
├── Dockerfile
├── Dockerfile.cpu
├── docker-compose.yml
├── docker-compose.cpu.yml
├── requirements.txt
└── LICENSE
```

---

## Step-by-step setup

### 1. Open the folder

```bash
cd python-uav-yolo
```

### 2. Download weights

```bash
mkdir -p weights
curl -L -o weights/yolov8n.pt \
  https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
```

### 3A. Docker CPU (recommended with n8n)

```bash
docker network create uav-net
docker compose -f docker-compose.cpu.yml up --build -d
```

### 3B. Local Python

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

### 4. Verify

- Docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@samples/street.jpg"
```

CLI:

```bash
python src/detect.py --source samples/street.jpg --show-fps
```

### 5. SOC dashboard (optional)

```bash
cd samples
python -m http.server 8765
```

Open: <http://127.0.0.1:8765/uav-detect-result.html>

---

## API endpoints

| Method + Path | Purpose |
| --- | --- |
| `GET  /health` | Liveness / readiness |
| `GET  /api/meta` | Model metadata for SOC UI |
| `POST /predict` | Image upload → detections JSON |
| `POST /enrich` | Risk scoring on detection payload |
| `WS   /ws/stream` | Live detection stream |

---

## Roadmap (research direction)

- [ ] Fine-tune on aerial small-object datasets (VisDrone, DOTA)
- [ ] Export to ONNX / TensorRT for NVIDIA Jetson edge deployment
- [ ] Kubernetes deployment with GPU scheduling + horizontal autoscaling
- [ ] Automated retrain → evaluate → roll-out pipeline

---

*Author: Raza — MS Information Technology, RHCSA. 18 years in server/platform management, containers, orchestration, and networking.*

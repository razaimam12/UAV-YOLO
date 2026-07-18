# UAV YOLO Surveillance Agent — n8n Method

Self-hosted **[n8n](https://n8n.io)** implementation of the UAV YOLO Surveillance Agent (visual low-code workflow + webhook alerts).

This is **Method A** in the root README. The detector itself lives in the **Python FastAPI** folder (`../python-uav-yolo`).

> **Disclaimer:** Demo / research use. Validate detections before any operational decision.

---

## Technology stack (n8n method)

| Component | What we use |
| --- | --- |
| Orchestration | **n8n** workflow (webhook → HTTP detect → alert JSON) |
| Detector | Python FastAPI YOLO service at `http://detector:8000` |
| Optional enrich | `POST /enrich` on the same detector (Python-Touch workflow) |
| Runtime | **Docker** (recommended) or any n8n host |

---

## What's inside

```
n8n-uav-yolo/
├── workflow/
│   ├── UAV-Surveillance-Agent.json              # Webhook → /predict → alert
│   └── UAV-Surveillance-Agent-Python-Touch.json  # + /enrich risk scoring
└── README.md
```

## The workflow

1. **Webhook** accepts a multipart image (`file`)
2. **HTTP Request** posts the image to `http://detector:8000/predict`
3. Nodes build an **alert** (priority, summary, detections, latency/FPS)
4. **Python-Touch variant** also posts the result to `http://detector:8000/enrich` for risk levels

Official n8n images typically **do not include Python**. Native Python Code nodes are not used; the “Python touch” is HTTP to FastAPI.

---

## Step-by-step setup

### 1. Run the Python detector

```bash
cd ../python-uav-yolo
docker network create uav-net
# place weights at weights/yolov8n.pt first
docker compose -f docker-compose.cpu.yml up --build -d
```

### 2. Run n8n

```bash
docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
docker network connect uav-net n8n
```

### 3. Import and activate

1. n8n → **Workflows → Import from File**
2. Import a JSON from `workflow/`
3. Toggle **Active**

### 4. Test

```bash
curl -X POST "http://localhost:5678/webhook/uav-detect" \
  -F "file=@../python-uav-yolo/samples/street.jpg"
```

## Endpoints used on the detector

| Detector | Method | Role |
| --- | --- | --- |
| `/health` | GET | Liveness |
| `/predict` | POST (multipart file) | YOLO detections |
| `/enrich` | POST (JSON) | Risk enrichment (Python-Touch workflow) |

From inside n8n, use hostname **`detector`** (not `localhost`).

# UAV Real-Time Multi-Object Detection (Demo)

A containerized, real-time multi-object detection service for UAV / aerial
surveillance footage. Built with **YOLOv8 (Ultralytics)**, served through a
**FastAPI** inference API, and packaged to run reproducibly in **Docker** — a
minimal, working slice of a larger research system on real-time AI-based
multi-object detection and classification for UAV surveillance.

This repository is intentionally small. Its purpose is to demonstrate an
end-to-end path from model → optimized inference → containerized service,
with latency/FPS instrumentation, which is the systems foundation any
*real-time* UAV pipeline depends on.

## What it does

- Runs YOLOv8 object detection on an image, a video file, or a live stream.
- Reports **per-frame latency and FPS**, so real-time performance is measurable.
- Exposes a **FastAPI `/predict` endpoint** that returns detections as JSON.
- Ships as a **Docker image** and a `docker-compose` stack for one-command run.

## Architecture

```
          ┌─────────────┐     ┌──────────────┐     ┌────────────────┐
 input →  │  Pre-proc   │ →   │  YOLOv8      │ →   │  Post-proc /   │ → detections
 frame    │  (resize)   │     │  inference   │     │  annotate      │   + latency
          └─────────────┘     └──────────────┘     └────────────────┘
                                     │
                                     ▼
                        FastAPI service  →  Docker  →  (Kubernetes-ready)
```

## Quick start

### Option A — Docker (recommended)

```bash
docker compose up --build
# API now live at http://localhost:8000/docs
```

### Option B — Local Python

```bash
pip install -r requirements.txt
python src/detect.py --source samples/street.jpg --show-fps
```

## Usage

Detect on an image and print timing:

```bash
python src/detect.py --source path/to/aerial.jpg --model yolov8n.pt --show-fps
```

Detect on a video / RTSP stream:

```bash
python src/detect.py --source rtsp://your-drone-stream --model yolov8n.pt
```

Call the running API:

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@samples/street.jpg"
```

## Roadmap (research direction)

- [ ] Fine-tune on aerial small-object datasets (VisDrone, DOTA).
- [ ] Export to ONNX / TensorRT for NVIDIA Jetson edge deployment.
- [ ] Kubernetes deployment with GPU scheduling + horizontal autoscaling.
- [ ] Automated retrain → evaluate → roll-out pipeline.

## Tech stack

Python · PyTorch · Ultralytics YOLOv8 · FastAPI · Docker · (Kubernetes-ready)

---

*Author: Raza — MS Information Technology, RHCSA. 18 years in server/platform
management, containers, orchestration, and networking.*

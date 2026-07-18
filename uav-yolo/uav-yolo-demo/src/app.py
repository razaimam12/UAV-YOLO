"""
FastAPI inference service wrapping YOLOv8 for UAV surveillance.

Exposes:
    GET  /health   -> liveness/readiness probe (Kubernetes-friendly)
    POST /predict  -> upload an image, get detections as JSON

Run locally:
    uvicorn src.app:app --host 0.0.0.0 --port 8000
Then open http://localhost:8000/docs
"""
import io
import time

import numpy as np
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from ultralytics import YOLO

app = FastAPI(
    title="UAV Object Detection API",
    description="Real-time multi-object detection for UAV surveillance (demo)",
    version="0.1.0",
)

# Loaded once at startup; weights auto-download on first run.
model = YOLO("yolov8n.pt")


@app.get("/health")
def health():
    return {"status": "ok", "classes": len(model.names)}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    raw = await file.read()
    image = Image.open(io.BytesIO(raw)).convert("RGB")

    t0 = time.perf_counter()
    results = model.predict(np.array(image), conf=0.25, verbose=False)
    latency_ms = (time.perf_counter() - t0) * 1000

    r = results[0]
    detections = [
        {
            "class": model.names[int(b.cls)],
            "confidence": round(float(b.conf), 3),
            "box_xyxy": [round(v, 1) for v in b.xyxy[0].tolist()],
        }
        for b in r.boxes
    ]
    return {
        "count": len(detections),
        "latency_ms": round(latency_ms, 1),
        "fps": round(1000 / latency_ms, 1) if latency_ms else None,
        "detections": detections,
    }

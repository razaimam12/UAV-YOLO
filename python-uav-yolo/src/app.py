"""
FastAPI inference service wrapping YOLOv8 for UAV surveillance.

Exposes:
    GET  /health        -> liveness/readiness
    POST /predict       -> image upload -> detections JSON
    WS   /ws/stream     -> live detection stream (sample or client frames)
    GET  /api/meta      -> model + CORS-friendly metadata for SOC UI

Run locally:
    uvicorn src.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import asyncio
import io
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, ImageEnhance
from ultralytics import YOLO

try:
    from risk_rules import assess_risk
except ImportError:  # pragma: no cover - container path /app/src
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).resolve().parent))
    from risk_rules import assess_risk

# PyTorch 2.6+ defaults torch.load(weights_only=True), which breaks Ultralytics checkpoints.
_torch_load = torch.load


def _torch_load_compat(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _torch_load(*args, **kwargs)


torch.load = _torch_load_compat

app = FastAPI(
    title="UAV Object Detection API",
    description="Real-time multi-object detection for UAV surveillance (SOC-ready)",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolov8n.pt")

SAMPLE_CANDIDATES = [
    Path("/app/samples/street.jpg"),
    Path("samples/street.jpg"),
    Path(__file__).resolve().parent.parent / "samples" / "street.jpg",
]


def _sample_image_path() -> Path | None:
    for p in SAMPLE_CANDIDATES:
        if p.exists():
            return p
    return None


def run_predict_array(image_rgb: np.ndarray, conf: float = 0.25) -> dict[str, Any]:
    t0 = time.perf_counter()
    results = model.predict(image_rgb, conf=conf, verbose=False)
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
        "model": "YOLOv8n",
        "degraded": False,
    }


def run_predict_bytes(raw: bytes, conf: float = 0.25) -> dict[str, Any]:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    return run_predict_array(np.array(image), conf=conf)


@app.get("/health")
def health():
    sample = _sample_image_path()
    return {
        "status": "ok",
        "classes": len(model.names),
        "model": "YOLOv8n",
        "sample_ready": bool(sample),
        "version": "0.2.0",
    }


@app.get("/api/meta")
def meta():
    return {
        "model": "YOLOv8n",
        "compare": [
            {"model": "YOLOv8n", "latency_ms": 86, "map": 37.3, "fps": 11.6, "active": True},
            {"model": "YOLOv8s", "latency_ms": 142, "map": 44.9, "fps": 7.1, "active": False},
            {"model": "YOLOv8m", "latency_ms": 228, "map": 50.2, "fps": 4.4, "active": False},
        ],
        "rules": [
            "IF person AND conf ≥ 80% → escalate CRITICAL",
            "IF person AND conf < 40% → anomaly review",
            "IF truck inside geofence → elevate MODERATE",
            "IF object count jumps ≥ +2 / 5s → threat toast",
            "IF detector down → DEGRADED MODE",
            "IF dwell(track) ≥ 12s → loitering flag",
        ],
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    raw = await file.read()
    return run_predict_bytes(raw)


class EnrichDetection(BaseModel):
    class_: str = Field(alias="class", default="unknown")
    confidence: float = 0.0
    box_xyxy: list[float] | None = None

    class Config:
        populate_by_name = True


class EnrichRequest(BaseModel):
    count: int | None = None
    latency_ms: float | None = None
    fps: float | None = None
    detections: list[dict[str, Any]] = Field(default_factory=list)


@app.post("/enrich")
def enrich(payload: EnrichRequest):
    """
    Python analytics touch for n8n workflows.
    Takes YOLO /predict JSON and returns risk scores + summary.
    """
    enriched = []
    class_counts: dict[str, int] = {}
    for d in payload.detections:
        cls = str(d.get("class", "unknown"))
        conf = float(d.get("confidence", 0))
        risk = assess_risk({"class": cls, "confidence": conf})
        class_counts[cls] = class_counts.get(cls, 0) + 1
        enriched.append(
            {
                **d,
                "risk_level": risk["level"],
                "risk_label": risk["label"],
                "risk_reason": risk["reason"],
                "ai_score": min(99, round(conf * 100 * (1.05 if cls == "person" else 1.0))),
            }
        )

    persons = class_counts.get("person", 0)
    critical = sum(1 for e in enriched if e["risk_level"] == "critical")
    summary_bits = ", ".join(f"{n} {c}" for c, n in class_counts.items()) or "none"
    priority = "HIGH — person detected" if persons else ("elevated" if critical else "normal")

    return {
        "success": True,
        "python_touch": True,
        "engine": "risk_rules.py",
        "alert": persons > 0 or critical > 0,
        "priority": priority,
        "summary": f"Python enrich: {len(enriched)} object(s) ({summary_bits})",
        "count": payload.count if payload.count is not None else len(enriched),
        "latency_ms": payload.latency_ms,
        "fps": payload.fps,
        "class_counts": class_counts,
        "critical_count": critical,
        "detections": enriched,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    """
    Live stream for SOC dashboard.
    - Default: re-infers mounted sample with light augmentation every interval.
    - Client may send binary image frames; server replies with prediction JSON.
    Query: interval_ms (default 2000)
    """
    await websocket.accept()
    interval = 2.0
    try:
        if websocket.query_params.get("interval_ms"):
            interval = max(0.5, min(10.0, float(websocket.query_params["interval_ms"]) / 1000.0))
    except ValueError:
        pass

    sample_path = _sample_image_path()
    tick = 0
    try:
        await websocket.send_json({"type": "hello", "sample_ready": bool(sample_path), "interval_s": interval})
        while True:
            # Prefer client-provided frame if available (non-blocking poll)
            try:
                msg = await asyncio.wait_for(websocket.receive(), timeout=interval)
            except asyncio.TimeoutError:
                msg = None

            payload: dict[str, Any]
            if msg and msg.get("type") == "websocket.receive" and msg.get("bytes"):
                payload = run_predict_bytes(msg["bytes"])
                payload["source"] = "client_frame"
            elif sample_path:
                img = Image.open(sample_path).convert("RGB")
                # Light augmentation so stream feels alive
                tick += 1
                brightness = 0.92 + 0.08 * abs((tick % 10) - 5) / 5
                img = ImageEnhance.Brightness(img).enhance(brightness)
                # Tiny crop jitter
                w, h = img.size
                j = (tick % 7) - 3
                img = img.crop((max(0, j), max(0, j), w - max(0, -j), h - max(0, -j))).resize((w, h))
                payload = run_predict_array(np.array(img))
                payload["source"] = "sample_stream"
                payload["tick"] = tick
            else:
                payload = {
                    "type": "error",
                    "degraded": True,
                    "message": "No sample image and no client frame",
                    "detections": [],
                    "count": 0,
                }

            payload["type"] = "detection"
            payload["ts"] = time.time()
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        try:
            await websocket.send_json({"type": "error", "degraded": True, "message": str(exc)})
        except Exception:  # noqa: BLE001
            pass

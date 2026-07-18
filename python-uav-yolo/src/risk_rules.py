"""Risk / escalate rules shared by unit tests (mirrors SOC dashboard logic)."""

from __future__ import annotations


def assess_risk(det: dict) -> dict:
    cls = det.get("class", "")
    conf = float(det.get("confidence", 0))
    if cls == "person" and conf >= 0.8:
        return {"level": "critical", "label": "Critical", "reason": "Human · high certainty"}
    if cls == "person" and conf < 0.45:
        return {"level": "elevated", "label": "Elevated", "reason": "Uncertain human"}
    if cls == "person":
        return {"level": "elevated", "label": "Elevated", "reason": "Human in FOV"}
    if cls == "truck":
        return {"level": "moderate", "label": "Moderate", "reason": "Heavy vehicle"}
    if cls == "bus":
        return {"level": "moderate", "label": "Moderate", "reason": "Large vehicle"}
    return {"level": "low", "label": "Low", "reason": "Routine"}


def should_escalate_critical(detections: list[dict]) -> bool:
    return any(d.get("class") == "person" and float(d.get("confidence", 0)) >= 0.8 for d in detections)


def is_anomaly_cluster(detections: list[dict]) -> bool:
    low = any(d.get("class") == "person" and float(d.get("confidence", 0)) < 0.4 for d in detections)
    many = sum(1 for d in detections if d.get("class") == "person") >= 3
    return low and many


def threat_spike(prev_count: int, new_count: int, threshold: int = 2) -> bool:
    return new_count >= prev_count + threshold


def loitering(dwell_s: float, limit_s: float = 12.0) -> bool:
    return dwell_s >= limit_s


def geofence_vehicle_hit(detections: list[dict], fence_active: bool) -> bool:
    if not fence_active:
        return False
    return any(d.get("class") in {"truck", "bus"} for d in detections)

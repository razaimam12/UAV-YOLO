import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from risk_rules import (  # noqa: E402
    assess_risk,
    geofence_vehicle_hit,
    is_anomaly_cluster,
    loitering,
    should_escalate_critical,
    threat_spike,
)


def test_critical_person():
    r = assess_risk({"class": "person", "confidence": 0.86})
    assert r["level"] == "critical"


def test_low_conf_person():
    r = assess_risk({"class": "person", "confidence": 0.33})
    assert r["level"] == "elevated"


def test_truck_moderate():
    r = assess_risk({"class": "truck", "confidence": 0.79})
    assert r["level"] == "moderate"


def test_escalate():
    assert should_escalate_critical([{"class": "person", "confidence": 0.9}])
    assert not should_escalate_critical([{"class": "bus", "confidence": 0.9}])


def test_anomaly_cluster():
    dets = [
        {"class": "person", "confidence": 0.86},
        {"class": "person", "confidence": 0.83},
        {"class": "person", "confidence": 0.33},
    ]
    assert is_anomaly_cluster(dets)


def test_threat_spike():
    assert threat_spike(3, 6)
    assert not threat_spike(5, 6)


def test_loitering():
    assert loitering(12)
    assert not loitering(5)


def test_geofence():
    assert geofence_vehicle_hit([{"class": "truck", "confidence": 0.8}], True)
    assert not geofence_vehicle_hit([{"class": "truck", "confidence": 0.8}], False)

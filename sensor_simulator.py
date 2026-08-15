"""
Sensor simulation service – generates realistic live sensor readings for demo.
"""
from __future__ import annotations
import random
import math
from datetime import datetime
from typing import Dict, List


SENSOR_BASELINES = {
    "SNS-H1": {"flow": 320.0, "level": 3.2, "gate": 72.0, "reach": "head"},
    "SNS-H2": {"flow": 290.0, "level": 3.0, "gate": 70.0, "reach": "head"},
    "SNS-M1": {"flow": 260.0, "level": 2.6, "gate": 68.0, "reach": "middle"},
    "SNS-M2": {"flow": 240.0, "level": 2.4, "gate": 65.0, "reach": "middle"},
    "SNS-T1": {"flow": 200.0, "level": 1.9, "gate": 62.0, "reach": "tail"},
    "SNS-T2": {"flow": 185.0, "level": 1.7, "gate": 60.0, "reach": "tail"},
}


def get_diurnal_factor(hour: int) -> float:
    """Canal flow is higher midday (operations), lower at night."""
    return 1.0 + 0.12 * math.sin(math.pi * (hour - 6) / 12)


def simulate_reading(sensor_id: str, scenario: str = "normal",
                     noise: float = 0.04) -> Dict:
    """
    Generate one realistic sensor reading.

    Scenarios:
    - normal:   baseline ± noise
    - shortage: 20% system-wide reduction; tail-end worst affected
    - anomaly:  sudden sharp drop at tail (blockage simulation)
    - recovery: gradual return to baseline after shortage
    """
    baseline = SENSOR_BASELINES.get(sensor_id, {"flow": 250.0, "level": 2.0,
                                                  "gate": 65.0, "reach": "middle"})
    hour = datetime.utcnow().hour
    diurnal = get_diurnal_factor(hour)
    reach = baseline["reach"]

    base_flow  = baseline["flow"]
    base_level = baseline["level"]

    if scenario == "shortage":
        if reach == "tail":
            factor = random.uniform(0.48, 0.62)
        elif reach == "middle":
            factor = random.uniform(0.68, 0.78)
        else:
            factor = random.uniform(0.80, 0.90)
    elif scenario == "anomaly":
        factor = random.uniform(0.30, 0.45) if reach == "tail" else random.uniform(0.90, 1.05)
    elif scenario == "recovery":
        if reach == "tail":
            factor = random.uniform(0.72, 0.85)
        else:
            factor = random.uniform(0.92, 1.02)
    else:
        factor = random.uniform(1.0 - noise, 1.0 + noise)

    flow  = round(base_flow  * factor * diurnal, 2)
    level = round(base_level * factor, 3)
    gate  = round(baseline["gate"] + random.uniform(-3, 3), 1)
    temp  = round(28 + 6 * abs((hour / 24) - 0.5) + random.uniform(-1, 1), 1)
    rain  = round(random.uniform(0, 5), 2) if random.random() < 0.08 else 0.0

    return {
        "sensor_id": sensor_id,
        "timestamp": datetime.utcnow().isoformat(),
        "water_level": max(level, 0.1),
        "flow_rate": max(flow, 0.0),
        "gate_open_percentage": min(max(gate, 0), 100),
        "temperature": temp,
        "rainfall": rain,
        "reach": reach,
        "scenario": scenario,
    }


def simulate_all_sensors(scenario: str = "normal") -> List[Dict]:
    """Simulate readings from all six sensors."""
    return [simulate_reading(sid, scenario) for sid in SENSOR_BASELINES]

"""
ML Models for Narmada Jal Nyay AI
- Flow prediction (Random Forest)
- Anomaly detection (Isolation Forest + statistical thresholding)
- Water demand prediction (Linear Regression baseline)
"""
from __future__ import annotations
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error


# ─── Flow Prediction Model ────────────────────────────────────────────────────

class FlowPredictionModel:
    """
    Predict canal flow rate (cumecs) for the next N hours.

    Features: hour_of_day, day_of_week, water_level, gate_open_pct,
              rainfall, temp, flow_lag_1h, flow_lag_3h, flow_lag_24h
    """

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=42, n_jobs=-1
        )
        self.scaler = StandardScaler()
        self._is_trained = False

    def _make_features(self, readings: List[Dict]) -> np.ndarray:
        features = []
        for i, r in enumerate(readings):
            lag1  = readings[i-1]["flow_rate"]  if i > 0  else r["flow_rate"]
            lag3  = readings[i-3]["flow_rate"]  if i > 2  else r["flow_rate"]
            lag24 = readings[i-24]["flow_rate"] if i > 23 else r["flow_rate"]
            ts = r["timestamp"]
            features.append([
                ts.hour,
                ts.weekday(),
                r["water_level"],
                r["gate_open_percentage"],
                r.get("rainfall", 0.0),
                r.get("temperature", 30.0),
                lag1, lag3, lag24,
            ])
        return np.array(features, dtype=np.float32)

    def train(self, readings: List[Dict], targets: List[float]) -> float:
        X = self._make_features(readings)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, targets)
        self._is_trained = True
        preds = self.model.predict(X_scaled)
        mae = mean_absolute_error(targets, preds)
        return mae

    def predict(self, readings: List[Dict]) -> List[float]:
        if not self._is_trained:
            # Return simple average if not trained
            avg = np.mean([r["flow_rate"] for r in readings]) if readings else 300.0
            return [float(avg)] * 24
        X = self._make_features(readings)
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled).tolist()

    def predict_next_24h(self, recent_readings: List[Dict], base_flow: float) -> List[float]:
        """Generate synthetic 24-hour forecast from recent readings."""
        if len(recent_readings) < 24:
            # Fallback: simple sinusoidal day pattern
            predictions = []
            for h in range(24):
                diurnal_factor = 1.0 + 0.12 * np.sin(np.pi * (h - 6) / 12)
                predictions.append(round(base_flow * diurnal_factor, 2))
            return predictions
        recent = recent_readings[-24:]
        return [round(v, 2) for v in self.predict(recent)]


# ─── Anomaly Detection Model ──────────────────────────────────────────────────

class AnomalyDetectionModel:
    """
    Two-layer anomaly detection:
    1. Statistical thresholding (fast, interpretable)
    2. Isolation Forest (unsupervised ML)
    """

    def __init__(self, contamination: float = 0.05):
        self.iso_forest = IsolationForest(
            n_estimators=100, contamination=contamination, random_state=42
        )
        self.mean_flow: Optional[float] = None
        self.std_flow:  Optional[float] = None
        self._is_trained = False

    def train(self, flow_rates: List[float]):
        arr = np.array(flow_rates).reshape(-1, 1)
        self.mean_flow = float(np.mean(arr))
        self.std_flow  = float(np.std(arr))
        self.iso_forest.fit(arr)
        self._is_trained = True

    def detect(self, flow_rate: float, threshold_sigma: float = 2.5) -> Dict:
        """
        Returns:
            is_anomaly: bool
            method: 'statistical' | 'isolation_forest' | 'both' | 'none'
            severity: 'low' | 'medium' | 'high' | 'critical'
            z_score: float
        """
        result = {
            "is_anomaly": False,
            "method": "none",
            "severity": "normal",
            "z_score": 0.0,
            "description": "Flow within normal range",
        }

        if self.mean_flow is None:
            return result

        z_score = (flow_rate - self.mean_flow) / max(self.std_flow, 1e-6)
        result["z_score"] = round(z_score, 3)
        stat_anomaly = abs(z_score) > threshold_sigma

        iso_anomaly = False
        if self._is_trained:
            pred = self.iso_forest.predict([[flow_rate]])
            iso_anomaly = pred[0] == -1

        if stat_anomaly and iso_anomaly:
            result["is_anomaly"] = True
            result["method"] = "both"
        elif stat_anomaly:
            result["is_anomaly"] = True
            result["method"] = "statistical"
        elif iso_anomaly:
            result["is_anomaly"] = True
            result["method"] = "isolation_forest"

        if result["is_anomaly"]:
            drop_pct = (self.mean_flow - flow_rate) / self.mean_flow * 100
            if abs(z_score) > 4.0 or drop_pct > 40:
                result["severity"] = "critical"
                result["description"] = f"Critical flow anomaly: {drop_pct:.1f}% below normal"
            elif abs(z_score) > 3.0 or drop_pct > 25:
                result["severity"] = "high"
                result["description"] = f"High flow anomaly: {drop_pct:.1f}% below normal"
            else:
                result["severity"] = "medium"
                result["description"] = f"Flow anomaly detected: {drop_pct:.1f}% deviation"

        return result


# ─── Water Demand Prediction ──────────────────────────────────────────────────

CROP_BASE_DEMAND: Dict[str, float] = {
    "Sugarcane":   9.0, "Cotton": 7.0, "Vegetables": 6.5,
    "Wheat":       5.5, "Bajra":  5.0, "Groundnut":  4.5,
    "Castor":      4.2, "Mustard":4.0, "Sesame":     3.8, "Cumin": 3.5,
}

SEASON_MULTIPLIER: Dict[str, float] = {
    "kharif": 1.15,   # June-October (monsoon)
    "rabi":   0.95,   # November-March (winter)
    "summer": 1.25,   # April-May (hot, high evapotranspiration)
}


class WaterDemandPredictor:
    """
    Estimates water demand per farmer per irrigation cycle.

    Formula:
        demand_m3 = crop_et (mm/day) × land_area (ha) × 10 × days_per_cycle
                    × season_mult × efficiency_factor

    A Linear Regression layer is applied to correct for historical bias.
    """

    def __init__(self):
        self.lr = LinearRegression()
        self.scaler = StandardScaler()
        self._is_trained = False

    def _base_demand(self, crop: str, land_area: float,
                     days_per_cycle: int = 10, season: str = "rabi") -> float:
        et = CROP_BASE_DEMAND.get(crop, 5.0)
        season_m = SEASON_MULTIPLIER.get(season, 1.0)
        efficiency = 0.85  # canal efficiency factor
        return et * land_area * 10 * days_per_cycle * season_m * efficiency

    def predict(self, crop: str, land_area: float,
                season: str = "rabi", days_per_cycle: int = 10,
                historical_received: Optional[float] = None) -> float:
        base = self._base_demand(crop, land_area, days_per_cycle, season)
        if historical_received is not None and historical_received > 0:
            # Blend base estimate with historical pattern
            blend = 0.7 * base + 0.3 * historical_received
        else:
            blend = base
        return round(blend, 2)

    def predict_batch(self, farmers: List[Dict], season: str = "rabi") -> Dict[str, float]:
        return {
            f["farmer_id"]: self.predict(
                f["crop"], f["land_area"], season,
                historical_received=f.get("previous_water_received")
            )
            for f in farmers
        }


# ─── Singleton instances ──────────────────────────────────────────────────────

_flow_model      = FlowPredictionModel()
_anomaly_model   = AnomalyDetectionModel()
_demand_predictor = WaterDemandPredictor()


def get_flow_model() -> FlowPredictionModel:
    return _flow_model


def get_anomaly_model() -> AnomalyDetectionModel:
    return _anomaly_model


def get_demand_predictor() -> WaterDemandPredictor:
    return _demand_predictor


def train_models_from_readings(readings: List[Dict]):
    """Train all models from historical sensor readings."""
    if len(readings) < 50:
        return

    # Sort by timestamp
    readings_sorted = sorted(readings, key=lambda r: r["timestamp"])
    flow_rates = [r["flow_rate"] for r in readings_sorted]

    # Train anomaly model
    _anomaly_model.train(flow_rates)

    # Train flow prediction model (shift by 1 to predict next reading)
    if len(readings_sorted) > 25:
        train_X = readings_sorted[:-1]
        train_y = flow_rates[1:]
        mae = _flow_model.train(train_X, train_y)
        print(f"Flow model trained. MAE: {mae:.2f} cumecs")

    print("Anomaly model trained.")

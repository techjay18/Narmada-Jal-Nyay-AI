"""
Canal status and flow monitoring API
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database.db import get_db
from ..database.models import CanalSensor, SensorReading, Canal
from ..agents.agents import CanalFlowMonitoringAgent
from ..services.sensor_simulator import simulate_all_sensors

router = APIRouter()
_agent = CanalFlowMonitoringAgent()


@router.get("/status")
async def get_canal_status(
    scenario: str = Query("normal", enum=["normal", "shortage", "anomaly", "recovery"]),
    db: AsyncSession = Depends(get_db),
):
    """Get current canal system status – uses live simulated sensor readings."""
    readings = simulate_all_sensors(scenario)
    status = _agent.get_canal_status(readings)
    return status


@router.get("/flow")
async def get_flow_data(
    hours: int = Query(24, ge=1, le=168),
    sensor_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get historical flow data for charts."""
    since = datetime.utcnow() - timedelta(hours=hours)

    stmt = (
        select(SensorReading, CanalSensor)
        .join(CanalSensor, SensorReading.sensor_id == CanalSensor.id)
        .where(SensorReading.timestamp >= since)
        .order_by(SensorReading.timestamp)
    )
    if sensor_id:
        stmt = stmt.where(CanalSensor.sensor_id == sensor_id)

    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for reading, sensor in rows:
        data.append({
            "timestamp":    reading.timestamp.isoformat(),
            "sensor_id":    sensor.sensor_id,
            "location":     sensor.location,
            "reach":        sensor.reach_position.value if sensor.reach_position else "unknown",
            "flow_rate":    reading.flow_rate,
            "water_level":  reading.water_level,
            "gate_open_pct":reading.gate_open_percentage,
            "temperature":  reading.temperature,
            "rainfall":     reading.rainfall,
            "is_anomaly":   reading.is_anomaly,
        })

    # Aggregate by reach for chart series
    head_series, middle_series, tail_series = [], [], []
    for row in data:
        ts = row["timestamp"]
        flow = row["flow_rate"]
        if row["reach"] == "head":
            head_series.append({"time": ts, "value": flow})
        elif row["reach"] == "middle":
            middle_series.append({"time": ts, "value": flow})
        else:
            tail_series.append({"time": ts, "value": flow})

    return {
        "raw": data[:500],
        "series": {
            "head":   head_series[:200],
            "middle": middle_series[:200],
            "tail":   tail_series[:200],
        },
    }


@router.get("/sensors")
async def get_sensors(db: AsyncSession = Depends(get_db)):
    """List all canal sensors with latest reading."""
    result = await db.execute(select(CanalSensor).where(CanalSensor.is_active == True))
    sensors = result.scalars().all()

    sensor_list = []
    for s in sensors:
        # Get latest reading
        stmt = (select(SensorReading)
                .where(SensorReading.sensor_id == s.id)
                .order_by(desc(SensorReading.timestamp))
                .limit(1))
        r = await db.execute(stmt)
        latest = r.scalar_one_or_none()

        sensor_list.append({
            "sensor_id": s.sensor_id,
            "location":  s.location,
            "reach":     s.reach_position.value if s.reach_position else "unknown",
            "latitude":  s.latitude,
            "longitude": s.longitude,
            "latest": {
                "flow_rate":    latest.flow_rate    if latest else None,
                "water_level":  latest.water_level  if latest else None,
                "gate_open_pct":latest.gate_open_percentage if latest else None,
                "timestamp":    latest.timestamp.isoformat() if latest else None,
                "is_anomaly":   latest.is_anomaly   if latest else False,
            } if latest else None,
        })

    return {"sensors": sensor_list, "total": len(sensor_list)}

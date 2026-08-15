"""
Main dashboard API – aggregates data from all agents
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ..database.db import get_db
from ..database.models import (
    Farmer, WaterAllocation, IrrigationSchedule, Complaint,
    Alert, AIRecommendation, SensorReading, CanalSensor
)
from ..agents.agents import AgentOrchestrator
from ..services.sensor_simulator import simulate_all_sensors

router = APIRouter()
_orchestrator = AgentOrchestrator()


@router.get("")
async def get_dashboard(
    scenario: str = Query("normal", enum=["normal", "shortage", "anomaly", "recovery"]),
    db: AsyncSession = Depends(get_db),
):
    """
    Full dashboard – triggers complete agent orchestration cycle.
    Returns canal status, equity metrics, AI insights, alerts, disputes.
    """
    # Load live sensor readings
    sensor_readings = simulate_all_sensors(scenario)

    # Load farmers
    farmers_result = await db.execute(select(Farmer).where(Farmer.is_active == True))
    farmers = farmers_result.scalars().all()
    farmers_data = [
        {
            "farmer_id": f.farmer_id,
            "reach_type": f.reach_type.value,
            "land_area": f.land_area,
            "crop": f.crop,
            "crop_water_requirement": f.crop_water_requirement,
            "previous_water_received": f.previous_water_received,
            "expected_water": f.expected_water,
        }
        for f in farmers
    ]

    # Load complaints
    complaints_result = await db.execute(
        select(Complaint, Farmer)
        .join(Farmer, Complaint.farmer_id == Farmer.id)
        .order_by(desc(Complaint.timestamp))
        .limit(50)
    )
    complaints = []
    for complaint, farmer in complaints_result.all():
        complaints.append({
            "complaint_id": complaint.complaint_id,
            "village":      farmer.village,
            "reach_type":   farmer.reach_type.value,
            "severity":     complaint.severity.value,
            "status":       complaint.status.value,
            "category":     complaint.category,
        })

    # Load alerts
    alerts_result = await db.execute(
        select(Alert).order_by(desc(Alert.created_at)).limit(20)
    )
    alerts = []
    for alert in alerts_result.scalars().all():
        alerts.append({
            "id":             alert.id,
            "alert_type":     alert.alert_type,
            "severity":       alert.severity.value,
            "message":        alert.message,
            "is_acknowledged":alert.is_acknowledged,
            "created_at":     alert.created_at.isoformat(),
        })

    # Load AI recommendations
    recs_result = await db.execute(
        select(AIRecommendation)
        .order_by(desc(AIRecommendation.created_at))
        .limit(10)
    )
    recommendations = []
    for rec in recs_result.scalars().all():
        recommendations.append({
            "id":              rec.id,
            "type":            rec.recommendation_type,
            "context":         rec.context,
            "recommendation":  rec.recommendation,
            "confidence":      rec.confidence,
            "requires_approval": rec.requires_approval,
            "approved":        rec.approved,
        })

    # Estimate total available water (from sensor reading)
    avg_head_flow = 320.0 if scenario != "shortage" else 256.0
    total_water = avg_head_flow * 86400 * 0.30

    # Run orchestration cycle
    result = await _orchestrator.run_full_cycle(
        sensor_readings=sensor_readings,
        farmers_data=farmers_data,
        total_water=total_water,
        complaints=complaints,
        alerts_db=alerts,
        recommendations_db=recommendations,
        scenario=scenario,
    )

    return {
        "scenario": scenario,
        **result,
    }


@router.post("/agent/analyze")
async def agent_analyze(
    question: str,
    scenario: str = "normal",
    db: AsyncSession = Depends(get_db),
):
    """AI assistant endpoint – powered by IBM Granite."""
    # Build context
    sensor_readings = simulate_all_sensors(scenario)
    canal_status = _orchestrator.flow_agent.get_canal_status(sensor_readings)

    context = {
        "canal_status":       canal_status.get("overall_status", "unknown"),
        "head_flow_cumecs":   canal_status.get("avg_head_flow", 0),
        "tail_flow_cumecs":   canal_status.get("avg_tail_flow", 0),
        "head_tail_ratio":    canal_status.get("head_tail_ratio", 0),
        "active_scenario":    scenario,
        "system":             "Narmada Jal Nyay AI – Gujarat Canal Water Distribution",
    }

    answer = await _orchestrator.handle_chat_query(question, context)
    return {"question": question, "answer": answer, "context": context}

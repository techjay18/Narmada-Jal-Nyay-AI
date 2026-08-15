"""
Water distribution schedule API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database.db import get_db
from ..database.models import Farmer, WaterAllocation, IrrigationSchedule, ReachType
from ..agents.agents import EquitableDistributionAgent, CanalFlowMonitoringAgent
from ..services.sensor_simulator import simulate_all_sensors

router = APIRouter()
_dist_agent = EquitableDistributionAgent()
_flow_agent = CanalFlowMonitoringAgent()


class GenerateScheduleRequest(BaseModel):
    total_available_water: Optional[float] = None  # cubic metres; auto-detect if None
    shortage_override: Optional[float] = None       # 0-1 fraction
    scenario: str = "normal"


@router.get("")
async def get_current_schedule(db: AsyncSession = Depends(get_db)):
    """Get the most recent irrigation schedule from DB."""
    stmt = (select(IrrigationSchedule)
            .where(IrrigationSchedule.is_active == True)
            .order_by(desc(IrrigationSchedule.schedule_date))
            .limit(1))
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "No active schedule found")

    # Get allocations for this schedule
    alloc_stmt = (
        select(WaterAllocation, Farmer)
        .join(Farmer, WaterAllocation.farmer_id == Farmer.id)
        .where(WaterAllocation.schedule_id == schedule.id)
        .order_by(Farmer.reach_type)
    )
    alloc_result = await db.execute(alloc_stmt)
    rows = alloc_result.all()

    allocations = []
    for alloc, farmer in rows:
        allocations.append({
            "farmer_id":         farmer.farmer_id,
            "farmer_name":       farmer.farmer_name,
            "village":           farmer.village,
            "reach_type":        farmer.reach_type.value,
            "crop":              farmer.crop,
            "expected_water":    farmer.expected_water,
            "allocated_water":   alloc.allocated_water,
            "actual_received":   alloc.actual_water_received,
            "fairness_score":    alloc.fairness_score,
            "slot_start":        alloc.irrigation_slot_start.isoformat() if alloc.irrigation_slot_start else None,
            "slot_end":          alloc.irrigation_slot_end.isoformat()   if alloc.irrigation_slot_end   else None,
        })

    fairness_report = _dist_agent.calculate_fairness_report(allocations)

    return {
        "schedule_id":          schedule.id,
        "schedule_date":        schedule.schedule_date.isoformat(),
        "total_available_water":schedule.total_available_water,
        "shortage_level":       schedule.shortage_level,
        "head_equity_score":    schedule.head_equity_score,
        "tail_equity_score":    schedule.tail_equity_score,
        "overall_fairness":     schedule.overall_fairness,
        "ai_summary":           schedule.ai_summary,
        "allocations":          allocations,
        "fairness_report":      fairness_report,
    }


@router.post("/generate")
async def generate_schedule(
    req: GenerateScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new optimised irrigation schedule using the equity algorithm.
    Human approval required if shortage > 25% or head-tail gap > 20%.
    """
    # Load all active farmers
    result = await db.execute(select(Farmer).where(Farmer.is_active == True))
    farmers = result.scalars().all()

    if not farmers:
        raise HTTPException(400, "No farmers found in database")

    farmers_data = [
        {
            "farmer_id":               f.farmer_id,
            "reach_type":              f.reach_type.value,
            "land_area":               f.land_area,
            "crop":                    f.crop,
            "crop_water_requirement":  f.crop_water_requirement,
            "previous_water_received": f.previous_water_received,
            "expected_water":          f.expected_water,
        }
        for f in farmers
    ]

    # Determine total available water
    total_water = req.total_available_water
    if total_water is None:
        # Auto-calculate from sensor data
        readings = simulate_all_sensors(req.scenario)
        canal_status = _flow_agent.get_canal_status(readings)
        head_flow = canal_status.get("avg_head_flow", 300.0)
        # Approximate daily volume = flow_rate × 86400 seconds × number of head farmers served
        total_water = head_flow * 86400 * 0.30  # rough estimate
        if req.scenario == "shortage":
            total_water *= 0.80

    schedule = _dist_agent.generate_schedule(
        farmers_data=farmers_data,
        total_available_water=total_water,
        shortage_override=req.shortage_override,
    )
    return schedule

"""
Farmer management and water status API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database.db import get_db
from ..database.models import Farmer, WaterAllocation, IrrigationSchedule, ReachType
from ..agents.agents import FarmerAlertAgent
from ..services.sensor_simulator import simulate_all_sensors
from ..agents.agents import CanalFlowMonitoringAgent

router = APIRouter()
_alert_agent = FarmerAlertAgent()
_flow_agent  = CanalFlowMonitoringAgent()


@router.get("")
async def list_farmers(
    reach_type: Optional[str] = Query(None, enum=["head", "middle", "tail"]),
    village: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Farmer).where(Farmer.is_active == True)
    if reach_type:
        stmt = stmt.where(Farmer.reach_type == ReachType(reach_type))
    if village:
        stmt = stmt.where(Farmer.village.ilike(f"%{village}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    farmers = result.scalars().all()

    return {
        "farmers": [_farmer_dict(f) for f in farmers],
        "total": len(farmers),
    }


@router.get("/{farmer_id}")
async def get_farmer(farmer_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    )
    farmer = result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(404, f"Farmer {farmer_id} not found")
    return _farmer_dict(farmer)


@router.get("/{farmer_id}/water-status")
async def get_farmer_water_status(
    farmer_id: str,
    scenario: str = Query("normal"),
    db: AsyncSession = Depends(get_db),
):
    """Get complete water status for a specific farmer."""
    result = await db.execute(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    )
    farmer = result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(404, f"Farmer {farmer_id} not found")

    # Get latest allocation
    stmt = (
        select(WaterAllocation)
        .where(WaterAllocation.farmer_id == farmer.id)
        .order_by(desc(WaterAllocation.date))
        .limit(1)
    )
    alloc_result = await db.execute(stmt)
    alloc = alloc_result.scalar_one_or_none()

    allocation_dict = {}
    if alloc:
        allocation_dict = {
            "allocated_water": alloc.allocated_water,
            "actual_water_received": alloc.actual_water_received,
            "expected_water": farmer.expected_water,
            "fairness_score": alloc.fairness_score,
            "irrigation_slot_start": alloc.irrigation_slot_start.isoformat() if alloc.irrigation_slot_start else None,
            "irrigation_slot_end":   alloc.irrigation_slot_end.isoformat()   if alloc.irrigation_slot_end   else None,
            "slot": {
                "start": alloc.irrigation_slot_start.isoformat() if alloc.irrigation_slot_start else None,
                "end":   alloc.irrigation_slot_end.isoformat()   if alloc.irrigation_slot_end   else None,
            }
        }

    # Canal status
    readings = simulate_all_sensors(scenario)
    canal_status = _flow_agent.get_canal_status(readings)

    status = _alert_agent.get_farmer_water_status(
        farmer=_farmer_dict(farmer),
        allocation=allocation_dict,
        canal_status=canal_status,
    )
    return status


def _farmer_dict(f: Farmer) -> dict:
    return {
        "id":                      f.id,
        "farmer_id":               f.farmer_id,
        "farmer_name":             f.farmer_name,
        "village":                 f.village,
        "canal_section":           f.canal_section,
        "reach_type":              f.reach_type.value,
        "land_area":               f.land_area,
        "crop":                    f.crop,
        "crop_water_requirement":  f.crop_water_requirement,
        "previous_water_received": f.previous_water_received,
        "expected_water":          f.expected_water,
        "contact_number":          f.contact_number,
        "language_preference":     f.language_preference,
    }

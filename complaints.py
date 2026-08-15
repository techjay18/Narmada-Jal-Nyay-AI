"""
Complaints and dispute management API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
import uuid
from datetime import datetime

from ..database.db import get_db
from ..database.models import Complaint, Farmer, WaterAllocation, SeverityLevel, ComplaintStatus
from ..agents.agents import DisputeDetectionAgent

router = APIRouter()
_dispute_agent = DisputeDetectionAgent()


class SubmitComplaintRequest(BaseModel):
    farmer_id: str
    complaint_text: str
    category: Optional[str] = "general"


class ResolveComplaintRequest(BaseModel):
    resolution_notes: str
    resolved_by: str


@router.get("")
async def list_complaints(
    status: Optional[str] = Query(None, enum=["open", "under_review", "resolved", "escalated"]),
    severity: Optional[str] = Query(None, enum=["normal", "low", "medium", "high", "critical"]),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Complaint, Farmer)
        .join(Farmer, Complaint.farmer_id == Farmer.id)
        .order_by(desc(Complaint.timestamp))
    )
    if status:
        stmt = stmt.where(Complaint.status == ComplaintStatus(status))
    if severity:
        stmt = stmt.where(Complaint.severity == SeverityLevel(severity))
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    complaints_list = []
    for complaint, farmer in rows:
        complaints_list.append({
            "complaint_id":      complaint.complaint_id,
            "farmer_id":         farmer.farmer_id,
            "farmer_name":       farmer.farmer_name,
            "village":           farmer.village,
            "reach_type":        farmer.reach_type.value,
            "complaint_text":    complaint.complaint_text,
            "timestamp":         complaint.timestamp.isoformat(),
            "category":          complaint.category,
            "severity":          complaint.severity.value,
            "status":            complaint.status.value,
            "ai_summary":        complaint.ai_summary,
            "ai_recommendation": complaint.ai_recommendation,
            "resolved_by":       complaint.resolved_by,
            "resolved_at":       complaint.resolved_at.isoformat() if complaint.resolved_at else None,
        })

    # Detect systemic issues
    systemic = _dispute_agent.detect_systemic_issues([
        {"reach_type": c["reach_type"], "status": c["status"], "village": c["village"]}
        for c in complaints_list
    ])

    return {
        "complaints": complaints_list,
        "total": len(complaints_list),
        "systemic_issues": systemic,
    }


@router.post("")
async def submit_complaint(req: SubmitComplaintRequest, db: AsyncSession = Depends(get_db)):
    """Submit a new farmer complaint. AI analysis runs asynchronously."""
    result = await db.execute(
        select(Farmer).where(Farmer.farmer_id == req.farmer_id)
    )
    farmer = result.scalar_one_or_none()
    if not farmer:
        raise HTTPException(404, f"Farmer {req.farmer_id} not found")

    # Auto-classify severity
    auto_severity = _dispute_agent.classify_severity(req.complaint_text)
    sev_enum = SeverityLevel(auto_severity) if auto_severity in [e.value for e in SeverityLevel] \
        else SeverityLevel.MEDIUM

    complaint = Complaint(
        complaint_id="CMP-" + uuid.uuid4().hex[:8].upper(),
        farmer_id=farmer.id,
        complaint_text=req.complaint_text,
        category=req.category,
        severity=sev_enum,
        status=ComplaintStatus.OPEN,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    return {
        "complaint_id": complaint.complaint_id,
        "auto_severity": auto_severity,
        "status": "open",
        "message": "Complaint submitted. AI analysis in progress.",
    }


@router.post("/{complaint_id}/analyze")
async def analyze_complaint(complaint_id: str, db: AsyncSession = Depends(get_db)):
    """Run AI analysis on a specific complaint using IBM Granite."""
    result = await db.execute(
        select(Complaint, Farmer)
        .join(Farmer, Complaint.farmer_id == Farmer.id)
        .where(Complaint.complaint_id == complaint_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, f"Complaint {complaint_id} not found")
    complaint, farmer = row

    # Get allocation history
    alloc_result = await db.execute(
        select(WaterAllocation)
        .where(WaterAllocation.farmer_id == farmer.id)
        .order_by(desc(WaterAllocation.date))
        .limit(7)
    )
    allocations = alloc_result.scalars().all()
    alloc_history = [{"fairness_score": a.fairness_score} for a in allocations]

    farmer_dict = {
        "farmer_id":   farmer.farmer_id,
        "farmer_name": farmer.farmer_name,
        "village":     farmer.village,
        "reach_type":  farmer.reach_type.value,
    }
    complaint_dict = {
        "complaint_id":   complaint.complaint_id,
        "complaint_text": complaint.complaint_text,
    }

    analysis = await _dispute_agent.analyze_complaint(complaint_dict, farmer_dict, alloc_history)

    # Update complaint in DB
    sev_val = analysis.get("final_severity", complaint.severity.value)
    try:
        sev_enum = SeverityLevel(sev_val)
    except ValueError:
        sev_enum = complaint.severity

    complaint.ai_summary        = analysis.get("ai_summary", "")
    complaint.ai_recommendation = analysis.get("ai_recommendation", "")
    complaint.severity          = sev_enum
    complaint.status            = ComplaintStatus.UNDER_REVIEW
    await db.commit()

    return analysis


@router.post("/{complaint_id}/resolve")
async def resolve_complaint(
    complaint_id: str,
    req: ResolveComplaintRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a complaint (requires human authority action)."""
    result = await db.execute(
        select(Complaint).where(Complaint.complaint_id == complaint_id)
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(404, f"Complaint {complaint_id} not found")

    complaint.status       = ComplaintStatus.RESOLVED
    complaint.resolved_by  = req.resolved_by
    complaint.resolved_at  = datetime.utcnow()
    complaint.ai_recommendation = (complaint.ai_recommendation or "") + \
        f"\n\nResolved by: {req.resolved_by}. Notes: {req.resolution_notes}"
    await db.commit()

    return {"complaint_id": complaint_id, "status": "resolved",
            "resolved_by": req.resolved_by}

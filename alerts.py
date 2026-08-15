"""
Alerts API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from ..database.db import get_db
from ..database.models import Alert, SeverityLevel

router = APIRouter()


@router.get("")
async def get_alerts(
    severity: str = Query(None, enum=["normal", "low", "medium", "high", "critical"]),
    acknowledged: bool = Query(None),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).order_by(desc(Alert.created_at)).limit(limit)
    if severity:
        stmt = stmt.where(Alert.severity == SeverityLevel(severity))
    if acknowledged is not None:
        stmt = stmt.where(Alert.is_acknowledged == acknowledged)

    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return {
        "alerts": [
            {
                "id":             a.id,
                "alert_type":     a.alert_type,
                "severity":       a.severity.value,
                "message":        a.message,
                "details":        a.details,
                "is_acknowledged":a.is_acknowledged,
                "created_at":     a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "total": len(alerts),
        "unacknowledged": sum(1 for a in alerts if not a.is_acknowledged),
    }


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        alert.is_acknowledged = True
        await db.commit()
    return {"alert_id": alert_id, "acknowledged": True}

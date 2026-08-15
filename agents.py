"""
Five AI Agents for Narmada Jal Nyay AI

Agent 1: Canal Flow Monitoring Agent
Agent 2: Equitable Distribution Scheduling Agent
Agent 3: Farmer Water Availability Alert Agent
Agent 4: Dispute Detection & Mediation Agent
Agent 5: Irrigation Efficiency Dashboard Agent
"""
from __future__ import annotations
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from ..ml.models import get_anomaly_model, get_flow_model, get_demand_predictor
from ..ml.water_equity import (
    allocate_water, FarmerDemand, ReachType, ScheduleResult, SAMPLE_FARMERS
)
from ..services.granite_service import (
    explain_water_shortage, analyze_complaint,
    generate_dashboard_insight, recommend_dispute_resolution,
    explain_farmer_alert, answer_chat_query,
)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 1 – Canal Flow Monitoring Agent
# ═══════════════════════════════════════════════════════════════════════════════

class CanalFlowMonitoringAgent:
    """
    Objective: Continuously monitor canal flow, detect anomalies, leakages,
    gate problems, and predict shortages.

    Autonomous actions:
    - Generate alerts for anomalies
    - Trigger distribution recalculation on shortage detection
    - Update flow predictions

    Human approval required:
    - Gate adjustment recommendations > 20%
    - Emergency flow diversions
    """

    FLOW_ALERT_THRESHOLDS = {
        "critical_low":  0.50,  # < 50% of normal
        "high_low":      0.65,  # < 65% of normal
        "medium_low":    0.80,  # < 80% of normal
    }

    def __init__(self):
        self.anomaly_model = get_anomaly_model()
        self.flow_model    = get_flow_model()
        self.baseline_flows: Dict[str, float] = {
            "SNS-H1": 320.0, "SNS-H2": 290.0,
            "SNS-M1": 260.0, "SNS-M2": 240.0,
            "SNS-T1": 200.0, "SNS-T2": 185.0,
        }

    def process_sensor_reading(self, sensor_id: str, reading: Dict) -> Dict:
        """
        Process a single sensor reading. Returns analysis dict with:
        - status, anomaly_result, alerts, recommendations
        """
        flow_rate = reading["flow_rate"]
        water_level = reading["water_level"]
        gate_pct = reading["gate_open_percentage"]
        baseline = self.baseline_flows.get(sensor_id, 300.0)

        # Anomaly detection
        anomaly_result = self.anomaly_model.detect(flow_rate)

        # Flow ratio analysis
        flow_ratio = flow_rate / baseline
        status = "normal"
        alerts = []
        recommendations = []

        if flow_ratio < self.FLOW_ALERT_THRESHOLDS["critical_low"]:
            status = "critical"
            alerts.append({
                "type": "critical_low_flow",
                "severity": "critical",
                "message": f"CRITICAL: Flow at {sensor_id} is {(1-flow_ratio)*100:.1f}% below baseline",
                "requires_action": True,
            })
            recommendations.append(
                f"Immediate inspection of {sensor_id} required. "
                f"Check for blockage, leakage, or unauthorized abstraction."
            )
        elif flow_ratio < self.FLOW_ALERT_THRESHOLDS["high_low"]:
            status = "high_alert"
            alerts.append({
                "type": "low_flow",
                "severity": "high",
                "message": f"High alert: Flow at {sensor_id} dropped {(1-flow_ratio)*100:.1f}% below baseline",
                "requires_action": True,
            })
        elif flow_ratio < self.FLOW_ALERT_THRESHOLDS["medium_low"]:
            status = "warning"
            alerts.append({
                "type": "low_flow_warning",
                "severity": "medium",
                "message": f"Warning: Reduced flow at {sensor_id} ({flow_rate:.1f} cumecs)",
                "requires_action": False,
            })

        # Gate anomaly check
        if gate_pct > 92:
            alerts.append({
                "type": "gate_over_open",
                "severity": "medium",
                "message": f"Gate at {sensor_id} open at {gate_pct}% – possible unauthorized opening",
                "requires_action": True,
            })

        # Low water level check
        if water_level < 0.8:
            alerts.append({
                "type": "low_water_level",
                "severity": "high" if water_level < 0.5 else "medium",
                "message": f"Low water level at {sensor_id}: {water_level:.2f}m",
                "requires_action": water_level < 0.5,
            })

        ts = reading.get("timestamp", datetime.utcnow())
        ts_str = ts if isinstance(ts, str) else ts.isoformat()
        return {
            "sensor_id": sensor_id,
            "timestamp": ts_str,
            "flow_rate": flow_rate,
            "water_level": water_level,
            "gate_open_pct": gate_pct,
            "flow_ratio": round(flow_ratio, 3),
            "status": status,
            "anomaly": anomaly_result,
            "alerts": alerts,
            "recommendations": recommendations,
            "shortage_detected": flow_ratio < 0.82,
            "shortage_estimate": round(1 - flow_ratio, 3) if flow_ratio < 1 else 0.0,
        }

    def get_canal_status(self, all_readings: List[Dict]) -> Dict:
        """Aggregate status from all sensors."""
        if not all_readings:
            return {"status": "no_data", "sensors": []}

        analyses = [self.process_sensor_reading(r["sensor_id"], r) for r in all_readings]
        severities = [a["status"] for a in analyses]

        if "critical" in severities:
            overall = "critical"
        elif "high_alert" in severities:
            overall = "high_alert"
        elif "warning" in severities:
            overall = "warning"
        else:
            overall = "normal"

        avg_head_flow = sum(
            a["flow_rate"] for a in analyses
            if a["sensor_id"] in ["SNS-H1", "SNS-H2"]
        ) / max(1, sum(1 for a in analyses if a["sensor_id"] in ["SNS-H1", "SNS-H2"]))

        avg_tail_flow = sum(
            a["flow_rate"] for a in analyses
            if a["sensor_id"] in ["SNS-T1", "SNS-T2"]
        ) / max(1, sum(1 for a in analyses if a["sensor_id"] in ["SNS-T1", "SNS-T2"]))

        head_tail_ratio = avg_tail_flow / max(avg_head_flow, 1.0)

        return {
            "overall_status": overall,
            "avg_head_flow": round(avg_head_flow, 2),
            "avg_tail_flow": round(avg_tail_flow, 2),
            "head_tail_ratio": round(head_tail_ratio, 3),
            "equity_alert": head_tail_ratio < 0.65,
            "sensor_analyses": analyses,
            "all_alerts": [a for s in analyses for a in s["alerts"]],
        }

    def simulate_live_reading(self, sensor_id: str, scenario: str = "normal") -> Dict:
        """Generate a simulated live sensor reading for demo purposes."""
        baseline = self.baseline_flows.get(sensor_id, 300.0)

        if scenario == "shortage":
            # 20% water reduction scenario
            if sensor_id.startswith("SNS-T"):
                flow = baseline * random.uniform(0.50, 0.62)  # tail-end worst affected
            elif sensor_id.startswith("SNS-M"):
                flow = baseline * random.uniform(0.68, 0.75)
            else:
                flow = baseline * random.uniform(0.82, 0.90)
        else:
            flow = baseline * random.uniform(0.92, 1.08)

        return {
            "sensor_id": sensor_id,
            "timestamp": datetime.utcnow(),
            "water_level": round(random.uniform(1.2, 3.2), 3),
            "flow_rate": round(flow, 2),
            "gate_open_percentage": round(random.uniform(55, 85), 1),
            "temperature": round(random.uniform(26, 38), 1),
            "rainfall": 0.0,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 2 – Equitable Distribution Scheduling Agent
# ═══════════════════════════════════════════════════════════════════════════════

class EquitableDistributionAgent:
    """
    Objective: Generate fair irrigation schedules that prioritize tail-end farmers
    without unfairly penalizing head-reach farmers.

    Autonomous actions:
    - Generate daily schedules
    - Recalculate on shortage detection
    - Update fairness scores

    Human approval required:
    - Schedule deviating > 30% from previous
    - Emergency reallocation affecting > 20 farmers
    """

    def generate_schedule(self, farmers_data: List[Dict],
                           total_available_water: float,
                           shortage_override: Optional[float] = None) -> Dict:
        """
        Main scheduling entry point.

        Returns schedule with allocations, equity metrics, and slot assignments.
        """
        # Convert to FarmerDemand objects
        demands = []
        for f in farmers_data:
            reach = ReachType(f.get("reach_type", "tail").lower())
            demands.append(FarmerDemand(
                farmer_id=f["farmer_id"],
                reach_type=reach,
                land_area=float(f.get("land_area", 1.0)),
                crop=f.get("crop", "Wheat"),
                crop_water_requirement=float(f.get("crop_water_requirement", 5.5)),
                previous_water_received=float(f.get("previous_water_received", 0.0)),
                expected_water=float(f.get("expected_water", 100.0)),
            ))

        result: ScheduleResult = allocate_water(demands, total_available_water, shortage_override)

        # Assign irrigation time slots
        slots = self._assign_time_slots(result.allocations)

        # Build response
        return {
            "schedule_id": "SCH-" + uuid.uuid4().hex[:8].upper(),
            "generated_at": datetime.utcnow().isoformat(),
            "total_available_water": result.total_available,
            "shortage_level": result.shortage_level,
            "head_equity_score": result.head_equity_score,
            "middle_equity_score": result.middle_equity_score,
            "tail_equity_score": result.tail_equity_score,
            "overall_fairness": result.overall_fairness,
            "head_tail_gap": result.head_tail_gap,
            "equity_alert": result.head_tail_gap > 0.15,
            "requires_human_approval": (
                result.shortage_level > 0.25 or result.head_tail_gap > 0.20
            ),
            "summary": result.summary,
            "allocations": [
                {
                    "farmer_id": a.farmer_id,
                    "reach_type": a.reach_type.value,
                    "crop": a.crop,
                    "expected_water": a.expected_water,
                    "allocated_water": a.allocated_water,
                    "fairness_score": a.fairness_score,
                    "priority_score": a.priority_score,
                    "irrigation_minutes": a.irrigation_minutes,
                    "slot": slots.get(a.farmer_id, {}),
                    "notes": a.notes,
                }
                for a in result.allocations
            ],
        }

    def _assign_time_slots(self, allocations: list) -> Dict[str, Dict]:
        """
        Assign non-overlapping irrigation slots starting from 6 AM tomorrow.
        Tail-end farmers get early morning slots (least evaporation loss).
        Head-reach farmers get midday slots.
        """
        base = datetime.utcnow().replace(hour=6, minute=0, second=0) + timedelta(days=1)
        slot_map = {}
        current_time = base

        # Sort: tail first (most priority, least evaporation in morning)
        order = {"tail": 0, "middle": 1, "head": 2}
        sorted_allocs = sorted(allocations, key=lambda a: order.get(a.reach_type.value, 1))

        for alloc in sorted_allocs:
            minutes = max(int(alloc.irrigation_minutes), 15)
            start = current_time
            end   = current_time + timedelta(minutes=minutes)
            slot_map[alloc.farmer_id] = {
                "start": start.isoformat(),
                "end":   end.isoformat(),
                "duration_minutes": minutes,
            }
            current_time = end + timedelta(minutes=5)  # 5-min buffer between slots

        return slot_map

    def calculate_fairness_report(self, allocations: List[Dict]) -> Dict:
        """Generate a fairness analysis report across reach types."""
        by_reach: Dict[str, List[float]] = {"head": [], "middle": [], "tail": []}
        for a in allocations:
            r = a.get("reach_type", "middle")
            if r in by_reach:
                by_reach[r].append(a.get("fairness_score", 1.0))

        def avg(lst): return round(sum(lst)/len(lst), 4) if lst else 0.0

        head_avg   = avg(by_reach["head"])
        middle_avg = avg(by_reach["middle"])
        tail_avg   = avg(by_reach["tail"])
        gap        = round(head_avg - tail_avg, 4)

        return {
            "head_avg_fairness":   head_avg,
            "middle_avg_fairness": middle_avg,
            "tail_avg_fairness":   tail_avg,
            "head_tail_gap":       gap,
            "equity_status": (
                "FAIR" if gap < 0.05 else
                "ACCEPTABLE" if gap < 0.10 else
                "ATTENTION" if gap < 0.15 else
                "INEQUITABLE"
            ),
            "total_farmers": len(allocations),
            "below_threshold": sum(1 for a in allocations if a.get("fairness_score", 1) < 0.75),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 3 – Farmer Water Availability Alert Agent
# ═══════════════════════════════════════════════════════════════════════════════

class FarmerAlertAgent:
    """
    Objective: Notify farmers about water availability, schedule changes,
    and emergencies in their language (English / Gujarati).

    Autonomous actions:
    - Send scheduled alerts for upcoming irrigation slots
    - Send shortage notifications
    - Send delay notifications

    Human approval required:
    - Emergency field bypass approvals
    """

    def __init__(self):
        self.pending_alerts: List[Dict] = []

    async def generate_farmer_alert(self, farmer: Dict,
                                     allocation: Dict,
                                     alert_type: str = "scheduled") -> Dict:
        """Generate a personalised alert for a farmer."""
        slot = allocation.get("slot", {})
        slot_start = slot.get("start", "Tomorrow 06:00")
        lang = farmer.get("language_preference", "en")

        ai_message = await explain_farmer_alert(
            farmer_name=farmer["farmer_name"],
            village=farmer["village"],
            reach_type=farmer.get("reach_type", "middle"),
            allocated_m3=allocation.get("allocated_water", 0),
            expected_m3=allocation.get("expected_water", 100),
            slot_start=slot_start,
            crop=farmer.get("crop", "Wheat"),
            language=lang,
        )

        alert = {
            "alert_id": "ALT-" + uuid.uuid4().hex[:8].upper(),
            "farmer_id": farmer["farmer_id"],
            "farmer_name": farmer["farmer_name"],
            "village": farmer["village"],
            "alert_type": alert_type,
            "language": lang,
            "message": ai_message,
            "slot_start": slot_start,
            "slot_end": slot.get("end", ""),
            "allocated_water_m3": allocation.get("allocated_water", 0),
            "fairness_score": allocation.get("fairness_score", 1.0),
            "timestamp": datetime.utcnow().isoformat(),
            "channels": ["dashboard", "sms", "whatsapp"],
            "delivered": False,
        }
        self.pending_alerts.append(alert)
        return alert

    async def generate_shortage_alert(self, affected_farmers: List[Dict],
                                       shortage_pct: float,
                                       head_eq: float, tail_eq: float) -> Dict:
        """Generate a batch shortage alert for affected farmers."""
        villages = list(set(f["village"] for f in affected_farmers))
        ai_explanation = await explain_water_shortage(shortage_pct, villages, head_eq, tail_eq)

        return {
            "alert_id": "SHT-" + uuid.uuid4().hex[:8].upper(),
            "alert_type": "shortage",
            "shortage_pct": shortage_pct,
            "affected_farmers": len(affected_farmers),
            "affected_villages": villages,
            "ai_explanation": ai_explanation,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if shortage_pct > 0.15 else "medium",
        }

    def get_farmer_water_status(self, farmer: Dict, allocation: Dict,
                                 canal_status: Dict) -> Dict:
        """Return current water status for farmer portal."""
        fairness = allocation.get("fairness_score", 1.0)
        slot = allocation.get("slot", {})

        if fairness >= 0.90:
            status_msg = "✅ Your water allocation is on schedule"
        elif fairness >= 0.75:
            status_msg = "⚠ Partial allocation – slight shortage in your section"
        else:
            status_msg = "🚨 Reduced allocation – canal shortage affecting your area"

        return {
            "farmer_id": farmer["farmer_id"],
            "farmer_name": farmer["farmer_name"],
            "village": farmer["village"],
            "reach_type": farmer.get("reach_type", "middle"),
            "crop": farmer.get("crop", "Wheat"),
            "expected_water_m3": allocation.get("expected_water", 0),
            "allocated_water_m3": allocation.get("allocated_water", 0),
            "fairness_score": fairness,
            "status_message": status_msg,
            "irrigation_slot_start": slot.get("start", ""),
            "irrigation_slot_end": slot.get("end", ""),
            "irrigation_duration_min": slot.get("duration_minutes", 0),
            "canal_status": canal_status.get("overall_status", "unknown"),
            "last_updated": datetime.utcnow().isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 4 – Dispute Detection & Mediation Agent
# ═══════════════════════════════════════════════════════════════════════════════

class DisputeDetectionAgent:
    """
    Objective: Detect, classify, and recommend resolutions for water-related disputes.

    Autonomous actions:
    - Classify complaint severity
    - Generate AI-powered resolution recommendations
    - Detect systemic patterns (repeated tail-end complaints)

    Human approval required:
    - All resolution implementations
    - Escalation to district authority
    """

    SEVERITY_KEYWORDS = {
        "critical": ["illegal", "blocking", "stolen", "destroyed", "critical", "emergency"],
        "high":     ["shortage", "3 days", "crop stress", "tail-end", "unfair", "ignored", "58%"],
        "medium":   ["missed slot", "late", "low pressure", "leaking", "schedule change"],
        "low":      ["late delivery", "slight", "minor", "query"],
    }

    def classify_severity(self, complaint_text: str) -> str:
        text_lower = complaint_text.lower()
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return severity
        return "normal"

    async def analyze_complaint(self, complaint: Dict,
                                 farmer: Dict,
                                 allocation_history: List[Dict]) -> Dict:
        """Full complaint analysis with Granite LLM."""
        history_summary = (
            f"Last 7 days: avg fairness score "
            f"{sum(a.get('fairness_score',1) for a in allocation_history) / max(len(allocation_history),1):.2%}"
            if allocation_history else "No recent history"
        )

        # Auto-classify first (deterministic)
        auto_severity = self.classify_severity(complaint["complaint_text"])

        # Get Granite analysis
        granite_result = await analyze_complaint(
            complaint_text=complaint["complaint_text"],
            farmer_name=farmer["farmer_name"],
            village=farmer["village"],
            reach_type=farmer.get("reach_type", "unknown"),
            allocation_history=history_summary,
        )

        return {
            "complaint_id": complaint.get("complaint_id", ""),
            "auto_severity": auto_severity,
            "ai_severity": granite_result.get("severity", auto_severity),
            "final_severity": granite_result.get("severity", auto_severity),
            "ai_summary": granite_result.get("summary", ""),
            "root_cause": granite_result.get("root_cause", ""),
            "ai_recommendation": granite_result.get("recommendation", ""),
            "full_analysis": granite_result.get("full_response", ""),
            "requires_authority_approval": auto_severity in ["critical", "high"],
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def detect_systemic_issues(self, complaints: List[Dict]) -> List[Dict]:
        """Detect patterns indicating systemic inequity rather than one-off issues."""
        issues = []

        # Count by reach type
        tail_complaints = [c for c in complaints if
                           c.get("reach_type") == "tail" and
                           c.get("status") in ["open", "under_review"]]

        if len(tail_complaints) >= 3:
            issues.append({
                "type": "systemic_tail_shortage",
                "severity": "high",
                "description": (
                    f"{len(tail_complaints)} open complaints from tail-reach farmers. "
                    "Possible systemic distribution inequity."
                ),
                "recommendation": (
                    "Conduct immediate audit of gate settings in middle-reach. "
                    "Increase tail-reach monitoring frequency."
                ),
                "auto_action": False,
            })

        # Check for repeated complaints from same village
        village_counts: Dict[str, int] = {}
        for c in complaints:
            v = c.get("village", "")
            village_counts[v] = village_counts.get(v, 0) + 1

        for village, count in village_counts.items():
            if count >= 2:
                issues.append({
                    "type": "repeated_village_complaints",
                    "severity": "medium",
                    "description": f"Village '{village}' has {count} recent complaints.",
                    "recommendation": f"Prioritise field inspection and special allocation review for {village}.",
                    "auto_action": False,
                })

        return issues


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 5 – Irrigation Efficiency Dashboard Agent
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardAgent:
    """
    Objective: Aggregate data from all agents and generate a unified dashboard
    view with natural-language AI insights.

    Autonomous actions:
    - Aggregate metrics in real-time
    - Generate natural-language insights via Granite
    - Identify KPI breaches

    Human approval required:
    - None (read-only aggregation)
    """

    async def generate_dashboard(
        self,
        canal_status: Dict,
        schedule: Dict,
        complaints: List[Dict],
        alerts: List[Dict],
        recommendations: List[Dict],
    ) -> Dict:
        """Generate comprehensive dashboard data."""

        shortage_pct    = schedule.get("shortage_level", 0.0)
        head_eq         = schedule.get("head_equity_score", 1.0)
        tail_eq         = schedule.get("tail_equity_score", 1.0)
        overall_fair    = schedule.get("overall_fairness", 1.0)
        head_tail_gap   = schedule.get("head_tail_gap", 0.0)
        active_alerts   = len([a for a in alerts if not a.get("is_acknowledged", False)])
        open_complaints = len([c for c in complaints if c.get("status") == "open"])
        critical_items  = len([a for a in alerts if a.get("severity") == "critical"])

        # Generate AI insight
        ai_insight = await generate_dashboard_insight(
            schedule_summary=schedule.get("summary", ""),
            head_eq=head_eq,
            tail_eq=tail_eq,
            shortage_pct=shortage_pct,
            active_alerts=active_alerts,
        )

        # KPI calculations
        kpis = self._calculate_kpis(schedule, canal_status, complaints)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "overall_system_status": self._overall_status(shortage_pct, critical_items, head_tail_gap),

            # Water metrics
            "water": {
                "total_available_m3": schedule.get("total_available_water", 0),
                "shortage_pct": round(shortage_pct * 100, 1),
                "head_flow_cumecs": canal_status.get("avg_head_flow", 0),
                "tail_flow_cumecs": canal_status.get("avg_tail_flow", 0),
                "head_tail_ratio": canal_status.get("head_tail_ratio", 0),
            },

            # Equity metrics
            "equity": {
                "head_score": head_eq,
                "middle_score": schedule.get("middle_equity_score", 1.0),
                "tail_score": tail_eq,
                "overall_fairness": overall_fair,
                "head_tail_gap": head_tail_gap,
                "equity_status": (
                    "FAIR" if head_tail_gap < 0.05 else
                    "ACCEPTABLE" if head_tail_gap < 0.10 else
                    "ATTENTION NEEDED" if head_tail_gap < 0.20 else
                    "INEQUITABLE – ACTION REQUIRED"
                ),
                "equity_alert": head_tail_gap > 0.15,
            },

            # Alerts & disputes
            "alerts_summary": {
                "total": len(alerts),
                "active": active_alerts,
                "critical": critical_items,
                "by_type": self._count_by_field(alerts, "alert_type"),
            },
            "complaints_summary": {
                "total": len(complaints),
                "open": open_complaints,
                "by_severity": self._count_by_field(complaints, "severity"),
            },

            # AI
            "ai_insight": ai_insight,
            "recommendations": recommendations[:5],

            # KPIs
            "kpis": kpis,
        }

    def _overall_status(self, shortage: float, critical: int, gap: float) -> str:
        if critical > 0 or shortage > 0.30:
            return "CRITICAL"
        if shortage > 0.15 or gap > 0.20:
            return "HIGH_ALERT"
        if shortage > 0.05 or gap > 0.10:
            return "WARNING"
        return "NORMAL"

    def _count_by_field(self, items: List[Dict], field: str) -> Dict:
        counts: Dict[str, int] = {}
        for item in items:
            v = str(item.get(field, "unknown"))
            counts[v] = counts.get(v, 0) + 1
        return counts

    def _calculate_kpis(self, schedule: Dict, canal_status: Dict, complaints: List[Dict]) -> Dict:
        allocations = schedule.get("allocations", [])
        total_expected = sum(a.get("expected_water", 0) for a in allocations)
        total_allocated = sum(a.get("allocated_water", 0) for a in allocations)

        distribution_efficiency = (
            round(total_allocated / total_expected, 4) if total_expected > 0 else 0
        )
        tail_allocs = [a for a in allocations if a.get("reach_type") == "tail"]
        head_allocs = [a for a in allocations if a.get("reach_type") == "head"]

        def avg_fair(lst):
            return round(sum(a.get("fairness_score",1) for a in lst) / max(len(lst),1), 4)

        return {
            "distribution_efficiency": distribution_efficiency,
            "head_fairness": avg_fair(head_allocs),
            "tail_fairness": avg_fair(tail_allocs),
            "head_tail_gap_pct": round(schedule.get("head_tail_gap", 0) * 100, 2),
            "open_disputes": len([c for c in complaints if c.get("status") == "open"]),
            "critical_alerts": len([a for a in canal_status.get("all_alerts", [])
                                     if a.get("severity") == "critical"]),
            "shortage_level_pct": round(schedule.get("shortage_level", 0) * 100, 1),
            "farmers_below_threshold": sum(
                1 for a in allocations if a.get("fairness_score", 1) < 0.75
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class AgentOrchestrator:
    """
    Coordinates all five agents.

    Workflow:
    Sensors → FlowMonitor → [shortage?] → DistributionAgent
                                        ↓
                              FarmerAlertAgent ← AI Alerts
                                        ↓
                              DisputeDetection ← Complaints
                                        ↓
                              DashboardAgent ← Full view + AI insight
    """

    def __init__(self):
        self.flow_agent       = CanalFlowMonitoringAgent()
        self.distribution     = EquitableDistributionAgent()
        self.alert_agent      = FarmerAlertAgent()
        self.dispute_agent    = DisputeDetectionAgent()
        self.dashboard_agent  = DashboardAgent()

    async def run_full_cycle(
        self,
        sensor_readings: List[Dict],
        farmers_data: List[Dict],
        total_water: float,
        complaints: List[Dict],
        alerts_db: List[Dict],
        recommendations_db: List[Dict],
        scenario: str = "normal",
    ) -> Dict:
        """Run one complete agent orchestration cycle."""

        # Step 1: Flow monitoring
        canal_status = self.flow_agent.get_canal_status(sensor_readings)
        shortage = canal_status.get("sensor_analyses", [{}])[0].get("shortage_estimate", 0.0) \
            if canal_status.get("sensor_analyses") else 0.0

        if scenario == "shortage":
            shortage = 0.20

        # Step 2: Distribution scheduling
        schedule = self.distribution.generate_schedule(
            farmers_data, total_water, shortage if shortage > 0.05 else None
        )

        # Step 3: Systemic dispute detection
        systemic_issues = self.dispute_agent.detect_systemic_issues(complaints)

        # Step 4: Dashboard
        dashboard = await self.dashboard_agent.generate_dashboard(
            canal_status=canal_status,
            schedule=schedule,
            complaints=complaints,
            alerts=alerts_db + canal_status.get("all_alerts", []),
            recommendations=recommendations_db,
        )

        return {
            "canal_status":    canal_status,
            "schedule":        schedule,
            "systemic_issues": systemic_issues,
            "dashboard":       dashboard,
            "requires_human_approval": schedule.get("requires_human_approval", False),
            "critical_alerts": [a for a in canal_status.get("all_alerts", [])
                                  if a.get("severity") == "critical"],
        }

    async def handle_chat_query(self, question: str, context: Dict) -> str:
        """Route chat query to Granite with system context."""
        return await answer_chat_query(question, context)

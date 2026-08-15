"""
Sensor simulation API – for demo and testing
"""
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services.sensor_simulator import simulate_all_sensors, simulate_reading
from ..agents.agents import CanalFlowMonitoringAgent

router = APIRouter()
_agent = CanalFlowMonitoringAgent()


@router.post("/sensor-data")
async def simulate_sensor_data(
    scenario: str = Query("normal", enum=["normal", "shortage", "anomaly", "recovery"]),
):
    """Simulate live sensor data for all sensors under a given scenario."""
    readings = simulate_all_sensors(scenario)
    canal_status = _agent.get_canal_status(readings)
    return {
        "scenario":   scenario,
        "readings":   readings,
        "canal_status": canal_status,
    }


@router.get("/demo-scenario")
async def run_demo_scenario():
    """
    Run the full hackathon demo scenario:
    Canal water drops 20% → system detects, reallocates fairly, prioritizes tail-end.
    """
    import asyncio
    from ..agents.agents import AgentOrchestrator, SAMPLE_FARMERS
    from ..ml.water_equity import run_sample_scenario

    orchestrator = AgentOrchestrator()

    # Before: normal conditions
    before_readings = simulate_all_sensors("normal")
    before_status   = orchestrator.flow_agent.get_canal_status(before_readings)
    before_schedule = run_sample_scenario(0.0)

    # After: 20% shortage
    after_readings  = simulate_all_sensors("shortage")
    after_status    = orchestrator.flow_agent.get_canal_status(after_readings)
    after_schedule  = run_sample_scenario(0.20)

    # Shortage alert
    shortage_pct = 0.20
    head_eq  = after_schedule.head_equity_score
    tail_eq  = after_schedule.tail_equity_score

    from ..services.granite_service import explain_water_shortage
    ai_explanation = await explain_water_shortage(
        shortage_pct=shortage_pct,
        affected_villages=["Vijapur", "Kalol", "Mansa", "Kadi"],
        head_eq=head_eq,
        tail_eq=tail_eq,
    )

    return {
        "demo_title": "20% Canal Water Reduction Scenario",
        "steps": [
            "1. Canal flow drops 20% due to reduced upstream inflow",
            "2. Flow Monitoring Agent detects anomaly at SNS-T1 and SNS-T2",
            "3. Distribution Agent recalculates with fairness-weighted algorithm",
            "4. Tail-end farmers protected via equity boost factor (1.12x)",
            "5. New irrigation schedule generated with head-tail gap reduced",
            "6. Farmer Alert Agent notifies affected farmers",
            "7. Granite LLM generates farmer-friendly explanation",
            "8. Dashboard shows before/after equity comparison",
            "9. Human canal authority reviews and approves gate adjustments",
        ],
        "before": {
            "canal_status":         before_status,
            "head_flow":            before_status.get("avg_head_flow"),
            "tail_flow":            before_status.get("avg_tail_flow"),
            "head_equity_score":    before_schedule.head_equity_score,
            "tail_equity_score":    before_schedule.tail_equity_score,
            "overall_fairness":     before_schedule.overall_fairness,
            "head_tail_gap":        before_schedule.head_tail_gap,
        },
        "after": {
            "canal_status":         after_status,
            "head_flow":            after_status.get("avg_head_flow"),
            "tail_flow":            after_status.get("avg_tail_flow"),
            "shortage_level":       f"{shortage_pct*100:.0f}%",
            "head_equity_score":    after_schedule.head_equity_score,
            "tail_equity_score":    after_schedule.tail_equity_score,
            "overall_fairness":     after_schedule.overall_fairness,
            "head_tail_gap":        after_schedule.head_tail_gap,
            "allocations": [
                {
                    "farmer": a.farmer_id,
                    "reach":  a.reach_type.value,
                    "crop":   a.crop,
                    "expected": a.expected_water,
                    "allocated": a.allocated_water,
                    "fairness": f"{a.fairness_score:.0%}",
                    "notes": a.notes,
                }
                for a in after_schedule.allocations
            ],
        },
        "ai_explanation": ai_explanation,
        "equity_improvement": {
            "head_tail_gap_before": f"{before_schedule.head_tail_gap:.2%}",
            "head_tail_gap_after":  f"{after_schedule.head_tail_gap:.2%}",
            "gap_reduction":        f"{(before_schedule.head_tail_gap - after_schedule.head_tail_gap)*100:.1f}%",
            "tail_farmers_protected": sum(1 for a in after_schedule.allocations
                                          if a.reach_type.value == "tail" and a.fairness_score >= 0.70),
        },
    }

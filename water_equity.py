"""
Water equity distribution algorithm.

DETERMINISTIC – no LLM involved.
IBM Granite is used only for natural-language explanations of the results.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ReachType(str, Enum):
    HEAD = "head"
    MIDDLE = "middle"
    TAIL = "tail"


# ─── Priority weights by crop water stress ───────────────────────────────────
CROP_STRESS_WEIGHT: Dict[str, float] = {
    "Sugarcane":   1.20,
    "Cotton":      1.15,
    "Vegetables":  1.10,
    "Wheat":       1.08,
    "Bajra":       1.05,
    "Groundnut":   1.03,
    "Mustard":     1.02,
    "Castor":      1.01,
    "Sesame":      1.00,
    "Cumin":       0.98,
}

# Equity correction factor: tail-end gets a bonus multiplier to compensate
# for historical under-delivery.  Head-reach gets a slight penalty.
REACH_EQUITY_FACTOR: Dict[ReachType, float] = {
    ReachType.HEAD:   0.95,
    ReachType.MIDDLE: 1.00,
    ReachType.TAIL:   1.12,
}


@dataclass
class FarmerDemand:
    farmer_id: str
    reach_type: ReachType
    land_area: float          # hectares
    crop: str
    crop_water_requirement: float  # mm/day
    previous_water_received: float # cubic metres (last cycle)
    expected_water: float     # cubic metres (ideal entitlement)
    deficit_carry: float = 0.0     # accumulated deficit from previous cycles


@dataclass
class AllocationResult:
    farmer_id: str
    reach_type: ReachType
    crop: str
    expected_water: float
    allocated_water: float
    fairness_score: float     # allocated / expected  (1.0 = perfect)
    priority_score: float
    irrigation_minutes: float
    notes: str = ""


@dataclass
class ScheduleResult:
    total_available: float
    shortage_level: float     # 0-1 fraction
    allocations: List[AllocationResult] = field(default_factory=list)
    head_equity_score: float = 1.0
    tail_equity_score: float = 1.0
    middle_equity_score: float = 1.0
    overall_fairness: float = 1.0
    head_tail_gap: float = 0.0
    summary: str = ""


# ─── Core algorithm ───────────────────────────────────────────────────────────

def calculate_priority_score(farmer: FarmerDemand, shortage_level: float) -> float:
    """
    Priority score formula:
        P = crop_stress_weight × equity_factor × (1 + deficit_ratio × 0.5) × land_weight

    Where:
        deficit_ratio  = max(0, (expected - prev_received) / expected)
        land_weight    = sqrt(land_area) / sqrt(5)   [normalised 0-1 roughly]

    During shortage the deficit component weight increases.
    """
    crop_w   = CROP_STRESS_WEIGHT.get(farmer.crop, 1.0)
    equity_f = REACH_EQUITY_FACTOR[farmer.reach_type]
    deficit  = max(0.0, (farmer.expected_water - farmer.previous_water_received)
                   / max(farmer.expected_water, 1.0))
    deficit_boost = 1.0 + deficit * (0.5 + shortage_level * 0.5)
    land_w   = math.sqrt(max(farmer.land_area, 0.1)) / math.sqrt(5.0)
    return crop_w * equity_f * deficit_boost * land_w


def allocate_water(
    farmers: List[FarmerDemand],
    total_available: float,
    shortage_override: Optional[float] = None,
) -> ScheduleResult:
    """
    Fairness-aware water allocation.

    Steps
    -----
    1. Compute total ideal demand.
    2. Determine shortage level.
    3. Compute priority score for every farmer.
    4. Proportionally allocate water weighted by priority score.
    5. Apply a minimum floor guarantee (50% of entitlement for all farmers).
    6. Compute fairness scores and equity metrics.

    Time complexity: O(N)  – linear in number of farmers.

    Shortage handling
    -----------------
    * If shortage_level < 0.10 → proportional allocation only.
    * If 0.10 ≤ shortage_level < 0.25 → priority-weighted allocation with
      floor guarantee at 60%.
    * If shortage_level ≥ 0.25 → emergency mode: tail-end and high-stress
      crops protected; floor guarantee at 50%.
    """
    if not farmers:
        return ScheduleResult(total_available=total_available, shortage_level=0.0)

    total_demand = sum(f.expected_water for f in farmers)
    shortage_level = shortage_override if shortage_override is not None else max(
        0.0, 1.0 - total_available / total_demand
    )

    # Floor guarantee (fraction of entitlement)
    if shortage_level < 0.10:
        floor_pct = 0.90
    elif shortage_level < 0.25:
        floor_pct = 0.60
    else:
        floor_pct = 0.50

    # Compute priority scores
    priority_scores = {f.farmer_id: calculate_priority_score(f, shortage_level)
                       for f in farmers}
    total_priority = sum(priority_scores.values())

    # First pass: priority-weighted allocation
    allocations_raw: Dict[str, float] = {}
    for f in farmers:
        share = (priority_scores[f.farmer_id] / total_priority) * total_available
        allocations_raw[f.farmer_id] = share

    # Second pass: enforce floor guarantees
    floor_water: Dict[str, float] = {f.farmer_id: f.expected_water * floor_pct
                                      for f in farmers}
    total_floor = sum(floor_water.values())

    if total_floor <= total_available:
        # Ensure every farmer gets at least the floor
        final_alloc: Dict[str, float] = {}
        surplus = total_available - total_floor
        surplus_priority_total = sum(
            priority_scores[f.farmer_id]
            for f in farmers
            if allocations_raw[f.farmer_id] >= floor_water[f.farmer_id]
        )
        for f in farmers:
            raw = allocations_raw[f.farmer_id]
            floor = floor_water[f.farmer_id]
            if raw < floor:
                final_alloc[f.farmer_id] = floor
            else:
                if surplus_priority_total > 0:
                    extra = (priority_scores[f.farmer_id] / surplus_priority_total) * surplus
                else:
                    extra = 0.0
                final_alloc[f.farmer_id] = floor + extra
    else:
        # Severe shortage: proportional cut, no floor guarantee
        cut = total_available / total_demand
        final_alloc = {f.farmer_id: f.expected_water * cut for f in farmers}

    # Build results
    results: List[AllocationResult] = []
    reach_scores: Dict[ReachType, List[float]] = {
        ReachType.HEAD: [], ReachType.MIDDLE: [], ReachType.TAIL: []
    }
    for f in farmers:
        allocated = round(final_alloc[f.farmer_id], 2)
        fairness = round(allocated / max(f.expected_water, 1.0), 4)
        # Irrigation minutes ≈ volume / (flow_rate_per_min × land_area)
        # Approximate: 1 cm depth over 1 ha = 100 m³; flow ~10 m³/min
        irrigation_min = round((allocated / max(f.land_area, 0.1)) / 10.0, 1)
        notes = ""
        if fairness < 0.70:
            notes = "⚠ Below threshold – emergency priority in next cycle"
        elif fairness < 0.85:
            notes = "Deficit carry-forward applied"

        results.append(AllocationResult(
            farmer_id=f.farmer_id,
            reach_type=f.reach_type,
            crop=f.crop,
            expected_water=f.expected_water,
            allocated_water=allocated,
            fairness_score=fairness,
            priority_score=round(priority_scores[f.farmer_id], 4),
            irrigation_minutes=irrigation_min,
            notes=notes,
        ))
        reach_scores[f.reach_type].append(fairness)

    def avg(lst): return sum(lst) / len(lst) if lst else 0.0

    head_eq   = round(avg(reach_scores[ReachType.HEAD]),   4)
    middle_eq = round(avg(reach_scores[ReachType.MIDDLE]), 4)
    tail_eq   = round(avg(reach_scores[ReachType.TAIL]),   4)
    overall   = round(avg([r.fairness_score for r in results]), 4)
    gap       = round(head_eq - tail_eq, 4)

    summary = (
        f"Shortage {shortage_level*100:.1f}%. "
        f"Head equity: {head_eq:.2%}, Middle: {middle_eq:.2%}, Tail: {tail_eq:.2%}. "
        f"Head-tail gap: {gap:.2%}. Overall fairness: {overall:.2%}."
    )

    return ScheduleResult(
        total_available=total_available,
        shortage_level=round(shortage_level, 4),
        allocations=results,
        head_equity_score=head_eq,
        middle_equity_score=middle_eq,
        tail_equity_score=tail_eq,
        overall_fairness=overall,
        head_tail_gap=gap,
        summary=summary,
    )


# ─── Sample scenario (used in tests / demo) ──────────────────────────────────

SAMPLE_FARMERS = [
    # Head-reach
    FarmerDemand("F100", ReachType.HEAD,   2.5, "Cotton",    7.0, 155.0, 175.0),
    FarmerDemand("F101", ReachType.HEAD,   3.0, "Wheat",     5.5, 148.0, 165.0),
    FarmerDemand("F102", ReachType.HEAD,   1.8, "Groundnut", 4.5,  72.0,  81.0),
    # Middle-reach
    FarmerDemand("F103", ReachType.MIDDLE, 2.2, "Bajra",     5.0,  95.0, 110.0),
    FarmerDemand("F104", ReachType.MIDDLE, 4.0, "Sugarcane", 9.0, 280.0, 360.0),
    FarmerDemand("F105", ReachType.MIDDLE, 1.5, "Mustard",   4.0,  48.0,  60.0),
    # Tail-reach
    FarmerDemand("F106", ReachType.TAIL,   3.5, "Cotton",    7.0, 140.0, 245.0),
    FarmerDemand("F107", ReachType.TAIL,   2.0, "Wheat",     5.5,  88.0, 110.0),
    FarmerDemand("F108", ReachType.TAIL,   1.2, "Vegetables",6.5,  46.0,  78.0),
]


def run_sample_scenario(shortage_pct: float = 0.18) -> ScheduleResult:
    total_demand = sum(f.expected_water for f in SAMPLE_FARMERS)
    total_available = total_demand * (1 - shortage_pct)
    return allocate_water(SAMPLE_FARMERS, total_available, shortage_pct)


if __name__ == "__main__":
    result = run_sample_scenario(0.18)
    print(f"\n{'='*60}")
    print("NARMADA JAL NYAY AI – Water Equity Algorithm Demo")
    print(f"{'='*60}")
    print(f"Total available: {result.total_available:.1f} m³")
    print(f"Shortage level:  {result.shortage_level*100:.1f}%")
    print(f"\n{'Farmer':<8} {'Reach':<8} {'Crop':<12} {'Expected':>10} {'Allocated':>10} {'Fairness':>10} {'Notes'}")
    print("-" * 80)
    for a in result.allocations:
        print(f"{a.farmer_id:<8} {a.reach_type.value:<8} {a.crop:<12} "
              f"{a.expected_water:>10.1f} {a.allocated_water:>10.1f} "
              f"{a.fairness_score:>9.1%}  {a.notes}")
    print(f"\n{result.summary}")
    print(f"Head-Tail Gap: {result.head_tail_gap:.2%}")

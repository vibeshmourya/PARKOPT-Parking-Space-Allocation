"""
baseline_allocation.py
Analytical baseline allocation using proportional demand distribution.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


def compute_proportional_baseline(
    capacities: List[int],
    demands: List[int],
    budget: int,
    weights: Optional[List[float]] = None,
    facility_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Computes an analytical baseline allocation by distributing the managed permit budget B
    proportionally to each facility's estimated demand, subject to physical capacity.
    
    Heuristic Methodology:
    1. Demand Share: For each facility i, its demand ratio is:
          p_i = d_i / SUM(d_k)
    2. Ideal Permit Share:
          s_i = B * p_i
    3. Capacity & Demand Bound:
          M_i = min(d_i, C_i)
    4. Integer Allocation via Largest Remainder (Hamilton Method) with Upper Bound M_i:
          x_i_floor = min(M_i, floor(s_i))
       Surplus budget units are assigned to facilities with remaining headroom (x_i < M_i),
       prioritizing the largest fractional remainder (s_i - floor(s_i)).
    
    Academic Note:
    This baseline represents standard administrative practice where permits are
    apportioned according to nominal size/demand without mathematical optimization
    of priority weights or marginal congestion relief.
    
    Returns:
        pd.DataFrame: Columns ['Facility', 'Capacity', 'EstimatedDemand', 'BaselineAllocation',
                              'UnmetDemand', 'CapacityUtilizationPct', 'PriorityWeight',
                              'WeightedContribution']
    """
    n = len(capacities)
    caps = np.array(capacities, dtype=int)
    dems = np.array(demands, dtype=int)
    w = np.array(weights if weights is not None else np.ones(n), dtype=float)
    names = facility_names or [f"Facility_{i+1}" for i in range(n)]

    effective_max = np.minimum(dems, caps)
    total_allocatable = int(effective_max.sum())
    total_demand = int(dems.sum())

    # If budget exceeds or equals allocatable demand, everyone gets their max
    if budget >= total_allocatable:
        baseline_alloc = effective_max.copy()
    elif total_demand == 0 or budget <= 0:
        baseline_alloc = np.zeros(n, dtype=int)
    else:
        # Standard proportional allocation
        shares = (budget * (dems / total_demand))
        # Initial floor allocation capped at M_i
        base_alloc = np.minimum(effective_max, np.floor(shares).astype(int))
        allocated = int(base_alloc.sum())
        remainder = budget - allocated

        # Distribute remaining permits by largest fractional part
        if remainder > 0:
            fractional_parts = shares - np.floor(shares)
            # Sort indices by remainder descending
            sort_indices = np.argsort(-fractional_parts)
            for idx in sort_indices:
                if remainder <= 0:
                    break
                if base_alloc[idx] < effective_max[idx]:
                    base_alloc[idx] += 1
                    remainder -= 1

            # If remainder still remains (because some lots hit cap), distribute to any lot with headroom
            if remainder > 0:
                for idx in range(n):
                    if remainder <= 0:
                        break
                    avail_headroom = effective_max[idx] - base_alloc[idx]
                    if avail_headroom > 0:
                        add_units = min(remainder, avail_headroom)
                        base_alloc[idx] += add_units
                        remainder -= add_units

        baseline_alloc = base_alloc

    # Derived baseline metrics
    unmet_demand = np.maximum(0, dems - baseline_alloc)
    utilization_pct = np.where(caps > 0, (baseline_alloc / caps) * 100.0, 0.0).round(2)
    weighted_contrib = (baseline_alloc * w).round(2)

    df_base = pd.DataFrame({
        "Facility": names,
        "Capacity": caps,
        "EstimatedDemand": dems,
        "BaselineAllocation": baseline_alloc,
        "UnmetDemand": unmet_demand,
        "CapacityUtilizationPct": utilization_pct,
        "PriorityWeight": w.round(4),
        "WeightedContribution": weighted_contrib
    })

    return df_base


if __name__ == "__main__":
    caps = [500, 300, 200]
    dems = [400, 350, 150]
    b = 600
    w = [1.0, 2.0, 1.0]
    res = compute_proportional_baseline(caps, dems, b, w)
    print("Baseline Allocation Test:")
    print(res.to_string())
    print("Total baseline allocated:", res["BaselineAllocation"].sum())
    print("Total baseline weighted value:", res["WeightedContribution"].sum())

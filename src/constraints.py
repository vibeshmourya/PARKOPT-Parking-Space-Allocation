"""
constraints.py
Mathematical constraint formulations and budget validation for Linear Programming.
Part of MCA ITOR Project: Optimal Parking Space Allocation Using Linear Programming.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


class OptimizationConstraints:
    """
    Manages and validates constraints for the Managed Parking Permit Allocation LP.
    
    Decision Variables:
        x_i: Managed parking permits allocated to facility i (i = 1, ..., n).
        
    Mathematical Constraints:
        1. Budget Constraint:            SUM(x_i) <= B
        2. Demand Constraint:            x_i <= d_i           for all i
        3. Physical Capacity Constraint: x_i <= C_i           for all i
        4. Minimum Allocation (if any):  x_i >= min_alloc_i   for all i
        5. Non-negativity & Integrality: x_i >= 0, x_i in Z   for all i
    """

    def __init__(
        self,
        capacities: List[int],
        demands: List[int],
        budget: int,
        facility_names: Optional[List[str]] = None,
        min_allocations: Optional[List[int]] = None
    ):
        self.capacities = np.array(capacities, dtype=int)
        self.demands = np.array(demands, dtype=int)
        self.budget = int(budget)
        self.n = len(self.capacities)
        self.facility_names = facility_names or [f"Facility_{i+1}" for i in range(self.n)]
        self.min_allocations = (
            np.array(min_allocations, dtype=int)
            if min_allocations is not None
            else np.zeros(self.n, dtype=int)
        )

        if len(self.demands) != self.n:
            raise ValueError("Capacities and Demands must have identical length.")
        if len(self.min_allocations) != self.n:
            raise ValueError("Min allocations must match number of facilities.")

        # Effective upper bound per facility: min(d_i, C_i)
        self.effective_caps = np.minimum(self.demands, self.capacities)
        self.total_allocatable_demand = int(self.effective_caps.sum())
        self.total_capacity = int(self.capacities.sum())
        self.total_demand = int(self.demands.sum())

    def check_feasibility(self) -> Tuple[bool, str]:
        """
        Validates trivial feasibility conditions before invoking solver.
        """
        # Budget cannot be negative
        if self.budget < 0:
            return False, f"Budget B={self.budget} cannot be negative."

        # Check if min allocations exceed physical capacity or demand
        for i in range(self.n):
            if self.min_allocations[i] > self.capacities[i]:
                return False, (
                    f"Infeasible: Min allocation for {self.facility_names[i]} "
                    f"({self.min_allocations[i]}) exceeds physical capacity ({self.capacities[i]})."
                )
            if self.min_allocations[i] > self.demands[i]:
                return False, (
                    f"Infeasible: Min allocation for {self.facility_names[i]} "
                    f"({self.min_allocations[i]}) exceeds estimated demand ({self.demands[i]})."
                )

        # Check if sum of min allocations exceeds total budget
        if self.min_allocations.sum() > self.budget:
            return False, (
                f"Infeasible: Sum of minimum required allocations ({self.min_allocations.sum()}) "
                f"exceeds total permit budget B={self.budget}."
            )

        return True, "Constraints are mathematically feasible."

    def is_budget_binding(self) -> Tuple[bool, str]:
        """
        Determines whether the permit budget B is strictly binding or non-binding.
        If B >= SUM(min(d_i, C_i)), every facility can receive its full demand,
        meaning the budget constraint is mathematically slack (non-binding).
        """
        if self.budget >= self.total_allocatable_demand:
            return False, (
                f"Notice: Budget B={self.budget:,} exceeds or meets total allocatable demand "
                f"({self.total_allocatable_demand:,}). The budget constraint is NON-BINDING; "
                f"each facility will be allocated exactly min(d_i, C_i)."
            )
        else:
            scarcity = self.total_allocatable_demand - self.budget
            return True, (
                f"Resource Scarcity Confirmed: Budget B={self.budget:,} is strictly BINDING. "
                f"Total allocatable demand exceeds budget by {scarcity:,} permits."
            )

    def get_standard_budget_scenarios(self) -> Dict[str, int]:
        """
        Generates standard realistic permit budget scenarios based on allocatable demand.
        Explicitly identified as simulation scenarios.
        """
        tot = self.total_allocatable_demand
        return {
            "Low Budget (50% of Allocatable Demand)": int(round(tot * 0.50)),
            "Medium Budget (75% of Allocatable Demand)": int(round(tot * 0.75)),
            "High Budget (90% of Allocatable Demand)": int(round(tot * 0.90)),
            "Full Demand Budget (100% of Allocatable Demand)": tot
        }


if __name__ == "__main__":
    caps = [500, 300, 200]
    dems = [400, 350, 150]
    b = 600
    cons = OptimizationConstraints(caps, dems, b)
    print("Feasibility:", cons.check_feasibility())
    print("Binding Check:", cons.is_budget_binding())
    print("Scenarios:", cons.get_standard_budget_scenarios())


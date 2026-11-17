# Academic Mathematical Formulation: Optimal Parking Space Allocation Using Linear Programming
**Course:** MCA ITOR (Introduction to Operations Research)  
**Project Domain:** Operations Research / Mathematical Optimization  
**Technique:** Integer Linear Programming (ILP)  
**Optimization Solver:** PuLP (Branch and Bound with CBC Solver)  
**Dataset:** Parking Birmingham (30 Municipal Facilities)  
**Document Phase:** Phase 2 Mathematical Model  

---

## 1. Problem Definition

In municipal traffic operations, parking demand is unevenly distributed across urban spaces. In Birmingham, UK, central shopping and healthcare facilities experience severe congestion and demand overflow, while expansive peripheral and arena car parks remain chronic capacity reservoirs with thousands of empty bays.

Because parking facilities are fixed geographic assets, physical parking spaces cannot be physically moved between locations. Therefore, this Operations Research system formulates the allocation problem as an **optimal centralized distribution of a limited quota of managed parking permits or admission admission slots** across the 30 municipal facilities.

The municipal authority possesses a limited allocation budget $B$ of managed permits/quotas to distribute across the city's $n = 30$ parking facilities. The objective is to maximize total priority-weighted parking demand served while strictly respecting the physical capacity of each facility, the estimated demand of each facility, and the overall permit budget.

---

## 2. Model Assumptions

1. **Geographic Immutability:** Parking infrastructure is geographically fixed. Decision variables represent permit or admission quota allocations rather than physical structure relocation.
2. **Facility Independence:** Demand at facility $i$ is estimated based on historical arrivals and is initially modeled independently of reallocation at facility $j$ (modal shift or secondary driver diversion can be analyzed in scenario planning).
3. **Integer Indivisibility:** Permits and admission quotas represent discrete motor vehicles and cannot be fractionally assigned ($x_i \in \mathbb{Z}_{\ge 0}$).
4. **Deterministic Parameters:** Estimated demand $d_i$, physical capacity $C_i$, and priority weights $w_i$ are treated as deterministic parameters within each solving run.
5. **Budget Scarcity:** To present an authentic Operations Research challenge, the total permit budget $B$ is constrained such that $B < \sum_{i=1}^{n} \min(d_i, C_i)$. When $B$ meets or exceeds allocatable demand, the system detects and reports a non-binding constraint.

---

## 3. Decision Variables

Let $i \in \{1, 2, \dots, n\}$ index the $n = 30$ parking facilities in the Birmingham municipal network.

$$\begin{aligned}
x_i &\in \mathbb{Z}_{\ge 0} \quad \text{for } i = 1, 2, \dots, 30
\end{aligned}$$

**Operational Interpretation:**  
$x_i$ represents the number of managed parking permits or guaranteed admission quotas assigned to parking facility $i$. Each permit grants authorized admission for one vehicle at facility $i$.

---

## 4. Model Parameters

| Parameter | Mathematical Symbol | Domain | Operational Meaning | Source |
| :--- | :---: | :---: | :--- | :--- |
| **Number of Facilities** | $n$ | $n = 30$ | Total parking facilities in Birmingham | Dataset (`SystemCodeNumber`) |
| **Physical Capacity** | $C_i$ | $\mathbb{Z}_{> 0}$ | Total marked parking bays at facility $i$ | Dataset (`Capacity`) |
| **Estimated Demand** | $d_i$ | $\mathbb{Z}_{\ge 0}$ | Estimated vehicle parking demand for facility $i$ | Historical Occupancy Model |
| **Priority Weight** | $w_i$ | $\mathbb{R}_{> 0}$ | Policy weight reflecting congestion pressure | Derived Operational Metric |
| **Permit Budget** | $B$ | $\mathbb{Z}_{> 0}$ | Total managed permit quota available for allocation | Municipal Policy Constraint |
| **Minimum Quota** | $\ell_i$ | $\mathbb{Z}_{\ge 0}$ | Minimum guaranteed allocation reserved for facility $i$ | Operational SLA (Default: $0$) |

---

## 5. Demand Estimation Methods

Historical occupancy observations from Phase 1 ($O_{i,t}^{\text{clean}} \ge 0$) are used to estimate facility demand $d_i$. Four statistical estimators are implemented:

1. **Historical Mean Occupancy (Average Baseline):**
   $$d_i^{\text{mean}} = \left\lfloor \frac{1}{T_i} \sum_{t=1}^{T_i} O_{i,t}^{\text{clean}} \right\rceil$$

2. **85th Percentile Occupancy (Standard High Demand):**
   $$d_i^{\text{P85}} = \left\lfloor P_{85}\left(O_{i,t}^{\text{clean}}\right) \right\rceil$$

3. **95th Percentile Occupancy (Robust Peak Demand - Default):**
   $$d_i^{\text{P95}} = \left\lfloor P_{95}\left(O_{i,t}^{\text{clean}}\right) \right\rceil$$

4. **Maximum Observed Occupancy (Extreme Stress Test):**
   $$d_i^{\text{max}} = \max_{t} O_{i,t}^{\text{clean}}$$

### Method Comparison across All 30 Birmingham Facilities:
- **Total Physical Capacity ($\sum C_i$):** $39,956 \text{ bays}$
- **Total Mean Demand ($\sum d_i^{\text{mean}}$):** $18,404 \text{ vehicles}$ (System ratio: $46.06\%$)
- **Total 85th Percentile Demand ($\sum d_i^{\text{P85}}$):** $25,426 \text{ vehicles}$ (System ratio: $63.64\%$)
- **Total 95th Percentile Demand ($\sum d_i^{\text{P95}}$):** $28,839 \text{ vehicles}$ (System ratio: $72.18\%$)
- **Total Maximum Observed Demand ($\sum d_i^{\text{max}}$):** $33,167 \text{ vehicles}$ (System ratio: $83.01\%$)

> [!NOTE]
> **Right-Censored Demand Limitation:**  
> In car parks operating at or near $100\%$ capacity (e.g., `BHMBCCTHL01`, `BHMBRCBRG01`), sensors only measure *satisfied demand* (vehicles inside). Arriving drivers turned away due to lack of space are unrecorded. Consequently, occupancy-based metrics represent a conservative lower bound on true latent demand during peak congestion.

---

## 6. Objective Function

The objective is to maximize the total priority-weighted demand served across all 30 facilities:

$$\text{Maximize } Z = \sum_{i=1}^{n} w_i x_i$$

**Operations Research Justification:**  
Under an unweighted objective ($w_i = 1$), the model treats a parking permit at an empty suburban lot identically to a permit at an overcrowded central hospital or shopping district. By introducing priority weights $w_i$, the linear objective prioritizes allocating scarce permit resources to high-congestion facilities where unmet demand creates severe local traffic queues.

---

## 7. Mathematical Constraints

The optimization model enforces five sets of linear constraints:

### Constraint A: Total Managed Permit Allocation Budget
The total permits allocated across all facilities cannot exceed the available municipal budget $B$:
$$\sum_{i=1}^{n} x_i \le B$$

### Constraint B: Estimated Facility Demand
No parking facility receives more permits than its estimated vehicle demand:
$$x_i \le d_i \quad \forall i \in \{1, 2, \dots, n\}$$

### Constraint C: Existing Physical Capacity Bound
No parking facility can be allocated permits exceeding its physical bay capacity $C_i$:
$$x_i \le C_i \quad \forall i \in \{1, 2, \dots, n\}$$

*Note:* Constraints B and C together guarantee that $x_i \le \min(d_i, C_i)$ for all $i$.

### Constraint D: Minimum Service Guarantee (Optional Policy Constraint)
Facilities may be assigned a minimum service quota $\ell_i \ge 0$:
$$x_i \ge \ell_i \quad \forall i \in \{1, 2, \dots, n\}$$

### Constraint E: Non-Negativity and Integrality
Allocations must be non-negative discrete integers:
$$x_i \in \mathbb{Z}_{\ge 0} \quad \forall i \in \{1, 2, \dots, n\}$$

---

## 8. Priority Weight Formulations

Three priority scenarios are implemented without fabricating demographic assumptions:

### Scenario 1: Equal Priority ($w_i = 1.0$)
Every facility is weighted equally:
$$w_i = 1.0 \quad \forall i$$
The objective reduces to maximizing the absolute volume of permits allocated: $\max Z = \sum x_i$.

### Scenario 2: Congestion-Sensitive Priority (Default)
Priority weights scale proportionally with historical demand pressure:
Let $u_i = \frac{\bar{O}_i}{C_i}$ be the historical average utilization rate of facility $i$, and let $u_{\max} = \max_{j} u_j$.
$$w_i = 1.0 + 2.0 \times \left(\frac{u_i}{u_{\max}}\right)$$

**Properties:**
- $w_i \in [1.0, 3.0]$ for all facilities.
- The most severely congested facility (`BHMBRTARC01`, $u_i = 77.66\%$) receives $w_i = 3.000$.
- Underutilized facilities (`NIA North`, $u_i = 7.53\%$) receive weights near $1.194$.
- Weights are deterministic, transparent, and derived directly from observed sensor data.

### Scenario 3: Custom Priority
Users can supply a manual vector of weights $[w_1, \dots, w_n]$ with $w_i \ge 0$ to model specific policy priorities (e.g., transit interchange support, commercial retail priority).

---

## 9. Allocation Budget Scenarios and Binding Analysis

The effective total allocatable demand is defined as:
$$D_{\text{allocatable}} = \sum_{i=1}^{n} \min(d_i, C_i)$$

For 95th percentile demand ($d_i^{\text{P95}}$), $D_{\text{allocatable}} = 28,788 \text{ permits}$.

| Scenario Name | Fraction of Allocatable Demand | Permit Budget ($B$) | Scarcity Status | Constraint Status |
| :--- | :---: | :---: | :--- | :--- |
| **Low Budget** | $50\%$ | $14,394$ | Severe permit scarcity | **Strictly Binding** |
| **Medium Budget** | $75\%$ | $21,617$ | Moderate permit scarcity | **Strictly Binding** |
| **High Budget** | $90\%$ | $25,909$ | Mild permit scarcity | **Strictly Binding** |
| **Full Capacity Budget** | $100\%$ | $28,788$ | No scarcity | **Non-Binding** ($x_i = \min(d_i, C_i)$) |

If $B \ge D_{\text{allocatable}}$, the model automatically issues an informational notice that the budget constraint is non-binding, as every facility can receive its upper-bound allocation.

---

## 10. Solver Methodology

The model is formulated in Python using **PuLP** and solved via the **COIN-OR Branch and Cut (CBC)** solver:

```text
Problem: Optimal_Parking_Permit_Allocation
Variables: 30 Integer Variables (bounded: lowBound=0, upBound=min(d_i, C_i))
Objective: Maximize Linear Function
Constraints: 1 Budget Constraint + 60 Explicit Bound Constraints
Algorithm: Simplex method + Branch and Bound for integer integrality
Complexity: Highly tractable (solves in < 0.05 seconds)
```

---

## 11. Baseline Allocation Methodology

To provide a fair, mathematically rigorous benchmark, we implement a **Proportional Demand Distribution Baseline** reflecting standard municipal non-optimized administrative allocations:

1. **Demand Share:** Each facility calculates its proportion of total demand:
   $$p_i = \frac{d_i}{\sum_{k=1}^n d_k}$$
2. **Ideal Share:**
   $$s_i = B \times p_i$$
3. **Capacity Capping:**
   $$M_i = \min(d_i, C_i)$$
4. **Hamilton (Largest-Remainder) Integer Distribution:**
   $$x_i^{\text{base}} = \min(M_i, \lfloor s_i \rfloor)$$
   Remaining permits $R = B - \sum x_i^{\text{base}}$ are apportioned by descending fractional parts $(s_i - \lfloor s_i \rfloor)$ subject to $x_i^{\text{base}} \le M_i$.

---

## 12. Mathematical Limitations

1. **Absence of User Demographics:** The Birmingham dataset lacks user distinctions (faculty, students, visitors). All allocations apply to municipal vehicle quotas.
2. **Right-Censored Observations:** True latent demand during peak hours is capped by facility physical capacity.
3. **Linearity of Value:** The objective assumes each served vehicle at facility $i$ yields a constant marginal value $w_i$. Nonlinear diminishing returns (e.g., quadratic congestion penalties) could be explored in advanced nonlinear extensions.
4. **Spatial Fixedness:** Permits assigned to facility $i$ can only be redeemed at facility $i$. Inter-facility vehicular re-routing is not dynamically modeled in the static LP.

---

## 13. Interpretation of Optimal Results (Medium Budget $B = 21,617$)

Under a medium budget of $21,617$ permits ($75\%$ of total peak demand) with Congestion Priority:

| Metric | Proportional Baseline | PuLP Optimized Allocation | Delta ($\Delta$) | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Total Permits Allocated** | $21,617$ | $21,617$ | $0$ | Full Budget Utilized ($100\%$) |
| **Total Unmet Demand** | $7,222$ | $7,222$ | $0$ | Balanced aggregate deficit |
| **Objective Value ($Z$)** | $49,584.86$ | **$53,274.47$** | **$+3,689.61$** | **$+7.44\%$ Gain** |
| **Central Saturated Lots Allocation** | $75.0\%$ of demand | **$100.0\%$ of capacity** | $+25.0\%$ | Complete congestion relief |
| **Peripheral Underutilized Lots Allocation** | Substantial idle quota | Quota reclaimed | Reduced | Eliminates wasted permits |

### Strategic Insight:
The LP model strategically shifts permit quotas away from chronically underutilized peripheral lots (e.g., `Others-CCCPS98`, `Others-CCCPS202`, `Others-CCCPS119a`) and channels them directly into downtown bottleneck facilities (`BHMBCCTHL01`, `BHMBRCBRG01`, `BHMNCPNHS01`), maximizing municipal utility without building a single additional parking bay.

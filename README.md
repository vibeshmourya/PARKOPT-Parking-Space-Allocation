# PARKOPT: Intelligent Smart Parking Allocation System
### Optimal Parking Space Allocation Using Linear Programming

**Master of Computer Applications (MCA) &bull; Introduction to Operations Research (ITOR)**

---

## 1. Project Overview

**PARKOPT** is a full-stack Operations Research and analytics application designed to solve the spatial and temporal parking congestion problem across modern smart parking facilities. Using empirical IoT sensor observations from the **Smart Parking Management Dataset (Kaggle)**, the system formulates and solves a **Bounded Integer Linear Programming (ILP)** problem using **PuLP (COIN-OR CBC Solver)** to determine the optimal allocation of scarce managed parking permits and admission quotas across four designated facility zones (`Zone A`, `Zone B`, `Zone C`, `Zone D`) comprising 193 physical sensor bays.

### ⚠️ Essential Modeling Principle
> **Stationary Physical Infrastructure:** Physical parking bays and civil infrastructure are geographically static civil assets. Parking spaces cannot be physically moved or transported across zones.
>
> Therefore, decision variables $x_i$ mathematically represent **managed parking permits, access passes, or admission quotas** issued by smart parking management authorities to regulate demand, alleviate severe bottlenecks, prevent overflow, and maximize social utility.

---

## 2. Mathematical Optimization Model

The system formulates the allocation challenge as a **Bounded Integer Knapsack Model**:

### Decision Variables
$$x_i \in \mathbb{Z}^+ \quad \forall i \in \{1, 2, 3, 4\} \quad (\text{Zone A, Zone B, Zone C, Zone D})$$
* $x_i$: Integer number of managed parking permits or admission quotas allocated to parking zone $i$.

### Parameters
* $C_i$: Stationary physical parking bay capacity of zone $i$ ($C_A=50, C_B=50, C_C=49, C_D=44$, Total: $C = 193$ bays).
* $d_i$: Estimated parking demand of zone $i$ derived via robust percentile estimators ($P_{95} \text{ Total} = 116$ permits).
* $w_i$: Priority weight for zone $i$, scaling dynamically with bottleneck congestion pressure ($w_i \in [1.0, 3.0]$).
* $B$: Total available managed permit allocation budget (Default: $B = 87$ permits at 75% P95 demand).
* $m_i$: Minimum required allocation quota per zone ($m_i \ge 0$, default 0).

### Objective Function
$$\text{Maximize } Z = \sum_{i=1}^{4} w_i \cdot x_i$$

### Subject to Constraints
1. **Permit Budget Constraint:**
   $$\sum_{i=1}^{4} x_i \le B$$
2. **Physical Bay Capacity Upper Bound:**
   $$x_i \le C_i \quad \forall i \in \{1, 2, 3, 4\}$$
3. **Estimated Demand Ceiling:**
   $$x_i \le d_i \quad \forall i \in \{1, 2, 3, 4\}$$
4. **Minimum Allocation Guarantee:**
   $$x_i \ge m_i \quad \forall i \in \{1, 2, 3, 4\}$$
5. **Non-negativity and Integrality:**
   $$x_i \in \{0, 1, 2, \dots\} \quad \forall i \in \{1, 2, 3, 4\}$$

---

## 3. Key Findings & Operations Research Proofs

* **Spatial Demand Heterogeneity:** Observed average utilization varies from **27.5%** (Zone A) to **31.3%** (Zone D), with peak single-event occupancy reaching **80.0%** in Zone D.
* **Smart Fleet & User Breakdown:** Registered commuters represent **73.2%** of parkers, standard passenger cars represent **70.4%**, motorcycles **19.1%**, and electric vehicles **10.5%**.
* **Algorithmic Dominance over Baseline:** Compared to heuristic proportional allocation under identical budgets ($B = 87$), PuLP ILP achieves:
  * **Higher weighted objective score ($Z^* = 249.52$ vs $247.01$, $+1.02\%$)**
  * Optimally targets high-pressure bottleneck zones while respecting integer bounds.
* **Exact Saturation Threshold ($B^*$):**
  $$\sum_{i=1}^{4} \min(C_i, d_i) = 116 \text{ permits}$$
  Sensitivity analysis mathematically proves that for any budget $B > 116$, the marginal gain is strictly:
  $$\frac{dZ}{dB} = 0.000$$

---

## 4. Application Architecture

```text
ITOR/
├── data/
│   ├── raw/                                # Original downloaded Kaggle dataset
│   │   └── IIoT_Smart_Parking_Management.csv # 1,000 records × 28 columns
│   ├── processed/                          # Standardized clean processed dataset
│   │   └── parking_sample_1500.csv         # 1,000 records × 33 columns
│   └── archive/                            # Archived legacy Birmingham dataset
│       ├── dataset.csv
│       └── parking_birmingham.csv
├── src/                                    # Core Operations Research & Analytics Engine
│   ├── data_loader.py                      # Data ingestion & schema standardization
│   ├── data_cleaning.py                    # Deduplication, integer occupancy & audit
│   ├── exploratory_analysis.py             # KPIs, fleet/user distributions & diurnal trends
│   ├── demand_estimation.py                # Mean, P85, P95, Max estimators
│   ├── constraints.py                      # Feasibility & budget binding managers
│   ├── baseline_allocation.py              # Proportional allocation heuristic
│   ├── optimization_model.py               # PuLP Integer Linear Programming solver
│   ├── model_validation.py                 # Mathematical validation suite & toy problem
│   ├── experiment_engine.py                # 36-scenario experiment grid
│   ├── sensitivity_analysis.py             # Budget sweeps & saturation proofs
│   ├── comparison_analysis.py              # Estimator & strategy comparisons
│   ├── scenario_analysis.py                # 5 canonical policy scenarios
│   └── visualization/                      # Visualization generators
│       ├── visualization_utils.py          # Color schemes & static/interactive exporters
│       ├── occupancy_charts.py             # Capacity, ranking, peak, availability
│       ├── temporal_charts.py              # Diurnal curves & 24h heatmaps
│       ├── optimization_charts.py          # Baseline vs LP, fulfillment, shifts
│       ├── sensitivity_charts.py           # Budget sweep, marginal gains, transitions
│       └── analytical_insights.py          # Automated markdown findings
├── dashboard/                              # Streamlit Full-Stack Application
│   ├── app.py                              # Main application entry point & 4-section router
│   ├── components/                         # Modular UI Components
│   │   ├── sidebar.py                      # Brand banner, academic badges, 4-step guide, status
│   │   ├── kpi_cards.py                    # Streamlit native responsive metric cards (zero HTML leaks)
│   │   ├── charts.py                       # Plotly responsive charts with dynamic auto-scaling
│   │   └── tables.py                       # Formatted tables with progress columns
│   ├── pages/                              # Rebuilt 4-Section Application Flow
│   │   ├── 1_Dashboard.py                  # Section 1: Dashboard (4 KPIs, zone demand, fleet mix, hourly)
│   │   ├── 2_Explore_Parking.py            # Section 2: Parking Facilities (zone search, 5 metrics, 2 charts)
│   │   ├── 3_Optimize_Allocation.py        # Section 3: Optimization (budget slider + presets, PuLP solver)
│   │   └── 4_Results_and_Reports.py        # Section 4: Results (summary table, baseline comparison, 5 scenarios, PDF)
│   └── utils/                              # Service Layer & Caching
│       ├── formatting.py                   # Responsive light theme CSS & number formatters
│       ├── state_manager.py                # Session state persistence across pages
│       ├── data_service.py                 # Cached data access layer
│       ├── optimization_service.py         # Solver orchestration service
│       └── report_service.py               # Multi-page ReportLab PDF compiler
├── outputs/                                # Verified Analytical CSVs & Figures
├── tests/                                  # 100% Comprehensive Unit Test Suite (116 tests passing)
│   ├── test_phase1_data.py                 # Phase 1 tests (9 passed)
│   ├── test_phase2_optimization.py         # Phase 2 tests (10 passed)
│   ├── test_phase3_experiments.py          # Phase 3 tests (13 passed)
│   ├── test_phase4_visualizations.py       # Phase 4 tests (11 passed)
│   ├── test_phase5_dashboard.py            # Phase 5 tests (19 passed)
│   ├── test_phase6_integration.py          # Phase 6 integration & edge cases (14 passed)
│   ├── test_end_to_end.py                  # Phase 6 12-stage sequential pipeline (1 passed)
│   ├── test_dashboard_validation.py        # Dashboard & chart verification (9 passed)
│   ├── test_ui_redesign.py                 # UI redesign architecture & charts (8 passed)
│   ├── test_html_rendering.py              # HTML integrity & dedenting verification (5 passed)
│   ├── test_ui_components.py               # Responsive dimensions & table formatting (5 passed)
│   ├── test_backend_functionality.py       # Data cleaning, deduplication & estimators (5 passed)
│   ├── test_optimization_consistency.py    # LP constraint satisfaction & scenario tests (3 passed)
│   └── test_full_application.py            # Workflow integration & PDF export tests (4 passed)
├── requirements.txt                        # Python dependencies
├── DATASET_MIGRATION_REPORT.md             # Dataset migration and audit report
├── DATASET_DESCRIPTION.md                  # Comprehensive schema and data dictionary
└── README.md                               # Project documentation
```

---

## 5. Technology Stack

* **Programming Language:** Python 3.11
* **Optimization Modeling & Solver:** PuLP 3.3.2 (COIN-OR CBC Solver)
* **Frontend Web Application:** Streamlit 1.50.0
* **Data Processing & Scientific Computing:** Pandas 3.0.2, NumPy, SciPy
* **Interactive Visualizations:** Plotly 7.1.0
* **Static Visualizations:** Matplotlib 3.10.8, Seaborn 0.13.2
* **Academic PDF Compilation:** ReportLab 4.4.10

---

## 6. Installation & Execution Guide

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone https://github.com/vibeshmourya/PARKOPT-Parking-Space-Allocation.git
cd ITOR

# Create and activate Python 3.11 virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run the Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501` to access **PARKOPT**.

### 3. Run the Complete Test Suite
```bash
python -m unittest discover tests
```
*Current test status: **116/116 unit and integration tests passing (100% test coverage)***.

---

## 7. Dashboard 4-Section Flow

| Section | Title | Core Functional Features |
|---|---|---|
| **1. Dashboard** | **Smart Parking System Overview** | High-level system KPIs, zone demand & utilization, vehicle mix donut chart, user category chart, 24h demand profile, key insights. |
| **2. Facilities** | **Smart Parking Zones Explorer** | Zone selection (`Zone A` through `Zone D`), 5 core metrics, progress-bar utilization indicator, capacity vs occupancy, diurnal trends, 2D heatmap. |
| **3. Optimize** | **Optimize Parking Allocation** | Preset budget buttons (Low: 60, Med: 87, High: 116), slider from 10 to 193 permits, demand estimator selection, priority strategy pill, PuLP solver execution. |
| **4. Results** | **Results & Academic Reports** | Recommended allocations vs proportional baseline, demand fulfillment chart, reallocation difference chart, 5-scenario evaluation, CSV export, academic PDF download. |

---

## 8. Academic Oral Defense (Viva) Reference Guide

* **Q: Why are physical spaces not relocated?**
  * *A:* Physical bays are static civil infrastructure. The model allocates *managed parking permits or admission quotas* across facility zones to regulate demand spatially without moving stationary concrete bays.
* **Q: What is the mathematical problem structure?**
  * *A:* A **Bounded Integer Knapsack Problem**, featuring capacity bounds $C_i$, demand ceilings $d_i$, integrality $x_i \in \mathbb{Z}^+$, and budget limit $B$.
* **Q: Why does marginal gain drop to zero at $B^* = 116$?**
  * *A:* $B^* = \sum \min(C_i, d_i) = 116$. Once every zone's demand or capacity is fully met, extra budget cannot be allocated without violating $x_i \le \min(C_i, d_i)$.
* **Q: How are priority weights calculated?**
  * *A:* $w_i = 1.0 + 2.0 \cdot \frac{u_i}{\max(u)} \in [1.0, 3.0]$, scaling strictly with historical congestion pressure, prioritizing bottleneck zones.

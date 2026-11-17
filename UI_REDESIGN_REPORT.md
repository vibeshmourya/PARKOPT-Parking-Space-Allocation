# PARKOPT — UI/UX Redesign Report
### Transforming Complex Operations Research into a Modern, Intuitive Application
**MCA ITOR Final Project:** *Optimal Parking Space Allocation Using Linear Programming*  
**Date:** November 2026  
**Status:** Completed & 100% Verified (93/93 Tests Passing)

---

## 1. Executive Summary & Redesign Rationale

### The Challenge of the Original Interface
Prior to this redesign, **PARKOPT** was structured as an exhaustive 6-page academic dashboard. While mathematically complete and verified, the interface presented several usability bottlenecks:
- **Information Overload:** Dense multi-column layouts presented up to 6 charts simultaneously on a single screen.
- **Academic Terminology Barrier:** Concepts were presented using heavy OR jargon (e.g., *bounded integer knapsack*, *shadow prices*, *objective function coefficients $w_i$*, *slack variables*), making the system inaccessible to first-time users or non-OR evaluators.
- **Fragmented Navigation:** 6 disparate pages forced users to jump between multiple tabs to perform a single optimization workflow.
- **Visual Clutter:** Dark gradients, high-contrast badges, and unformatted data tables dominated the user experience.

### The Redesign Mission
The complete UI/UX redesign simplifies and elevates the application into a **clean, modern, intuitive, and accessible product** while strictly preserving 100% of the underlying mathematical modeling, data integrity, and solver algorithms.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BEFORE (6-Page Academic Heavy)                        │
│  [1. Overview] → [2. Dataset] → [3. LP Model] → [4. Alloc] → [5. Scen] → [6. Rep]│
│  - Heavy OR jargon, 6-8 charts/page, dark gradients, dense multi-step UI    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Redesigned into
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   AFTER: PARKOPT Modern 4-Section Flow                      │
│                                                                             │
│  1. DASHBOARD           2. EXPLORE PARKING     3. OPTIMIZE ALLOCATION   4. RESULTS & REPORTS│
│  - 4 Key Metrics        - Search & Filter      - 3 Clean Controls       - Clear Summary Table│
│  - 2 Glance Charts      - Selected Lot Stats   - Quick Budget Presets   - 2 Focus Charts    │
│  - 3 Core Findings      - 2 Focus Charts       - One-Click Solve        - Plain Insights    │
│  - Action to Optimize   - Deep Expanders       - Mathematical Expander  - PDF & CSV Export  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 5 Core User Questions Answered

The redesigned application ensures that any evaluator or user can answer five critical operational questions immediately upon opening the system:

| Core Question | How the Redesigned UI Answers It | Location in App |
| :--- | :--- | :--- |
| **1. How many parking spaces are available?** | Displays verified **39,956 total bays** across 30 municipal lots, **20,447 peak vehicles**, and **51.2% peak utilization** via prominent KPI cards. | Section 1 (Dashboard) & Section 2 (Explore) |
| **2. Which parking facilities have high demand?** | "Top 5 High-Demand Facilities" chart and a 3-tier demand filter (High $\ge 65\%$, Moderate, Low) instantly highlight hotspot lots like Bull Ring and NIA South. | Section 1 (Dashboard) & Section 2 (Explore) |
| **3. Why is optimization required?** | Explains clearly that civil parking bays are stationary assets that cannot be moved, while demand is severely unbalanced (some lots overflow while others sit mostly empty). Managed permits must be optimized mathematically. | Section 1 ("Important Findings") & Section 3 |
| **4. What allocation does the system recommend?** | The PuLP LP solver computes the exact integer permit quota for each facility, displayed in a clean 4-column summary table and grouped charts. | Section 3 (Optimize) & Section 4 (Results) |
| **5. What is the difference between original and optimized results?** | Diverging reallocation bar chart and plain-language automated insights explain exactly which facilities gained permits, which lost permits, and why. | Section 4 (Results & Reports) |

---

## 3. Design System & Visual Language

### 3.1 Color Palette
The application adopts an accessible, high-contrast light theme:
- **Primary Accent (`#2563EB`):** Interactive elements, primary buttons, active tabs, and primary trend lines.
- **Success / Optimal (`#10B981`):** Optimal solver solutions, satisfied demand, and positive reallocation gains.
- **Warning / Moderate (`#F59E0B`):** Moderate demand thresholds and attention notices.
- **Alert / High Pressure (`#EF4444`):** Severe bottlenecks, deficit, or unmet demand (used sparingly).
- **Neutral Dark (`#0F172A` / `#1E293B`):** High-contrast typography and headings.
- **Neutral Light (`#FFFFFF` / `#F8FAFC` / `#E2E8F0`):** Clean backgrounds, cards, dividers, and progress track backgrounds.

### 3.2 Plain Language Glossary
All technical terminology has been translated into intuitive operational language, while formal mathematical notation is preserved in expandable containers:

| Technical / Academic Term | Plain Language Used in Redesign |
| :--- | :--- |
| Budget Constraint $B$ | **Available Parking Permits** |
| Peak Demand Estimator $d_{\max}$ | **Peak Vehicles Observed** |
| Weighted Objective Value $Z^*$ | **Optimization Priority Score** |
| System Unmet Demand $\sum (d_i - x_i)^+$ | **Estimated Demand Not Covered** |
| Priority Weights $w_i \in [1.0, 3.0]$ | **Allocation Priority Score** |
| Decision Variables $x_i \in \mathbb{Z}^+$ | **Recommended Facility Permit Allocation** |
| Physical Bay Capacity $C_i$ | **Stationary Physical Capacity (Fixed)** |

---

## 4. Page-by-Page Transformation

### Section 1: Dashboard (`1_Dashboard.py`)
- **Hero Banner:** *"Understand your parking. Optimize your allocation."*
- **4 Primary Metric Cards:**
  1. `Total Parking Spaces: 39,956 bays`
  2. `Peak Vehicles Observed: 20,447 cars`
  3. `Monitored Facilities: 30 sites`
  4. `Peak System Utilization: 51.2%`
- **Parking at a Glance (Only 2 Charts):**
  1. *Top 5 High-Demand Facilities:* Horizontal grouped bar comparing capacity and average occupancy.
  2. *Facility Count by Demand Tier:* Clear distribution of facilities into High ($\ge 65\%$), Moderate (40–65%), and Low (< 40%) demand tiers.
- **Important Findings:** Exactly 3 concise, data-backed bullet points explaining the demand imbalance, bottleneck overflows, and fixed infrastructure constraints.
- **Primary Action Button:** *"Start Optimizing"* routing directly to Section 3.
- **Collapsible Expander:** *"About this Project"* containing MCA ITOR academic notes, PuLP solver formulation, and Kaggle dataset provenance.

### Section 2: Explore Parking (`2_Explore_Parking.py`)
- **Search & Filter Controls:**
  - Dropdown selector to choose between "All Facilities" or any of the 30 specific Birmingham parking lots.
  - Demand level filter dropdown (All Tiers, High Demand, Moderate Demand, Low Demand).
- **Facility Detail Card (Selected Facility):**
  - Physical Capacity, Average Occupied Spaces, and Average Available Spaces.
  - Single-line visual utilization progress bar with explicit threshold markers (0% Empty, 40% Moderate, 65% High Pressure, 100% Full).
- **Only 2 Core Charts:**
  1. *Capacity vs. Occupancy:* Clean horizontal bar chart.
  2. *Hourly Parking Demand Pattern:* 24-hour diurnal curve showing traffic peaks.
- **Deep Exploration Expanders:**
  - *Advanced Analysis:* Diurnal profiles and 24-hour facility heatmap matrix.
  - *Data Quality & Cleaning Audit:* Complete audit of 216 deduplicated records and 9 sensor clipping corrections across 35,501 observations.
  - *View Full Dataset:* 30-facility interactive data table and CSV download button.

### Section 3: Optimize Allocation (`3_Optimize_Allocation.py`)
- **Streamlined Parameter Inputs (3 Primary Controls):**
  1. *Available Parking Permits (Budget):* Interactive slider with quick preset buttons for **Low (15,000)**, **Medium (21,617)**, and **High (28,000)** permits.
  2. *Demand Estimation Method:* Simple selector between **95th Percentile [Recommended]**, 85th Percentile, Average Occupancy, and Maximum Observed.
  3. *Allocation Priority Strategy:* Selector between **Congestion-based [Recommended]**, Equal Priority, and Custom Weights.
- **One-Click Action:** Prominent *"RUN OPTIMIZATION"* button that triggers the PuLP Integer Linear Programming solver.
- **Summary Result Cards:** Solver Status (`Optimal`), Total Allocated Permits, Unused Budget, Unmet Demand, and Optimization Priority Score ($Z^*$).
- **Success Banner:** *"Your recommended allocation is ready!"* with a direct action button to view detailed results in Section 4.
- **Mathematical Expander:** Complete LaTeX LP equations ($\max \sum w_i x_i$, $\sum x_i \le B$, $x_i \le C_i$, $x_i \le d_i$) for faculty inspection.

### Section 4: Results & Reports (`4_Results_and_Reports.py`)
- **Summary Results Table:** Clean 4-column table:
  $$\text{Parking Facility} \quad|\quad \text{Estimated Demand} \quad|\quad \text{Recommended Allocation} \quad|\quad \text{Unmet Demand}$$
- **Only 2 Core Analytical Charts:**
  1. *Demand vs. Recommended Allocation:* Stacked bar showing satisfied vs. unmet demand per facility.
  2. *Reallocation Shifts:* Diverging bar chart showing permit shifts from baseline ($\Delta = \text{LP} - \text{Baseline}$).
- **Automated Plain-Language Insights:**
  - Explains which facilities received more permits and why (high-congestion priority).
  - Explains which facilities received fewer permits and why (underutilized buffer released).
  - Identifies exactly where unmet demand remains (physical civil capacity bottlenecks).
- **Civil Infrastructure Distinction Note:** Clarifies that physical bays are stationary civil infrastructure, and the LP model reallocates administrative managed permits.
- **Primary Export Actions:**
  - *"Download Recommended Allocation (CSV)"*
  - *"Download Academic Project PDF Report"* (ReportLab compiled publication document).
- **Academic Expanders:**
  - *Compare Optimization Scenarios:* 5 canonical experiment comparisons.
  - *Viva Preparation Guide:* Curated OR interview questions and answers.

---

## 5. Component Upgrades & Architecture

### Sidebar Redesign
- Clean PARKOPT brand header with subtitle *"Smart Parking Allocation System"*.
- Academic badges: `MCA ITOR`, `PuLP LP`, `30 Facilities`.
- **4-Step User Guide:** Compact onboard checklist orienting first-time users.
- **System Status Card:** Live monitoring of monitored lots, total capacity, and solver state.
- **Stationary Assets Notice:** Clear notice on the non-relocatability of civil parking spaces.

### Table & Chart Simplification
- Strict limitation of **maximum 2 core charts per view**, eliminating clutter and visual fatigue.
- Custom Plotly layout template with clean whitespace, muted gridlines, and uncluttered tooltips.
- Streamlit native progress bars embedded directly inside dataframes for instant visual comprehension.

---

## 6. Verification, Testing & Quality Assurance

The redesign was subjected to automated unit and integration testing:

```text
======================================================================
TEST SUITE EXECUTION SUMMARY
======================================================================
test_phase1_data.py .........................  9 passed
test_phase2_optimization.py ................. 10 passed
test_phase3_experiments.py .................. 13 passed
test_phase4_visualizations.py ............... 11 passed
test_phase5_dashboard.py .................... 19 passed
test_phase6_integration.py .................. 13 passed
test_end_to_end.py ..........................  1 passed (12-stage pipeline)
test_dashboard_validation.py ................  9 passed
test_ui_redesign.py .........................  8 passed
----------------------------------------------------------------------
TOTAL TESTS: 93 PASSED IN 25.6s (100% SUCCESS RATE, 0 FAILURES)
======================================================================
```

### Verification Checks Completed:
1. **Mathematical Invariance:** Solver outputs, objective values ($Z^*$), and constraint checks remain identical to verified Phase 2 & 3 formulations.
2. **Dataset Integrity:** 35,501 cleaned observations across all 30 facilities preserved without fabrication.
3. **Backward Compatibility:** All legacy page callables (`render_overview_page`, `render_dataset_analysis_page`, etc.) aliased cleanly.
4. **Streamlit Multi-Page Routing:** Successfully verified multi-page initialization using `st.Page` and `st.navigation`.
5. **PDF & CSV Generation:** ReportLab academic report generation tested and verified.

---

## 7. Conclusion

The redesigned **PARKOPT** system successfully balances **extreme usability for first-time evaluators** with **rigorous mathematical depth for academic examination**. The intuitive 4-section flow allows anyone to understand the city-wide parking problem and run an optimization in under 60 seconds, while deep collapsible expanders provide full transparency into the Linear Programming mathematics.


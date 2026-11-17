# PARKOPT — Dataset Migration & Data Pipeline Modernization Report

**Project Title:** Optimal Parking Space Allocation Using Linear Programming (PARKOPT)  
**Academic Domain:** MCA ITOR (Introduction to Operations Research)  
**Date:** November 2026  
**Status:** Completed & Mathematically Verified (116/116 Tests Passing)

---

## 1. Executive Summary

This report documents the dataset replacement and data pipeline migration of **PARKOPT** from the legacy *Parking Birmingham Dataset* to the modern *Smart Parking Management Dataset (IIoT-enabled)* sourced from Kaggle.

The legacy dataset comprised 35,717 raw municipal records across 30 dispersed parking lots with simple aggregate occupancy counts and no vehicle or user classifications. The new dataset provides granular Internet-of-Things (IoT) sensor observations (ultrasonic, proximity, pressure) across 4 designated parking zones (`Zone A`, `Zone B`, `Zone C`, `Zone D`) encompassing 193 distinct physical bays, rich vehicle classes (*Car*, *Motorcycle*, *Electric Vehicle*), user categories (*Registered*, *Visitor*, *Staff*), and temporal dynamics across 24 operating hours.

All data loaders, cleaning pipelines, exploratory data analysis modules, demand estimators, linear programming models, scenario engines, sensitivity analyzers, dashboard pages, and test suites have been updated, validated, and verified.

---

## 2. Dataset Comparative Analysis

| Dimension | Legacy Dataset (Birmingham) | New Dataset (Smart Parking) |
| :--- | :--- | :--- |
| **Source** | Kaggle: Parking Birmingham | Kaggle: Smart Parking Management (`IIoT_Smart_Parking_Management.csv`) |
| **Raw Records** | 35,717 rows | 1,000 rows |
| **Cleaned Valid Records** | 35,501 rows | 1,000 rows |
| **Raw File Size** | 1.41 MB | 301 KB |
| **Missing Values** | 0 nulls | 0 nulls |
| **Duplicate Records** | 216 key duplicates | 0 duplicates (100% clean) |
| **Facilities / Zones** | 30 municipal parking lots | 4 Parking Zones (`Zone A`, `Zone B`, `Zone C`, `Zone D`) |
| **Physical Bay Capacity** | 39,956 bays | 193 physical bays ($C_A=50, C_B=50, C_C=49, C_D=44$) |
| **Individual Spot IDs** | Not available | 193 unique physical spot IDs (`Zone A_Spot01` .. `Zone D_Spot50`) |
| **Sensor Types** | Municipal induction loops | Ultrasonic, Proximity, Pressure |
| **Vehicle Types** | None (unclassified) | Car (70.4%), Motorcycle (19.1%), EV (10.5%) |
| **User Categories** | None (unclassified) | Registered (73.2%), Visitor (23.5%), Staff (3.3%) |
| **Spot Sizes** | Unspecified | Standard (71.2%), Compact (18.1%), Oversized (10.7%) |
| **Temporal Coverage** | Oct 2016 – Dec 2016 (07:00–16:00) | Jan 2021 – Jun 2024 (24 Hours: 00:00–23:00) |
| **Peak Demand ($d^{P95}$)** | 28,839 permits | 116 permits |
| **Standard Permit Budget** | 21,617 permits (75% of $d^{P95}$) | 87 permits (75% of $d^{P95}$) |

---

## 3. Dataset Target Size & Archival Methodology

### 3.1 Target Size & Row Count Policy
- **Target Size Directive:** Target 1,500–2,000 records; preferred target 1,800 records.
- **Strict Anti-Fabrication Rule:** *"If the source contains fewer than 1,500 valid records, do not fabricate additional rows. Report the actual available count."*
- **Actual Available Count:** The downloaded Kaggle file contains exactly **1,000 verified sensor records**.
- **Action Taken:** In strict adherence to academic research integrity, all 1,000 genuine records are preserved without synthetic row duplication or artificial event fabrication.
- **Output Storage:**
  - Original raw file preserved at: `data/raw/IIoT_Smart_Parking_Management.csv`
  - Cleaned, standardized processed dataset saved at: `data/processed/parking_sample_1500.csv` (1,000 rows × 33 columns).
  - SHA-256 Checksum: `460a7ae5e853697f3a660d64af3b94f6c2ddd012ccf89964b7558716a4c7fada`

### 3.2 Safe Archiving of Legacy Data
- Legacy Birmingham datasets (`parking_birmingham.csv` and root `dataset.csv`) were moved into `data/archive/`:
  - `data/archive/parking_birmingham.csv`
  - `data/archive/dataset.csv`
- No old Birmingham records, facility names, or statistics exist in active project pipelines.

---

## 4. Pipeline & Model Architecture Updates

### 4.1 Data Pipeline Modules (`src/`)
1. **`src/data_loader.py`:**
   - Prioritizes `data/processed/parking_sample_1500.csv`, with fallback to `data/raw/IIoT_Smart_Parking_Management.csv`.
   - Generates standardized compatibility fields (`SystemCodeNumber`, `Capacity`, `Occupancy`, `LastUpdated`, `Spot_Global_ID`).
   - Extracts comprehensive metadata covering the 4 zones, 193 bays, vehicle types, user categories, and IoT sensors.

2. **`src/data_cleaning.py`:**
   - Validates zero missing values, zero duplicates, and zero negative occupancies.
   - Computes integer bay occupancy: $\text{Occupancy} = \text{round}(\text{Occupancy\_Rate} \times \text{Capacity})$.
   - Computes `AvailableSpaces`, `OccupancyRate`, `EffectiveUtilization`, and decomposed datetime fields (`Date`, `Hour`, `DayOfWeek`, `IsWeekend`).

3. **`src/exploratory_analysis.py`:**
   - Computes system KPIs for 4 zones and 193 bays.
   - Computes zone statistics, 24-hour hourly demand profiles, and day-of-week trends.
   - Added `get_vehicle_type_distribution()` and `get_user_type_distribution()`.

4. **`src/demand_estimation.py`:**
   - Evaluates Mean, P85, P95, and Max demand across the 4 zones:
     - **Mean Demand:** 56 permits
     - **P85 Demand:** 89 permits
     - **P95 Demand:** 116 permits (Standard operational peak)
     - **Max Demand:** 145 permits (Extreme stress peak)
   - Capacity vs. P95 demand ratio: 60.1%.

### 4.2 Linear Programming Optimization Engine (`src/`)
- **Mathematical Formulation:**
  $$\text{Maximize } Z = \sum_{i \in \{A, B, C, D\}} w_i x_i$$
  Subject to:
  $$\sum_{i=1}^4 x_i \le B \quad (\text{Permit Budget Constraint})$$
  $$x_i \le C_i \quad \forall i \in \{A, B, C, D\} \quad (C_A=50, C_B=50, C_C=49, C_D=44)$$
  $$x_i \le d_i \quad \forall i \in \{A, B, C, D\}$$
  $$x_i \ge 0, \quad x_i \in \mathbb{Z} \quad \forall i \in \{A, B, C, D\}$$
- **Priority Scenarios:**
  - `equal`: $w_i = 1.0$ (raw permit maximization)
  - `congestion`: $w_i = 1.0 + 2.0 \cdot (u_i / \max(u)) \in [1.0, 3.0]$
  - `custom`: Policy weights: Zone A (2.5), Zone B (2.2), Zone C (1.8), Zone D (1.4).
- **Proportional Baseline Comparison:** Proportional Hamilton-Webster baseline algorithm with largest remainder apportionment.
- **Scenario Analysis:** 5 canonical scenarios updated with base budget $B = 87$ permits (~75% of P95 demand).
- **Budget Sensitivity:** Parametric sweep across 18 fractions ($B \in [0, 139]$) identifying the exact saturation threshold at $B^* = 116$ permits.

---

## 5. Streamlit Dashboard Modernization

1. **`dashboard/utils/data_service.py`:** Updated cache loaders for the processed Smart Parking dataset, vehicle/user distributions, and zone summaries.
2. **`dashboard/pages/1_Dashboard.py`:**
   - 4 primary KPI cards: Total Capacity (193 bays), Single Zone Peak (40 cars), Zones (4), Peak Utilization (80.0%).
   - Integrated new donut charts for Vehicle Mix (Car, Motorcycle, EV) and User Types (Registered, Visitor, Staff).
   - Zone demand distribution and 24-hour demand profile.
3. **`dashboard/pages/2_Explore_Parking.py`:**
   - Zone filter (`All Zones`, `Zone A`, `Zone B`, `Zone C`, `Zone D`).
   - 5 core metrics per zone with color-coded utilization progress indicators.
   - Diurnal curves and 2D occupancy heatmap.
4. **`dashboard/pages/3_Optimize_Allocation.py`:**
   - Permit budget presets calibrated for 193-capacity facility: Low (60), Medium (87), High (116).
   - Interactive slider from 10 to 193 permits.
   - PuLP integer knapsack solver with live KPI results.
5. **`dashboard/pages/4_Results_and_Reports.py`:**
   - Baseline vs. LP comparison tables and reallocation shift charts.
   - 5-scenario evaluation and budget sensitivity curves.
   - Export CSV and academic PDF report compilation.

---

## 6. Verification and Test Results

The entire unit, integration, UI, and mathematical test suite was updated and executed:

```
Ran 116 tests in 14.052s
OK
```

- **Data Pipeline Tests (9/9 passed):** Schema, 1,000 records, 4 zones, 193 capacity, zero duplicates, zero negative occupancies.
- **Optimization Model Tests (10/10 passed):** Analytical toy proof, monotonicity, constraint bounds, feasibility.
- **Experiment Engine Tests (13/13 passed):** 36-experiment matrix, budget saturation, priority shifts, edge cases.
- **Visualization Tests (11/11 passed):** Plotly chart generation, static figures, analytical insight metrics.
- **Dashboard Service Tests (19/19 passed):** Data caching, solver execution, PDF generation, Plotly layout validation.
- **Integration Tests (14/14 passed):** Mathematical soundness, SHA-256 stability, zero-budget, minimal unit budget, saturation.
- **UI & Regression Tests (40/40 passed):** Component dimensions, CSS sanitation, session state, navigation routing.

**Result: 100% Pass Rate across all 116 test cases.**


# Academic Exploratory Data Analysis Report: Birmingham Parking Dataset
**Subject:** MCA ITOR (Introduction to Operations Research)  
**Project:** Optimal Parking Space Allocation Using Linear Programming  
**Dataset:** Parking Birmingham (Kaggle)  
**Date:** November 2026  

---

## 1. Executive Summary

This report presents the Phase 1 Exploratory Data Analysis (EDA) of the **Parking Birmingham** dataset from Kaggle. The objective is to inspect the raw data, verify data hygiene, map operational variables to Operations Research (OR) constructs, and evaluate empirical parking demand patterns across municipal parking facilities in Birmingham, UK.

The primary finding is a **severe spatial asymmetry in parking utilization**: central shopping and hospital car parks regularly face 100%+ peak saturation and vehicle overflows, whereas large suburban and civic lots sit mostly idle with thousands of wasted parking spaces. This empirical reality provides strong justification for applying **Linear Programming (LP)** to optimize capacity allocation.

---

## 2. Dataset Identification and File Inspection

- **File Name:** `parking_birmingham.csv` (original: `dataset.csv`)
- **Location:** `data/parking_birmingham.csv`
- **File Size:** 1.41 MB (1,479,909 bytes)
- **Raw Record Count:** 35,717 rows × 4 columns
- **Temporal Span:** October 4, 2016 07:46:28 to December 19, 2016 16:30:35 (76 calendar days, 73 observation dates)
- **Observation Frequency:** Approximately every 30 minutes during daytime operating hours (07:00 – 16:30).

### Column Mapping and Data Types

| Original Column Name | Pandas Data Type | Operational Meaning | OR Model Role |
| :--- | :--- | :--- | :--- |
| `SystemCodeNumber` | `object` (string) | Unique identifier for each parking lot | Optimization index $i \in \{1, \dots, 30\}$ |
| `Capacity` | `int64` | Total designated bays for the parking lot | Existing baseline capacity $C_i$ |
| `Occupancy` | `int64` | Number of vehicles parked at timestamp | Historical demand sample $O_{i,t}$ |
| `LastUpdated` | `object` (datetime) | Observation timestamp | Temporal index $t$ |

> [!IMPORTANT]
> **Absence of User Categories:**  
> The raw Kaggle dataset **does NOT contain user classification fields** such as Faculty, Students, Staff, or Visitors. The allocation units for this Operations Research study are strictly **the 30 geographic parking facilities ($i = 1, \dots, 30$)** across the Birmingham municipal network.

---

## 3. Data Cleaning, Hygiene, and Anomaly Detection

| Check | Raw Count | Issue Description | Mitigation Strategy | Post-Clean Count |
| :--- | :--- | :--- | :--- | :--- |
| **Missing Values** | 0 | None. All 4 columns are 100% complete. | None required | 0 missing |
| **Exact Duplicates** | 216 | Duplicate sensor transmissions for identical lot & time | Deduplicated on `(SystemCodeNumber, LastUpdated)` | 0 duplicates (35,501 rows remain) |
| **Negative Occupancy** | 12 | Occupancy values of -1, -3, -8 in lot `NIA North` | Sensor zero-drift error; clipped to `0` | 0 negative values |
| **Occupancy > Capacity** | 373 | Vehicles parked exceed official capacity (e.g., 320 in 317 cap) | Real-world overflow / illegal aisle parking; retained for unconstrained demand estimation, capped at 100% for utilization | 373 tracked as overflow flags |
| **Capacity Consistency** | 30 / 30 | Fixed capacity per lot across all timestamps | Confirmed: 1 unique capacity per lot | 100% consistent |

---

## 4. System-Wide Aggregations & Key Metrics

- **Total Monitored Facilities:** 30 parking areas
- **Total System Capacity:** 39,956 spaces
- **Average Simultaneous System Occupancy:** 12,832.4 vehicles
- **Average System Utilization:** 32.12%
- **Peak System-Wide Simultaneous Occupancy:** 28,183 vehicles (70.54% system utilization on December 19, 2016 at 14:30:33)
- **Mean Single-Facility Observed Occupancy:** 644.9 spaces
- **Mean Single-Facility Available Spaces:** 754.5 spaces

---

## 5. Facility-Wise Utilization & Demand Profiling

The 30 parking areas exhibit drastic variations in utilization, categorized into three distinct operational demand tiers:

### Tier 1: High Demand / Saturated Facilities (Average Utilization $\ge$ 65%)
These car parks experience frequent saturation, vehicle rejections, and demand overflows:

| Parking Area (`SystemCodeNumber`) | Capacity ($C_i$) | Avg Occupancy | Peak Occupancy | Avg Utilization | Peak Utilization | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BHMBRTARC01` | 496 | 385.2 | 417 | 77.66% | 84.07% | High Pressure |
| `BHMBCCTHL01` | 387 | 289.1 | 403 | 74.70% | **104.13%** | Overcapacity |
| `BHMNCPNHS01` | 500 | 357.9 | 503 | 71.58% | **100.60%** | Overcapacity |
| `BHMNCPLDH01` | 720 | 506.8 | 723 | 70.39% | **100.42%** | Overcapacity |
| `BHMMBMMBX01` | 687 | 478.0 | 688 | 69.58% | **100.15%** | Overcapacity |
| `BHMBCCSNH01` | 863 | 573.5 | 869 | 66.46% | **100.70%** | Overcapacity |

### Tier 2: Moderate Demand Facilities (40% $\le$ Utilization < 65%)
Facilities operating at healthy capacity margins:
- `BHMNCPRAN01` (600 cap, 64.90% util)
- `BHMEURBRD01` (470 cap, 64.55% util)
- `BHMBRCBRG01` (1,010 cap, 64.39% util)
- `Broad Street` (690 cap, 63.39% util)
- `BHMEURBRD02` (220 cap, 62.24% util)
- `Others-CCCPS135a` (3,883 cap, 59.17% util)
- `BHMNCPNST01` (485 cap, 59.05% util)
- `Others-CCCPS105a` (2,009 cap, 56.76% util)
- `Shopping` (1,920 cap, 55.69% util)
- `Others-CCCPS8` (1,322 cap, 50.10% util)
- `Bull Ring` (3,053 cap, 47.84% util)
- `BHMBRCBRG02` (1,194 cap, 47.45% util)
- `Others-CCCPS133` (4,675 cap, 47.26% util)
- `BHMNCPHST01` (1,200 cap, 46.74% util)
- `BHMBCCPST01` (317 cap, 43.01% util)

### Tier 3: Low Demand / Underutilized Facilities (Utilization < 40%)
Large capacity reservoirs that remain significantly underutilized:

| Parking Area (`SystemCodeNumber`) | Capacity ($C_i$) | Avg Occupancy | Unused Capacity | Avg Utilization | Peak Utilization | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Others-CCCPS202` | 2,937 | 1,012.7 | 1,924.3 | 34.48% | 49.95% | Underutilized |
| `Others-CCCPS98` | 3,103 | 1,016.8 | 2,086.2 | 32.77% | 61.59% | Underutilized |
| `BHMBRCBRG03` | 849 | 244.3 | 604.7 | 28.78% | 74.56% | Low Demand |
| `BHMBCCMKT01` | 577 | 162.5 | 414.5 | 28.16% | 99.31% | Low Demand |
| `NIA South` | 788 | 197.0 | 591.0 | 25.00% | 88.32% | Low Demand |
| `BHMNCPPLS01` | 450 | 88.8 | 361.2 | 19.72% | 83.78% | Low Demand |
| `Others-CCCPS119a` | 2,803 | 541.6 | **2,261.4** | 19.32% | 54.73% | Severe Waste |
| `NIA Car Parks` | 1,268 | 207.9 | **1,060.1** | 16.40% | 66.80% | Severe Waste |
| `NIA North` | 480 | 36.2 | 443.8 | 7.53% | 31.46% | Extreme Waste |

---

## 6. Temporal Demand Variations

### Diurnal Pattern (Operating Hours: 07:00 – 16:30)
- **Morning Build-Up (07:00 – 09:00):** System occupancy ramps from an average of 266 vehicles (07:00) to 464 vehicles (09:00).
- **Core Business Peak (11:00 – 14:00):** Highest consistent demand is observed at 13:00 – 14:00, averaging over 800 vehicles per facility.
- **Afternoon Clearance (15:00 – 16:30):** Gradual decrease to 658 vehicles by 16:00.

### Weekly Distribution
- **Weekdays (Mon–Fri):** Consistently high activity, averaging ~640–660 vehicles per observation.
- **Weekends (Sat–Sun):** Slightly reduced overall commuter traffic, but heightened commercial shopping pressure around `Bull Ring` and `Shopping`.

---

## 7. Mathematical Formulation Insights for Phase 2

1. **Demand Estimation ($d_i$):**
   - Historical average occupancy ($\bar{O}_i$) represents regular baseline demand.
   - 85th/95th percentile or peak occupancy ($O_{i}^{max}$) represents stress/peak demand.
   - The existence of 373 overflow occurrences indicates that observed occupancy in saturated lots is *right-censored* (unmet demand cannot park once bays are full). Hence, $d_i$ for saturated lots should account for peak observed pressure.

2. **Reallocation Potential:**
   - In lots such as `Others-CCCPS119a` and `NIA Car Parks`, over 3,300 spaces sit idle on average.
   - In contrast, central lots like `BHMBCCTHL01` and `BHMNCPNHS01` spill over.
   - Linear Programming can reallocate zoned municipal capacity or dynamic access quotas to balance the load and maximize demand served subject to physical, operational, and minimum-service constraints.

---

## 8. Conclusion and Readiness for Phase 2

Phase 1 data inspection and exploratory data analysis are complete. All required fields have been mapped, data cleanliness is established, anomalies are documented with corrective protocols, and empirical demand distributions are computed.


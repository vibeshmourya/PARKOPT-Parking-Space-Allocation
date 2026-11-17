# Automated Analytical Insights Report
**Project:** Optimal Parking Space Allocation Using Linear Programming  
**Course:** MCA ITOR (Introduction to Operations Research)  
**Dataset:** Birmingham Municipal Parking (30 Facilities)  
**Generated Date:** November 2026  

---

## 1. Key Demand Extremes

### Top 5 High-Demand Bottleneck Facilities (Highest Historical Utilization)
These facilities experience continuous saturation and require maximum managed permit allocations:
1. **BHMBRTARC01**: Capacity = 496 bays | Avg Occupancy = 385.2 | **Utilization = 77.66%**
2. **BHMBCCTHL01**: Capacity = 387 bays | Avg Occupancy = 289.1 | **Utilization = 74.70%**
3. **BHMNCPNHS01**: Capacity = 500 bays | Avg Occupancy = 357.9 | **Utilization = 71.58%**
4. **BHMNCPLDH01**: Capacity = 720 bays | Avg Occupancy = 506.8 | **Utilization = 70.39%**
5. **BHMMBMMBX01**: Capacity = 687 bays | Avg Occupancy = 478.0 | **Utilization = 69.58%**

### Top 5 Underutilized Facilities (Chronic Capacity Reservoirs)
These large peripheral lots experience substantial bay vacancies and act as primary permit donors in LP reallocation:
1. **NIA South**: Capacity = 788 bays | Avg Occupancy = 197.0 | **Utilization = 25.00%**
2. **BHMNCPPLS01**: Capacity = 450 bays | Avg Occupancy = 88.8 | **Utilization = 19.72%**
3. **Others-CCCPS119a**: Capacity = 2,803 bays | Avg Occupancy = 541.6 | **Utilization = 19.32%**
4. **NIA Car Parks**: Capacity = 1,268 bays | Avg Occupancy = 207.9 | **Utilization = 16.40%**
5. **NIA North**: Capacity = 480 bays | Avg Occupancy = 36.2 | **Utilization = 7.53%**

---

## 2. Overflow & Capacity Saturation Analysis

A total of **8 facilities** exhibited real-world overflow events where observed occupancy exceeded nominal marked bay capacity:
- **BHMBCCTHL01**: Capacity = 387, Peak Occupancy = **403** (+16 bays overflow across 240 sensor recordings).
- **BHMBRCBRG01**: Capacity = 1010, Peak Occupancy = **1013** (+3 bays overflow across 86 sensor recordings).
- **BHMBRCBRG02**: Capacity = 1194, Peak Occupancy = **1198** (+4 bays overflow across 30 sensor recordings).
- **BHMBCCSNH01**: Capacity = 863, Peak Occupancy = **869** (+6 bays overflow across 11 sensor recordings).
- **BHMNCPNHS01**: Capacity = 500, Peak Occupancy = **503** (+3 bays overflow across 2 sensor recordings).
- **BHMBCCPST01**: Capacity = 317, Peak Occupancy = **320** (+3 bays overflow across 2 sensor recordings).
- **BHMMBMMBX01**: Capacity = 687, Peak Occupancy = **688** (+1 bays overflow across 1 sensor recordings).
- **BHMNCPLDH01**: Capacity = 720, Peak Occupancy = **723** (+3 bays overflow across 1 sensor recordings).

---

## 3. Spatiotemporal Demand Dynamics

- **Peak Operating Hours:** **14:00** is the peak single hour (average occupancy = 800.6 vehicles). The core peak window spans **11:00 AM to 2:00 PM**, averaging over 800 vehicles per active car park.
- **Busiest Day of the Week:** **Thursday** (Average occupancy = 696.8 vehicles). Weekday commuter traffic maintains a remarkably uniform profile Monday through Friday.
- **Quietest Day:** **Sunday** (Average occupancy = 497.6 vehicles).

---

## 4. Reallocation Impact (PuLP Optimization vs. Proportional Baseline)

Under a medium budget of 21,617 permits (75% of peak allocatable demand), the LP model strategically moves quotas from underutilized reservoirs to congested downtown facilities:

### Top Quota Gainers (Permits Added to Relieve Congestion):
- **Others-CCCPS133**: Baseline = 2,747 -> Optimized = **3,665** (**+918 permits**)
- **Others-CCCPS135a**: Baseline = 2,539 -> Optimized = **3,387** (**+848 permits**)
- **Bull Ring**: Baseline = 1,983 -> Optimized = **2,645** (**+662 permits**)

### Top Quota Donors (Permits Reclaimed from Underutilized Lots):
- **Others-CCCPS119a**: Baseline = 851 -> Optimized = **0** (**-851 permits**)
- **Others-CCCPS202**: Baseline = 1,032 -> Optimized = **0** (**-1,032 permits**)
- **Others-CCCPS98**: Baseline = 1,172 -> Optimized = **0** (**-1,172 permits**)

---

## 5. Methodological Insights: Estimators and Priority Formulations

1. **Demand Estimator Discrepancy:**
   - Historical Mean: **18,404 vehicles** (0 saturated lots).
   - 95th Percentile ($P_95$): **28,839 vehicles** (2 saturated lots).
   - Maximum Observed: **33,167 vehicles** (11 saturated lots).
   - *Operational Takeaway:* Historical mean occupancy is structurally inadequate for peak traffic management because it dilutes midday surges with early morning low occupancy.

2. **Priority Sensitivity:**
   - Under Equal Priority ($w_i = 1.0$), municipal objective equals raw permit volume ($Z = 21,617$).
   - Under Congestion Priority ($w_i \in [1.0, 3.0]$), municipal weighted objective reaches **$Z = 53,274.47$** (+7.44% gain), eliminating shortages in the 19 highest-demand car parks.

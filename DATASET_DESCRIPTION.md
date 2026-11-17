# Smart Parking Management Dataset — Technical Description & Data Dictionary

**Dataset Name:** Smart Parking Management Dataset (IIoT-enabled)  
**Dataset Source:** Kaggle (`IIoT_Smart_Parking_Management.csv`, URL: https://www.kaggle.com/dsv/9686139)  
**Application:** PARKOPT — Optimal Parking Space Allocation Using Linear Programming  
**Domain:** Master of Computer Applications (MCA) — Introduction to Operations Research (ITOR)  
**Processed File:** `data/processed/parking_sample_1500.csv` (1,000 records × 33 columns)

---

## 1. Overview and Architecture

The Smart Parking Management dataset captures simulated Industrial Internet-of-Things (IIoT) sensor feeds deployed across a structured municipal parking facility. The facility is organized into four geographic zones (`Zone A`, `Zone B`, `Zone C`, `Zone D`), each equipped with dedicated smart sensor nodes (ultrasonic, proximity, pressure) monitoring individual physical parking bays.

Unlike aggregate municipal count data, this dataset incorporates individual spot telemetry, vehicle physical characteristics, user demographics, environmental factors, dynamic pricing factors, and payment statuses, providing a multi-dimensional foundation for Operations Research modeling.

---

## 2. Facility Structure & Physical Capacity

The parking facility comprises **193 unique physical bays** across 4 designated sections:

| Zone / Section | Physical Spot IDs | Unique Bays ($C_i$) | Operational Character |
| :--- | :--- | :---: | :--- |
| **Zone A** | Spot 01 to Spot 50 | **50** | Central commercial hub, highest turnover, standard spots |
| **Zone B** | Spot 01 to Spot 50 | **50** | Commercial & business district parking |
| **Zone C** | Spot 01 to Spot 50 (excl. 40) | **49** | Commuter & transit access zone |
| **Zone D** | Spot 01 to Spot 50 (excl. 7, 21, 29, 33, 36, 44) | **44** | Long-term & peripheral parking, highest congestion pressure |
| **System Total** | — | **193** | Total stationary civil infrastructure bays |

Each bay is assigned a unique global identifier formatted as `{Zone}_{SpotID:02d}` (e.g., `Zone A_Spot01` through `Zone D_Spot50`).

---

## 3. Data Dictionary & Schema Specification

The dataset contains **33 total columns** (28 raw Kaggle columns + 5 standardized operational columns):

### 3.1 Primary Identification & Operational Fields
| Column Name | Data Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `SystemCodeNumber` | String | Standardized parking facility / zone identifier | `Zone A`, `Zone B`, `Zone C`, `Zone D` |
| `Parking_Lot_Section`| String | Section of the facility (raw Kaggle field) | `Zone A`, `Zone B`, `Zone C`, `Zone D` |
| `Parking_Spot_ID` | Integer | Local bay index within section | $1 \le \text{ID} \le 50$ |
| `Spot_Global_ID` | String | Globally unique bay identifier | e.g. `Zone A_Spot01` .. `Zone D_Spot50` |
| `Capacity` | Integer | Physical bay capacity of the section | 50 (A), 50 (B), 49 (C), 44 (D) |
| `Occupancy` | Integer | Estimated integer occupied bays at observation | $\text{round}(\text{Occupancy\_Rate} \times \text{Capacity})$ |
| `Occupancy_Cleaned` | Integer | Non-negative integer occupancy | $0 \le O \le C_i$ |
| `Occupancy_Rate` | Float | Instantaneous fractional occupancy rate | $[0.0079, 0.7927]$, Mean: $0.2837$ |
| `Occupancy_Status` | String | Discrete spot occupancy state | `Occupied` (55.0%), `Vacant` (45.0%) |
| `AvailableSpaces` | Integer | Buffer capacity remaining | $\max(0, C_i - \text{Occupancy})$ |
| `EffectiveUtilization`| Float | Capped utilization percentage | $[0.0\%, 100.0\%]$, Mean: $28.36\%$ |

### 3.2 Temporal & Environmental Telemetry
| Column Name | Data Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `Timestamp` | String / Datetime | Observation timestamp | `2021-01-01 00:00:00` to `2024-06-30 00:00:00` |
| `LastUpdated` | String | Compatibility alias for Timestamp | Formatted ISO datetime string |
| `Date` | Date | Calendar date of observation | 1,000 distinct observation dates |
| `Hour` | Integer | Operating hour of vehicle arrival | $0 \le \text{Hour} \le 23$ (24-hour cycle) |
| `Entry_Time` | Integer | Vehicle check-in hour | $0 \le \text{Entry} \le 23$ |
| `Exit_Time` | Integer | Vehicle check-out hour | $0 \le \text{Exit} \le 23$ |
| `Parking_Duration` | Integer | Dwell time duration (hours) | $[0, 9]$ hours, Mean: $2.87$ hours |
| `DayOfWeek` | String | Day name | Monday through Sunday |
| `IsWeekend` | Boolean | Weekend indicator flag | True for Saturday / Sunday |
| `Weather_Temperature` | Float | Ambient temperature (°C) | $[-4.7^\circ\text{C}, 34.8^\circ\text{C}]$, Mean: $15.1^\circ\text{C}$ |
| `Weather_Precipitation` | Integer | Binary rain/snow indicator | 0 (Dry), 1 (Precipitation) |
| `Environmental_Noise_Level` | Float | Ambient decibel level (dB) | $[40.1, 74.9]$ dB, Mean: $55.0$ dB |

### 3.3 Vehicle, User & Spot Attributes
| Column Name | Data Type | Description | Breakdown / Values |
| :--- | :--- | :--- | :--- |
| `Vehicle_Type` | String | Classification of arriving vehicle | Car (70.4%), Motorcycle (19.1%), EV (10.5%) |
| `Vehicle_Type_Weight` | Float | Vehicle curb weight (kg) | $[800.5, 2498.7]$ kg |
| `Vehicle_Type_Height` | Float | Vehicle height (meters) | $[1.20, 2.10]$ meters |
| `Electric_Vehicle` | Integer | Binary EV status flag | 0 (Combustion), 1 (Electric) |
| `User_Type` | String | Driver demographic membership | Registered (73.2%), Visitor (23.5%), Staff (3.3%) |
| `Spot_Size` | String | Dimension classification of bay | Standard (71.2%), Compact (18.1%), Oversized (10.7%) |
| `Proximity_To_Exit` | Float | Distance to nearest facility exit (m) | $[1.0, 15.0]$ meters |
| `User_Parking_History` | Float | Historical visit frequency score | $[1.0, 10.0]$ visits / month |

### 3.4 IIoT Sensor & Transactional Fields
| Column Name | Data Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `Sensor_Reading_Ultrasonic` | Float | Distance to vehicle chassis (cm) | $[10.0, 150.0]$ cm |
| `Sensor_Reading_Proximity` | Float | Optical infrared proximity signal | Continuous index $[0.5, 5.0]$ |
| `Sensor_Reading_Pressure` | Float | Piezoelectric road surface pressure | Continuous index $[0.8, 3.2]$ |
| `Nearby_Traffic_Level` | String | Exterior roadway congestion | `Low`, `Medium`, `High` |
| `Reserved_Status` | Integer | Advance reservation booking flag | 0 (No), 1 (Reserved) |
| `Dynamic_Pricing_Factor`| Float | Real-time congestion multiplier | $0.8\times, 1.0\times, 1.2\times, 1.5\times$ |
| `Payment_Amount` | Float | Collected parking fee (\$) | $[\$0.50, \$14.80]$, Mean: $\$3.85$ |
| `Payment_Status` | String | Transaction settlement state | `Paid`, `Unpaid`, `Pending` |
| `Parking_Violation` | Integer | Overtime or unauthorized parking | 0 (Compliant), 1 (Violation) |

---

## 4. Empirical Demand Modeling

Demand $d_i$ for each zone is derived empirically from the sensor occupancy series under four standard Operations Research estimators:

$$\begin{aligned}
d_i^{\text{mean}} &= \left\lfloor \frac{1}{T} \sum_{t=1}^T O_{i,t} + 0.5 \right\rfloor \\
d_i^{\text{P85}} &= \text{round}\left( \text{Percentile}_{85}(O_{i,t}) \right) \\
d_i^{\text{P95}} &= \text{round}\left( \text{Percentile}_{95}(O_{i,t}) \right) \quad (\text{Primary Academic Model}) \\
d_i^{\text{max}} &= \max_{t} O_{i,t} \quad (\text{Stress-Test Peak})
\end{aligned}$$

### Zone Demand Summary Table
| Zone | Capacity ($C_i$) | Mean Demand | P85 Demand | P95 Demand ($d_i$) | Max Demand | Historical Avg Util |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Zone A** | 50 | 14 | 22 | **29** | 35 | 27.51% |
| **Zone B** | 50 | 14 | 23 | **30** | 40 | 28.34% |
| **Zone C** | 49 | 14 | 23 | **30** | 35 | 28.34% |
| **Zone D** | 44 | 14 | 21 | **27** | 35 | 31.34% |
| **System Total** | **193** | **56** | **89** | **116** | **145** | **28.36%** |

---

## 5. Operations Research Linear Programming Formulation

The linear program determines the optimal managed permit allocation $x_i \in \mathbb{Z}^+$ to each zone $i \in \{\text{Zone A}, \text{Zone B}, \text{Zone C}, \text{Zone D}\}$ under a municipal permit budget $B$:

$$\text{Maximize } Z = \sum_{i \in \{A, B, C, D\}} w_i x_i$$

Subject to:
1. **Total Available Permit Budget:**
   $$\sum_{i=1}^4 x_i \le B$$
2. **Physical Civil Capacity Bound:**
   $$x_i \le C_i \quad \forall i \in \{A, B, C, D\} \quad (C_A=50, C_B=50, C_C=49, C_D=44)$$
3. **Estimated Demand Ceiling:**
   $$x_i \le d_i \quad \forall i \in \{A, B, C, D\}$$
4. **Integrality & Non-negativity:**
   $$x_i \ge 0, \quad x_i \in \mathbb{Z} \quad \forall i \in \{A, B, C, D\}$$

### Priority Weight Formulations ($w_i$)
- **Equal Priority:** $w_i = 1.0 \quad \forall i$ (Permit Volume Maximization).
- **Congestion Priority:** $w_i = 1.0 + 2.0 \cdot \frac{u_i}{\max(u)} \in [1.0, 3.0]$ where $u_i = \text{AvgUtilization}_i$. High-pressure bottleneck lots receive priority weight up to 3.0.
- **Custom Policy Strategy:** Zone A (2.5), Zone B (2.2), Zone C (1.8), Zone D (1.4).


# Freeze/Cold Wave Events - Experimental Design

**Event Category**: Extreme Cold/Freeze Events
**Model**: Aurora 0.25° Pretrained
**Focus**: Detection, onset timing, spatial characterization, physical mechanisms

**Last Updated**: November 17, 2025
**Status**: Active - Beast from East 2018 baseline complete, Stage 1 next

---

## Guiding Research Questions

### **Question 1 (Stage 1)**: Can Aurora predict freeze occurrence and when will it happen?
*"Can Aurora provide early warning of freeze events at operationally useful lead times?"*

**Focus**: Detection before onset (not just accuracy at peak)
- Binary detection: Will a freeze occur?
- Onset timing: When does freeze BEGIN (first T2m < 0°C)?
- Duration prediction: How many consecutive cold days?
- Predictability horizon: What is the practical early warning lead time?

### **Question 2 (Stage 2)**: How accurately does Aurora characterize freeze events?
*"When Aurora predicts a freeze, how well does it capture spatial extent, intensity, and physical mechanisms?"*

**Focus**: Detailed event characterization at useful lead times
- Spatial extent: Which regions affected and how accurately?
- Intensity: How cold and for how long?
- Physical mechanisms: Does Aurora capture the blocking patterns and jet stream configurations causing the freeze?
- Recovery prediction: When does warming begin?

---

## Event Selection

### Two Events: In-Sample vs Out-of-Sample

| Event | Dates | Region | Sample Status | Peak Impact |
|-------|-------|--------|---------------|-------------|
| **2018 Beast from the East** | Feb 22 - Mar 5, 2018 | British Isles/W. Europe | In-sample | -15°C anomalies, major disruption |
| **2021 Texas Freeze** | Feb 11-20, 2021 | Texas/Southern US | Out-of-sample | Power grid failure, 246 deaths |

**Rationale:**
- **Sample diversity**: 1 in-sample + 1 out-of-sample (tests temporal generalization)
- **Geographic diversity**: Europe vs North America
- **Mechanism diversity**: Arctic outbreak (Texas), European blocking (Beast)
- **Impact diversity**: Infrastructure failure (Texas), transportation disruption (Europe)
- **Professor feedback**: Focus on 2 freeze events to add heatwave category

**Analysis Priority**: Start with **Beast from East 2018** to develop methodology, then apply to Texas 2021.

**Note**: UK 2022 event removed per professor feedback to add heatwave category instead.

---

## Key Differences from Tropical Cyclone Framework

### Why Freeze Events Require Different Experimental Design

| Aspect | Tropical Cyclones | Freeze Events |
|--------|-------------------|---------------|
| **Duration** | 3-7 days (genesis → landfall) | 7-14 days (onset → peak → recovery) |
| **Spatial scale** | Point-based (landfall location) | Regional (100s-1000s km²) |
| **Target metric** | Single landfall time/location | Onset timing + spatial fields |
| **Predictability** | Track position (km) | Onset detection, temperature anomaly (°C) |
| **Physical process** | Convective system, intensification | Large-scale blocking, air mass advection |
| **Initialization sensitivity** | High (6h can matter) | Lower (synoptic-scale, slower evolution) |
| **Lead time range** | 1-7 days typical | 1-21 days (subseasonal skill possible) |

**Implication**: Two-stage approach but fundamentally different from TC:
- **Stage 1**: Detection & onset timing (answers "Will it freeze? When?")
- **Stage 2**: Spatial & physical characterization (answers "Where? How severe? Why?")
- **No initialization sensitivity testing** (synoptic scale, lower sensitivity than mesoscale TCs)

---

## Two-Stage Experimental Framework

### **Stage 1: Detection & Predictability Horizon**

**Research Question**: *"Can Aurora predict freeze occurrence, and what is the practical early warning lead time?"*

**Approach**: Variable initialization date targeting ONSET (first freeze day)

**Lead Times Tested**: **1, 7, 14, 21 days**
- **1 day**: Baseline (should be excellent)
- **7 days**: Standard medium-range operational horizon
- **14 days**: Subseasonal (high value for preparedness)
- **21 days**: Subseasonal-to-seasonal frontier

**Why 1, 7, 14, 21 instead of 1, 3, 5, 7?**
- Tests whether Aurora has skill beyond traditional NWP limits (~10 days)
- Operationally meaningful: Weekly intervals align with decision-making cycles
- Subseasonal skill (14-21 days) extremely valuable for infrastructure preparation

**Target**: ONSET day (first day regional T2m drops below threshold)

**Metrics** (Stage 1):
1. **Binary detection**: Does forecast predict regional T2m < 0°C threshold?
   - True positive, false negative, false alarm rates
2. **Onset timing error**: Hours difference in first freeze occurrence
3. **Duration prediction**: Consecutive days below threshold (forecast vs truth)
4. **Peak timing error**: When is coldest day predicted vs observed?

**Deliverable**: Identify practical predictability horizon for freeze detection

---

### **Stage 2: Spatial & Physical Characterization**

**Research Question**: *"When Aurora predicts a freeze at X-day lead time, how accurately does it characterize spatial extent, intensity, and physical mechanisms?"*

**Approach**:
- Use best/useful lead time from Stage 1 (e.g., 7-day if it has skill)
- Evaluate throughout event timeline: onset → peak → recovery
- Not just single snapshot!

**Evaluation Periods**:
1. **Onset** (first freeze day): Onset spatial pattern, cold air arrival
2. **Peak** (coldest day): Maximum intensity, spatial extent
3. **Recovery** (warming begins): Event duration, recovery timing

**Spatial Metrics**:
1. **Cold pool area**: km² below thresholds (0°C, -5°C, -10°C)
2. **Intersection over Union (IoU)**: Spatial overlap Aurora vs ERA5
3. **Pattern correlation**: Spatial structure of T2m field
4. **City-level accuracy**: Major cities correctly predicted below threshold?

**Intensity Metrics**:
1. **T2m RMSE**: Over affected region at onset/peak/recovery
2. **Temperature bias**: Systematic warm/cold bias (does Aurora dampen extremes?)
3. **Peak intensity error**: Minimum T2m difference at peak day
4. **Extreme cold capture**: Percentile analysis of temperature distribution

**Physical Mechanism Metrics** (KEY!):
1. **500 hPa blocking pattern**:
   - Position and persistence of blocking high (geopotential anomaly)
   - Blocking indices (omega block, Rex block patterns)
   - Aurora vs ERA5 Z500 field comparison

2. **Jet stream configuration**:
   - 250 hPa wind position (latitude of maximum wind)
   - Jet meandering amplitude
   - Rossby wave pattern reproduction

3. **Cold air mass tracking**:
   - 850 hPa temperature field (less surface noise than T2m)
   - Cold pool extent at 850 hPa
   - Vertical structure (850, 700, 500 hPa T profiles)
   - Temperature advection patterns

4. **Surface pressure patterns**:
   - MSL pressure anomalies
   - Arctic high position (Texas case)
   - Scandinavian high persistence (Beast from East)

**Duration Metrics**:
- Event start/end timing
- Number of consecutive cold days
- Recovery timing (warming onset)

**Deliverable**:
- Comprehensive characterization of Aurora's freeze prediction capabilities
- Identification of strengths (e.g., blocking patterns) vs weaknesses (e.g., extreme intensity)
- Physical process validation (does Aurora capture mechanisms correctly?)

---

## Variables Required for Analysis

### **⚠️ CRITICAL: Aurora Pressure Level Indexing**

**Aurora pressure levels are in REVERSE order:**
```
(1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50) hPa
Index:  0     1     2     3     4     5     6     7     8     9    10    11    12
```

**Correct indices for atmospheric variables:**
- **850 hPa**: `level_idx=2` (NOT 10!)
- **700 hPa**: `level_idx=3` (NOT 8!)
- **500 hPa**: `level_idx=5` (NOT 6!)
- **250 hPa**: `level_idx=8` (NOT 3!)

**Bug discovered Nov 20, 2024**: Beast from East initially extracted wrong pressure levels, causing visualization issues (T850 showed stratosphere, Z500 showed 400 hPa). Fixed in all scripts.

---

### **Essential Variables** (Stage 1 & 2):
- **2m temperature (t2m)**: Primary freeze indicator, intensity, spatial extent
- **850 hPa temperature** (`level_idx=2`): Cold air mass position/intensity (less surface noise)
- **500 hPa geopotential (z)** (`level_idx=5`): Blocking pattern identification
- **Mean sea level pressure (msl)**: Surface pressure patterns (blocking signature)

### **Important Variables** (Stage 2 characterization):
- **250 hPa u/v winds** (`level_idx=8`): Jet stream position, meandering, Rossby waves
- **850 hPa u/v winds** (`level_idx=2`): Low-level cold air advection
- **700 hPa temperature** (`level_idx=3`): Mid-troposphere cold pool
- **10m u/v winds**: Surface wind (for wind chill calculation)

### **Derived/Composite Variables**:
- **Wind chill** (Texas-specific): Combined T2m + 10m wind (human impact, power demand)
- **Temperature anomalies**: Forecast vs climatology (how unusual?)
- **Geopotential height anomalies**: Identify blocking vs climatology
- **Blocking indices**: Omega block, Rex block patterns

---

### **Data Range Verification Workflow** (Added Nov 20, 2024)

**After running baseline predictions, verify data ranges before finalizing visualizations:**

1. **Extract regional data ranges** for each variable from cached predictions
2. **Compare with expected ranges** (climatology, ERA5 verification)
3. **Set appropriate plotting scales** based on actual event characteristics
4. **Document ranges** for reproducibility

**Example (Beast from East 2018):**

| Variable | Expected Range | Aurora Regional | Plotting Scale | Notes |
|----------|---------------|----------------|----------------|-------|
| T2m | Varies by event | -30 to 15°C | -30 to 15°C | Good contrast |
| T850 | ~-20 to 10°C | -20 to 10°C | -20 to 10°C | Tropospheric range |
| Z500 | ~5000-5800 m | Auto-scale | Auto-scale | Blocking patterns |
| MSL | 960-1055 hPa | 960-1055 hPa | Auto-scale | Pressure systems |

**Why this matters:**
- Wrong pressure levels → wrong data ranges → misleading visualizations
- Auto-scale can hide spatial dynamics if range too wide
- Event-specific scales highlight important features

---

## Event-Specific Configurations

### Event 1: Beast from the East (Feb 22 - Mar 5, 2018)

**Status**: **PRIMARY EVENT - Starting analysis here**

**Regional Domain**:
- Latitude: 45°N - 62°N
- Longitude: -12°W - 10°E (or 348°E - 10°E in 0-360° format)
- Covers: UK, Ireland, France, Netherlands, Belgium

**Event Timeline**:
- **Blocking formation**: ~Feb 20-21 (Scandinavian High develops)
- **Easterly flow onset**: Feb 22-23
- **Onset**: **Feb 24, 2018** (Cold air ARRIVES, T2m < 0°C in affected regions)
- **Peak**: **Mar 1, 2018** (Coldest day, maximum spatial extent)
- **Recovery**: Mar 4-5, 2018

**Physical Mechanism**:
- Persistent Scandinavian High at 500 hPa
- Easterly flow bringing Siberian air mass
- Amplified Rossby wave pattern
- Snow-albedo feedback amplifying cold

**Stage 1 Lead Time Configurations** (targeting ONSET: Feb 24):
| Lead Time | Init Date | Init Hour | Target (Onset Day) | Steps to Feb 24 |
|-----------|-----------|-----------|-------------------|-----------------|
| **1-day** | Feb 23, 12 UTC | 12 | Feb 24 onset | 3 (18h) |
| **7-day** | Feb 17, 12 UTC | 12 | Feb 24 onset | 27 (162h) |
| **14-day** | Feb 10, 12 UTC | 12 | Feb 24 onset | 55 (330h) |
| **21-day** | Feb 3, 12 UTC | 12 | Feb 24 onset | 83 (498h) |

**Note**: Forecasts continue through peak (Mar 1) and recovery (Mar 4-5) for full event assessment

**Data Download Range**: **Feb 3 - Mar 2, 2018** (28 days continuous)
- Covers all initialization times (Feb 3, 10, 17, 23)
- Full verification period (onset Feb 24 → peak Mar 1 → recovery Mar 4-5)
- Enables onset/peak/recovery analysis for all lead times

**Freeze Thresholds**: 0°C, -5°C, -10°C (regional T2m)

**Key Scientific Questions**:
- Can Aurora detect freeze occurrence 21 days in advance?
- At what lead time does onset timing skill degrade below operational usefulness?
- Does Aurora capture the Scandinavian blocking pattern at subseasonal leads?

---

### Event 2: 2021 Texas Freeze (Feb 11-20, 2021)

**Regional Domain**:
- Latitude: 25°N - 37°N
- Longitude: -107°W - -93°W (253°E - 267°E)
- Covers: Texas, Oklahoma, Louisiana, Arkansas

**Target Periods**:
- **Onset**: Feb 14, 2021 (Arctic front arrival)
- **Peak**: Feb 15-16, 2021 (statewide power failure)
- **Recovery**: Feb 19-20, 2021

**Lead Time Configurations**:
| Lead Time | Init Date | Init Hour | Target (Peak Day) | Steps |
|-----------|-----------|-----------|-------------------|-------|
| 1-day | Feb 14 12:00 UTC | 12 | Feb 16 12:00 UTC | 7 |
| 3-day | Feb 12 12:00 UTC | 12 | Feb 16 12:00 UTC | 15 |
| 5-day | Feb 10 12:00 UTC | 12 | Feb 16 12:00 UTC | 23 |
| 7-day | Feb 08 12:00 UTC | 12 | Feb 16 12:00 UTC | 31 |
| 10-day | Feb 05 12:00 UTC | 12 | Feb 16 12:00 UTC | 43 |

**Thresholds**: 0°C (-18°F), -5°C (23°F), -10°C (14°F)

**Key Challenge**:
- Unusual southward Arctic air penetration
- Wind chill critical (combines temperature + wind)
- Infrastructure impact (not designed for sustained cold)
- Out-of-sample test (2021)

---


## Visualization Strategy

### Per-Event Outputs

**1. Temperature Evolution Maps** (4-6 panels):
- ERA5 truth vs Aurora forecast at peak day
- For each lead time: 1, 3, 5, 7, 10 days
- Show T2m field with 0°C, -5°C, -10°C contours

**2. Time Series at Key Cities**:
- Major population centers (London, Dallas, Dublin, etc.)
- ERA5 vs Aurora temperature evolution
- Shaded regions for different lead times
- Shows onset timing accuracy

**3. Lead Time Skill Degradation**:
- RMSE vs lead time (1, 3, 5, 7, 10 days)
- Temperature bias vs lead time
- Onset timing error vs lead time

**4. Spatial Extent Comparison**:
- Area below threshold (0°C, -5°C, -10°C)
- Aurora vs ERA5 for each lead time
- IoU metric visualization

**5. Error Maps**:
- Spatial distribution of temperature errors
- At peak day
- For 3-day and 7-day leads (most operationally relevant)

### Cross-Event Comparison

**6. Unified Skill Assessment**:
- RMSE vs lead time for both events
- Shows in-sample (Beast 2018) vs out-of-sample (Texas 2021)
- Identifies if Aurora degrades for out-of-sample cold events

---

## Data Requirements

### ERA5 Variables Needed

**Surface-level** (single-levels):
- `2t`: 2-meter temperature (primary freeze indicator)
- `10u`, `10v`: 10-meter winds (for wind chill, surface circulation)
- `msl`: Mean sea level pressure (surface blocking patterns)

**Atmospheric** (pressure-levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `t`: Temperature (all levels for vertical structure, especially 850, 700, 500 hPa)
- `u`, `v`: Wind components (jet stream at 250 hPa, advection at 850 hPa)
- `z`: Geopotential (blocking patterns at 500 hPa)
- `q`: Specific humidity (required by Aurora)

**Static** (provided with Aurora checkpoints):
- `z`: Geopotential (topography)
- `lsm`: Land-sea mask
- `slt`: Soil type

**Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)

### Download Strategy (Following TC Pattern)

**Beast from East 2018**:
- **Download range**: Feb 3 - Mar 2, 2018 (28 days continuous, ~112 timesteps)
- **Actual usage**: 4 init timesteps (Feb 3, 10, 17, 23 at 12 UTC) + continuous verification (Feb 22 - Mar 2)
- **Efficiency**: ~36% utilization, but simpler scripts and more flexible for debugging
- **Individual files**: One file per date (surface + atmospheric)
  - `2018-02-03-surface-level.nc`, `2018-02-03-atmospheric.nc`
  - ...
  - `2018-03-02-surface-level.nc`, `2018-03-02-atmospheric.nc`
- **Combined files**: Concatenated into continuous timeseries
  - `beast_2018_surface_feb03-mar02.nc`
  - `beast_2018_atmospheric_feb03-mar02.nc`

**Texas 2021** (future):
- Download range: Jan 26 - Feb 21, 2021 (27 days)

**UK 2022** (future):
- Download range: Nov 21 - Dec 19, 2022 (29 days)

---

## Success Criteria

### Temperature Prediction

**Excellent Performance**:
- 1-day lead: RMSE < 2°C
- 3-day lead: RMSE < 3°C
- 5-day lead: RMSE < 4°C
- 7-day lead: RMSE < 5°C
- 10-day lead: RMSE < 6°C

**Minimum Acceptable**:
- 1-day lead: RMSE < 3°C
- 3-day lead: RMSE < 5°C
- 5-day lead: RMSE < 7°C
- 7-day lead: RMSE < 9°C
- 10-day lead: RMSE < 10°C

### Onset Timing

**Excellent**: Onset timing within ±6 hours at 7-day lead
**Acceptable**: Onset timing within ±12 hours at 7-day lead

### Spatial Extent

**Excellent**: IoU > 0.7 at 3-day lead
**Acceptable**: IoU > 0.5 at 3-day lead

---

## Why No Stage 2 (Initialization Sensitivity)?

**Decision: Skip initialization time sensitivity testing for freeze events**

**Rationale:**
1. **Synoptic scale**: Freeze events are driven by large-scale patterns (100s-1000s km)
2. **Slow evolution**: Temperature changes occur over days, not hours
3. **Lower sensitivity**: Unlike TCs (mesoscale, 6h init matters), 6-12h difference in freeze init is negligible
4. **Resource allocation**: Focus computational resources on more lead times (extend to 10 days) rather than init time tests
5. **Literature support**: NWP studies show initialization time is less critical for synoptic cold events vs mesoscale phenomena

**Trade-off**: We test 5 lead times (1, 3, 5, 7, 10 days) instead of 4 TC lead times + 4 init times

---

## Expected Aurora Challenges

### Challenge 1: Temperature Bias in Extreme Cold
- ML models often underpredict temperature extremes (regression to the mean)
- Aurora may predict too warm during coldest periods
- Critical for infrastructure planning (power demand, road safety)

### Challenge 2: Blocking Pattern Persistence
- Beast from the East required persistent Scandinavian High
- Aurora's ability to maintain blocking patterns beyond 5-7 days uncertain
- 10-day lead will test this directly

### Challenge 3: Onset Timing
- Small errors in cold front timing → large impact
- Texas: 12h delay in onset = different power failure scenario
- Tests Aurora's synoptic feature propagation skill

### Challenge 4: Out-of-Sample Degradation
- Beast (2018, in-sample) vs Texas/UK (2021-2022, out-of-sample)
- Expected: Better performance for Beast than Texas/UK
- Tests temporal generalization

### Challenge 5: Regional Topography
- Texas: Varied terrain (plains, hills, coast)
- UK: Complex coastline, varied elevation
- Aurora's 0.25° resolution may smooth out local cold pools

---

## Research Significance

### Novel Contributions

1. **First Aurora freeze/cold wave assessment**: No published studies on Aurora's cold event skill
2. **Multi-day event evaluation**: Beyond single-day forecasts, tests event duration
3. **In-sample vs out-of-sample**: Direct comparison at event level
4. **Extended lead times**: 10-day forecasts rare in extreme event literature
5. **Infrastructure relevance**: Texas case directly relevant to power grid resilience

### Paper Narrative

Freeze events contrast with TCs:
- **TCs**: Mesoscale, rapid evolution, short duration → Aurora excels? struggles?
- **Freezes**: Synoptic-scale, slow evolution, long duration → Aurora excels? struggles?

Results will reveal Aurora's **scale-dependent predictability**.

---

## Next Steps

1. ✅ Create experimental design document
2. ⬜ Create Freeze event folders (2018_BeastFromEast, 2021_TexasFreeze, 2022_UKColdWave)
3. ⬜ Download ERA5 data for all three events
4. ⬜ Create analysis scripts (beast_lead_day.py, texas_lead_day.py, uk_lead_day.py)
5. ⬜ Run forecasts (5 lead times × 3 events = 15 runs)
6. ⬜ Analyze results
7. ⬜ Document findings (FREEZE_RESULTS.md)
8. ⬜ Update master research plan

---

**Notes**:
- **No Stage 2**: Skip initialization sensitivity (synoptic scale, slower evolution)
- **Extended lead times**: Test up to 10 days (operational relevance)
- **Multiple targets**: Onset, peak, recovery (not just single time like TC landfall)
- **Temperature focus**: Primary metric is T2m RMSE/bias, not position error
- **Infrastructure context**: Frame results for operational decision-making (power grid, transportation)

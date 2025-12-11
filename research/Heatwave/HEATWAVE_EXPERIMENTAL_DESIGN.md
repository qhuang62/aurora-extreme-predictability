# Heatwave Events - Experimental Design

**Event Category**: Extreme Heat/Heatwave Events
**Model**: Aurora 0.25° Pretrained
**Focus**: Detection, onset timing, spatial characterization, physical mechanisms

**Last Updated**: November 23, 2025
**Status**: Active - Setting up experimental framework

---

## Guiding Research Questions

### **Question 1 (Stage 1)**: Can Aurora predict heatwave occurrence and when will it happen?
*"Can Aurora provide early warning of heatwave events at operationally useful lead times?"*

**Focus**: Detection before onset (not just accuracy at peak)
- Binary detection: Will a heatwave occur?
- Onset timing: When does heat BEGIN (first T2m > 30°C)?
- Duration prediction: How many consecutive hot days?
- Predictability horizon: What is the practical early warning lead time?

### **Question 2 (Stage 2)**: How accurately does Aurora characterize heatwave events?
*"When Aurora predicts a heatwave, how well does it capture spatial extent, intensity, and physical mechanisms?"*

**Focus**: Detailed event characterization at useful lead times
- Spatial extent: Which regions affected and how accurately?
- Intensity: How hot and for how long?
- Physical mechanisms: Does Aurora capture the blocking patterns and heat dome causing the event?
- Recovery prediction: When does cooling begin?

---

## Event Selection

### Event: August 2023 Southwest Europe Heatwave

| Event | Dates | Region | Sample Status | Peak Impact |
|-------|-------|--------|---------------|-------------|
| **2023 SW Europe Heatwave** | Aug 9-26, 2023 | France, N. Spain, Switzerland | Out-of-sample | 41.4°C Lyon, 44.0°C Bilbao, 17-day sustained heat |

**Rationale:**
- **Out-of-sample**: August 2023 is well beyond Aurora's training period (1979-2020)
- **High impact**: Record-breaking temperatures, sustained multi-week heatwave
- **Well-defined timeline**: Clear onset, peak, and recovery phases
- **Mechanism diversity**: Heat dome/blocking high (opposite of freeze but similar scale)
- **Operational relevance**: Heat health warnings, power grid stress, wildfire risk
- **Complements freeze**: Tests Aurora on both cold and heat temperature extremes

---

## Key Differences from Freeze Events

### Why Heatwaves Require Inverted Logic but Similar Framework

| Aspect | Freeze Events | Heatwave Events |
|--------|---------------|-----------------|
| **Duration** | 7-14 days (onset → peak → recovery) | 7-21 days (onset → peak → recovery) |
| **Spatial scale** | Regional (100s-1000s km²) | Regional (100s-1000s km²) |
| **Target metric** | Onset timing + spatial fields | Onset timing + spatial fields |
| **Predictability** | Onset detection, T anomaly (°C) | Onset detection, T anomaly (°C) |
| **Physical process** | Arctic air mass, blocking high | Mediterranean heat, subtropical high |
| **Thresholds** | < 0°C, < -5°C, < -10°C | > 30°C, > 35°C, > 40°C |
| **Detection logic** | `field < threshold` | `field > threshold` |
| **Peak detection** | `np.argmin()` (coldest) | `np.argmax()` (hottest) |
| **Lead time range** | 1-21 days | 1-21 days |

**Implication**: Same two-stage approach with **inverted temperature logic**:
- **Stage 1**: Detection & onset timing (answers "Will it be hot? When?")
- **Stage 2**: Spatial & physical characterization (answers "Where? How severe? Why?")

---

## Two-Stage Experimental Framework

### **Stage 1: Detection & Predictability Horizon**

**Research Question**: *"Can Aurora predict heatwave occurrence, and what is the practical early warning lead time?"*

**Approach**: Variable initialization date targeting ONSET (first heat day)

**Lead Times Tested**: **1, 7, 14, 21 days**
- **1 day**: Baseline (should be excellent)
- **7 days**: Standard medium-range operational horizon
- **14 days**: Subseasonal (high value for preparedness)
- **21 days**: Subseasonal-to-seasonal frontier

**Target**: ONSET day (Aug 9, 2023 - first day regional T2m > 30°C)

**Metrics** (Stage 1):
1. **Binary detection**: Does forecast predict regional T2m > 30°C threshold?
   - True positive, false negative, false alarm rates
2. **Onset timing error**: Hours difference in first heat occurrence
3. **Duration prediction**: Consecutive days above threshold (forecast vs truth)
4. **Peak timing error**: When is hottest day predicted vs observed?

**Deliverable**: Identify practical predictability horizon for heatwave detection

---

### **Stage 2: Spatial & Physical Characterization**

**Research Question**: *"When Aurora predicts a heatwave at X-day lead time, how accurately does it characterize spatial extent, intensity, and physical mechanisms?"*

**Approach**:
- Use best/useful lead time from Stage 1 (e.g., 7-day if it has skill)
- Evaluate throughout event timeline: onset → peak → recovery

**Evaluation Periods**:
1. **Onset** (Aug 9): Onset spatial pattern, warm air arrival
2. **Peak** (Aug 23-24): Maximum intensity, spatial extent
3. **Recovery** (Aug 26): Event duration, recovery timing

**Spatial Metrics**:
1. **Heat area**: km² above thresholds (30°C, 35°C, 40°C)
2. **Intersection over Union (IoU)**: Spatial overlap Aurora vs ERA5
3. **Pattern correlation**: Spatial structure of T2m field
4. **City-level accuracy**: Major cities correctly predicted above threshold?

**Intensity Metrics**:
1. **T2m RMSE**: Over affected region at onset/peak/recovery
2. **Temperature bias**: Systematic warm/cold bias (does Aurora dampen extremes?)
3. **Peak intensity error**: Maximum T2m difference at peak day
4. **Extreme heat capture**: Percentile analysis of temperature distribution

**Physical Mechanism Metrics** (KEY!):
1. **500 hPa blocking pattern**:
   - Position and persistence of heat dome (geopotential anomaly)
   - Blocking indices (omega block, Rex block patterns)
   - Aurora vs ERA5 Z500 field comparison

2. **Jet stream configuration**:
   - 250 hPa wind position (latitude of maximum wind)
   - Subtropical vs polar jet separation
   - Rossby wave pattern reproduction

3. **Warm air mass tracking**:
   - 850 hPa temperature field (less surface noise than T2m)
   - Heat pool extent at 850 hPa
   - Vertical structure (850, 700, 500 hPa T profiles)
   - Temperature advection patterns (southerly flow)

4. **Surface pressure patterns**:
   - MSL pressure anomalies
   - Subtropical high position and strength
   - Heat dome persistence

**Duration Metrics**:
- Event start/end timing
- Number of consecutive hot days
- Recovery timing (cooling onset)

**Deliverable**:
- Comprehensive characterization of Aurora's heatwave prediction capabilities
- Identification of strengths (e.g., blocking patterns) vs weaknesses (e.g., extreme intensity)
- Physical process validation (does Aurora capture mechanisms correctly?)

---

## Event-Specific Configuration

### Event: August 2023 Southwest Europe Heatwave

**Regional Domain**:
- Latitude: 42°N - 48°N
- Longitude: -2°W - 8°E (-2°E - 8°E, or 358°E - 8°E in 0-360°)
- Covers: France (Lyon, Toulouse, Bordeaux), N. Spain (Bilbao), Switzerland (Geneva)

**Event Timeline** (Based on ECMWF analysis and temperature records):
- **Heat build-up**: ~Aug 7-8 (Subtropical high strengthens)
- **Onset**: **Aug 9, 2023** (Warm air ARRIVES, T2m > 30°C in affected regions)
- **Peak**: **Aug 23-24, 2023** (Hottest days: Lyon 41.4°C, Bilbao 44.0°C)
- **Recovery**: Aug 26, 2023 (Regional mean drops below 30°C)

**Physical Mechanism**:
- Persistent subtropical high at 500 hPa (heat dome)
- Southerly flow bringing Mediterranean/Saharan air
- Amplified Rossby wave pattern
- Suppressed precipitation reinforcing heating

**Stage 1 Lead Time Configurations** (targeting ONSET: Aug 9):

| Lead Time | Init Date | Init Hour | Target (Onset Day) | Forecast Days | Steps |
|-----------|-----------|-----------|-------------------|---------------|-------|
| **1-day** | Aug 8, 12 UTC | 12 | Aug 9 onset | 18 days | 71 (to Aug 26) |
| **7-day** | Aug 2, 12 UTC | 12 | Aug 9 onset | 24 days | 95 (to Aug 26) |
| **14-day** | Jul 26, 12 UTC | 12 | Aug 9 onset | 31 days | 123 (to Aug 26) |
| **21-day** | Jul 19, 12 UTC | 12 | Aug 9 onset | 38 days | 151 (to Aug 26) |

**Note**: Forecasts continue through peak (Aug 23-24) and recovery (Aug 26) for full event assessment

**Data Download Range**: **Jul 19 - Aug 27, 2023** (40 days continuous)
- Covers all initialization times (Jul 19, 26, Aug 2, 8 at 12 UTC)
- Full verification period (onset Aug 9 → peak Aug 23-24 → recovery Aug 26)
- Enables onset/peak/recovery analysis for all lead times

**Heatwave Thresholds**: 30°C, 35°C, 40°C (regional T2m)

**Key Scientific Questions**:
- Can Aurora detect heatwave occurrence 21 days in advance?
- At what lead time does onset timing skill degrade below operational usefulness?
- Does Aurora capture the heat dome blocking pattern at subseasonal leads?
- Does Aurora underpredict heat extremes (like it underpredicts cold extremes)?

---

## Variables Required for Analysis

### **⚠️ CRITICAL: Aurora Pressure Level Indexing**

**Aurora pressure levels are in REVERSE order:**
```
(1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50) hPa
Index:  0     1     2     3     4     5     6     7     8     9    10    11    12
```

**Correct indices for atmospheric variables:**
- **850 hPa**: `level_idx=2` (warm air mass)
- **700 hPa**: `level_idx=3` (mid-troposphere)
- **500 hPa**: `level_idx=5` (heat dome/blocking)
- **250 hPa**: `level_idx=8` (jet stream)

---

### **Essential Variables** (Stage 1 & 2):
- **2m temperature (t2m)**: Primary heatwave indicator, intensity, spatial extent
- **850 hPa temperature** (`level_idx=2`): Warm air mass position/intensity
- **500 hPa geopotential (z)** (`level_idx=5`): Heat dome/blocking pattern
- **Mean sea level pressure (msl)**: Surface high-pressure system

### **Important Variables** (Stage 2 characterization):
- **250 hPa u/v winds** (`level_idx=8`): Jet stream position, subtropical jet
- **850 hPa u/v winds** (`level_idx=2`): Low-level warm air advection (southerly flow)
- **700 hPa temperature** (`level_idx=3`): Mid-troposphere heat pool
- **10m u/v winds**: Surface wind (for heat advection)

### **Derived/Composite Variables**:
- **Heat index** (optional): Combined T2m + humidity (human impact)
- **Temperature anomalies**: Forecast vs climatology (how unusual?)
- **Geopotential height anomalies**: Identify heat dome vs climatology
- **Blocking indices**: Omega block, Rex block patterns

---

## Visualization Strategy

### Per-Event Outputs

**1. Temperature Evolution Maps** (3-panel comparisons):
- Aurora forecast vs ERA5 truth at onset/peak/recovery
- For each lead time: 1, 7, 14, 21 days
- Show T2m field with 30°C, 35°C, 40°C contours (RED TONES)

**2. Time Series at Key Cities**:
- Major population centers (Lyon, Toulouse, Bilbao, Geneva)
- ERA5 vs Aurora temperature evolution
- Shaded regions for different lead times
- Shows onset timing accuracy

**3. Lead Time Skill Degradation**:
- RMSE vs lead time (1, 7, 14, 21 days)
- Temperature bias vs lead time
- Onset timing error vs lead time
- Duration error vs lead time

**4. Spatial Extent Comparison**:
- Area above threshold (30°C, 35°C, 40°C)
- Aurora vs ERA5 for each lead time
- IoU metric visualization

**5. Error Maps**:
- Spatial distribution of temperature errors
- At peak day (Aug 23-24)
- For 7-day and 14-day leads (most operationally relevant)

**6. Physical Mechanism Validation**:
- Z500 blocking pattern: Aurora vs ERA5
- T850 warm air mass: Aurora vs ERA5
- MSL high-pressure system: Aurora vs ERA5
- Jet stream position (250 hPa winds)

### Color Schemes (INVERTED from Freeze)

**Temperature fields**:
- Colormap: `YlOrRd` or `Reds` (hot colors instead of blues)
- Range: 15°C to 45°C (instead of -30°C to 15°C)

**Contours**:
- 30°C: Black (thick)
- 35°C: Red (medium)
- 40°C: Dark red (thin)

**Difference plots**:
- Still `RdBu_r` (blue = Aurora too cold, red = Aurora too warm)
- Centered at 0

---

## Data Requirements

### ERA5 Variables Needed

**Surface-level** (single-levels):
- `2t`: 2-meter temperature (primary heatwave indicator)
- `10u`, `10v`: 10-meter winds (for heat advection, surface circulation)
- `msl`: Mean sea level pressure (surface high-pressure patterns)

**Atmospheric** (pressure-levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `t`: Temperature (all levels for vertical structure, especially 850, 700, 500 hPa)
- `u`, `v`: Wind components (jet stream at 250 hPa, advection at 850 hPa)
- `z`: Geopotential (heat dome/blocking patterns at 500 hPa)
- `q`: Specific humidity (required by Aurora, for heat index)

**Static** (provided with Aurora checkpoints):
- `z`: Geopotential (topography)
- `lsm`: Land-sea mask
- `slt`: Soil type

**Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)

### Download Strategy

**August 2023 Heatwave**:
- **Download range**: Jul 19 - Aug 27, 2023 (40 days continuous, ~160 timesteps)
- **Actual usage**: 4 init timesteps (Jul 19, 26, Aug 2, 8 at 12 UTC) + continuous verification
- **Individual files**: One file per date (surface + atmospheric)
  - `2023-07-19-surface-level.nc`, `2023-07-19-atmospheric.nc`
  - ...
  - `2023-08-27-surface-level.nc`, `2023-08-27-atmospheric.nc`
- **Combined files**: Concatenated into continuous timeseries
  - `heatwave_2023_surface_jul19-aug27.nc`
  - `heatwave_2023_atmospheric_jul19-aug27.nc`

---

## Success Criteria

### Temperature Prediction

**Excellent Performance**:
- 1-day lead: RMSE < 2°C
- 7-day lead: RMSE < 4°C
- 14-day lead: RMSE < 6°C
- 21-day lead: RMSE < 8°C

**Minimum Acceptable**:
- 1-day lead: RMSE < 3°C
- 7-day lead: RMSE < 6°C
- 14-day lead: RMSE < 8°C
- 21-day lead: RMSE < 10°C

### Onset Timing

**Excellent**: Onset timing within ±6 hours at 7-day lead
**Acceptable**: Onset timing within ±12 hours at 7-day lead

### Spatial Extent

**Excellent**: IoU > 0.7 at 7-day lead
**Acceptable**: IoU > 0.5 at 7-day lead

---

## Expected Aurora Challenges

### Challenge 1: Temperature Bias in Extreme Heat
- ML models often underpredict temperature extremes (regression to the mean)
- Aurora may predict too cool during hottest periods
- Critical for heat health warnings (underestimating = missed warnings)

### Challenge 2: Heat Dome Persistence
- August 2023 required persistent subtropical high
- Aurora's ability to maintain blocking patterns beyond 7 days uncertain
- 21-day lead will test this directly

### Challenge 3: Onset Timing
- Small errors in southerly flow onset → large temperature impact
- 12h delay in heat onset = different heat health scenario
- Tests Aurora's synoptic feature propagation skill

### Challenge 4: Regional Topography
- Complex terrain (Alps, Pyrenees, Massif Central)
- Urban heat islands (Lyon, Toulouse)
- Aurora's 0.25° resolution may smooth out local heating amplification

### Challenge 5: Comparison with Freeze Performance
- Does Aurora have symmetric skill for cold vs heat extremes?
- Or does it show bias toward one direction?
- Critical for understanding model physics

---

## Research Significance

### Novel Contributions

1. **First Aurora heatwave assessment**: No published studies on Aurora's heat extreme skill
2. **Cold-heat symmetry test**: Direct comparison with freeze event skill
3. **Multi-week event evaluation**: Tests sustained heat prediction (17+ days)
4. **Extended lead times**: 21-day forecasts rare in extreme event literature
5. **Heat health relevance**: Early warning for vulnerable populations

### Paper Narrative

Heatwave events provide critical comparison to freeze events:
- **Freeze**: Arctic air, blocking high, cold temperature extremes
- **Heatwave**: Mediterranean/subtropical air, heat dome, hot temperature extremes
- **Both**: Large-scale synoptic forcing, slow evolution, ~2-week duration

Results will reveal Aurora's **temperature extreme symmetry** and **bias patterns**.

---

## Why No Stage 2 (Initialization Sensitivity)?

**Decision: Skip initialization time sensitivity testing for heatwave events**

**Rationale** (same as freeze):
1. **Synoptic scale**: Heatwaves are driven by large-scale patterns (100s-1000s km)
2. **Slow evolution**: Temperature changes occur over days, not hours
3. **Lower sensitivity**: Unlike TCs (mesoscale, 6h init matters), 6-12h difference negligible
4. **Resource allocation**: Focus computational resources on more lead times (1, 7, 14, 21 days)
5. **Literature support**: NWP studies show initialization time less critical for synoptic events

**Trade-off**: We test 4 lead times (1, 7, 14, 21 days) instead of 4 TC lead times + 4 init times

---

## Next Steps

1. ✅ Create experimental design document
2. ✅ Create Heatwave folder structure
3. ⬜ Create Heatwave_utils.py (adapt from Freeze_utils.py)
4. ⬜ Create data download scripts
5. ⬜ Download ERA5 data for Aug 2023 heatwave
6. ⬜ Create baseline analysis script
7. ⬜ Create Stage 1 detection script
8. ⬜ Run forecasts (4 lead times)
9. ⬜ Analyze results
10. ⬜ Document findings (HEATWAVE_RESULTS.md)
11. ⬜ Update master research plan

---

**Notes**:
- **Inverted logic from freeze**: Use `>` instead of `<` for thresholds, `argmax` instead of `argmin`
- **Similar structure**: Same two-stage approach, same lead times, same metrics framework
- **Red color scheme**: Hot colors instead of cold blues
- **Complementary to freeze**: Tests Aurora on opposite temperature extreme
- **Out-of-sample**: August 2023 ensures scientific validity

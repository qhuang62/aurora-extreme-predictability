# Typhoon Hinnamnor 2022 - Experimental Design

**Event**: Typhoon Hinnamnor (2022)
**Target**: September 6, 2022 18:00 UTC (South Korea landfall)
**Model**: Aurora 0.25° Pretrained
**Basin**: Western Pacific (East China Sea → South Korea)
**Status**: Out-of-sample (2022, after Aurora's 1979-2020 training period)

---

## Event Overview

### Typhoon Hinnamnor Characteristics

**Track Summary**:
- **Origin**: Aug 28, 2022 (east of Ogasawara Islands, Japan)
- **Peak Intensity**: Aug 30-31, 2022 (145 kt, 910 mb - Category 5 super typhoon)
- **Primary Landfall**: Sep 6, 2022 18:00 UTC (South Korea, near Geoje) ← **TARGET**
- **Dissipation**: Sep 9, 2022 (extratropical transition)

**Notable Track Features**:
1. Rapid intensification to Cat 5 (Aug 28 → Aug 30: 35 kt → 145 kt)
2. Westward drift at peak intensity (Aug 30-31)
3. Stalling south of Okinawa (Sep 1-3)
4. Sharp northward recurvature into Korea (Sep 4-6)
5. Significant weakening before landfall (~75-90 kt at landfall vs 145 kt peak)

**Why This Event?**:
- Out-of-sample test case (2022 vs Aurora's 1979-2020 training)
- First Category 5 typhoon of 2022
- Unusual track: westward peak → stall → sharp north turn
- Significant intensity change challenge (145 kt → 75 kt in 5 days)
- Clean landfall target on 6-hourly grid (18:00 UTC)
- Tests Aurora's Western Pacific TC skill (vs Ian/Sandy Atlantic basin)

---

## Target Selection

### Primary Target: Sep 6, 2022 18:00 UTC

**Landfall Position**: ~35.0°N, 128.0°E (South Korea, Geoje area)

**Rationale**:
- Most operationally significant landfall (South Korea mainland)
- On 6-hourly grid (18:00 UTC) - perfect for Aurora
- Clear verification target for field comparisons
- Follows Sandy/Ian methodology (target = landfall time)

**Storm Characteristics at Target**:
- Intensity: ~75-90 kt, ~960-970 mb (weakened from peak)
- Size: Large circulation, well-defined but weakening
- Motion: N/NNE at ~30-40 km/h (fast-moving)
- Environment: Weakening due to land interaction + cooler waters

---

## Stage 1: Lead Time Assessment

**Question**: How far in advance can Aurora predict Hinnamnor's South Korea landfall?

**Approach**: Variable initialization date, fixed target (Sep 6, 2022 18:00 UTC)

### Configuration

| Lead Time | Init Date & Time | Storm Stage | IBTrACS Position | Forecast Steps |
|-----------|------------------|-------------|------------------|----------------|
| **1-day** | Sep 5 18:00 UTC | Approaching Korea, weakening | ~33°N, 127°E | 3 steps (24h) |
| **3-day** | Sep 3 18:00 UTC | Post-stall, turning north | ~29°N, 126°E | 11 steps (72h) |
| **5-day** | Sep 1 18:00 UTC | Stalling phase, still strong | ~24°N, 126°E | 19 steps (120h) |
| **7-day** | Aug 30 18:00 UTC | Peak intensity (Cat 5!) | ~27°N, 133°E | 27 steps (168h) |

**Target for All**: Sep 6, 2022 18:00 UTC (South Korea landfall)

**Note**: 7-day lead initializes at peak Cat 5 intensity - tests Aurora's ability to predict:
1. The sharp northward turn
2. Significant weakening (145 kt → 75 kt)
3. Timing of landfall after stalling period

### Expected Challenges by Lead Time

**1-Day Lead** (Sep 5 18:00 UTC):
- Storm already approaching Korea
- Weakening phase (from peak)
- Short forecast, but rapid motion challenge

**3-Day Lead** (Sep 3 18:00 UTC):
- Post-stall phase
- Must predict northward recurvature timing
- Critical for operational warning lead time

**5-Day Lead** (Sep 1 18:00 UTC):
- During stalling phase south of Okinawa
- Must predict end of stall + northward acceleration
- Must predict significant weakening trend
- Tests Aurora's medium-range TC skill in WPac

**7-Day Lead** (Aug 30 18:00 UTC):
- At peak Cat 5 intensity!
- Must predict entire weakening + recurvature + landfall sequence
- Extremely challenging: includes stall, turn, and intensity change
- Tests Aurora's ability to predict track regime change

---

## Stage 2: Initialization Time Sensitivity

**Question**: How sensitive is Aurora's Hinnamnor prediction to initialization time of day?

**Approach**: Fixed lead time (based on Stage 1 best performance), variable initialization time

### Anticipated Configuration (3-Day Lead)

Based on Sandy/Ian results (3-day typically optimal for sensitivity testing):

**Initialization Date**: Sep 3, 2022 (3 days before landfall)

| Init Time | Init Date & Time | IBTrACS Position | Forecast Steps | Forecast Hours |
|-----------|------------------|------------------|----------------|----------------|
| **00 UTC** | Sep 3 00:00 UTC | ~27.5°N, 125.5°E | 14 steps | 90h |
| **06 UTC** | Sep 3 06:00 UTC | ~28.0°N, 125.7°E | 13 steps | 84h |
| **12 UTC** | Sep 3 12:00 UTC | ~28.5°N, 126.0°E | 12 steps | 78h |
| **18 UTC** | Sep 3 18:00 UTC | ~29.0°N, 126.3°E | 11 steps | 72h |

**Target for All**: Sep 6, 2022 18:00 UTC (South Korea landfall)

**Note**: Final Stage 2 configuration determined after Stage 1 analysis.

### Alternative Configurations

**If 1-Day Lead Optimal** (Sep 5 init):
- 00, 06, 12, 18 UTC on Sep 5
- Very short lead but high accuracy expected

**If 5-Day Lead Optimal** (Sep 1 init):
- 00, 06, 12, 18 UTC on Sep 1
- During stalling phase - interesting sensitivity test

---

## Evaluation Metrics

### Track-Based Metrics (Tracker-Derived)

**Pre-Landfall Ocean Phase**:
- Track position error (km) at 24h, 48h, 72h, 96h, 120h lead times
- Mean track error over entire forecast
- Track error evolution vs lead time
- Position uncertainty (spread across init times)

**Landfall Metrics**:
- Landfall location error (km) - predicted vs observed (~35°N, 128°E)
- Landfall timing error (hours)
- Track continuity during recurvature (Sep 3-6)

### Field-Based Metrics (Direct Comparison at Landfall)

**Primary Variables** (at Sep 6, 2022 18:00 UTC):

1. **Mean Sea Level Pressure (MSL)**
   - Minimum pressure (Aurora vs ERA5)
   - Pressure bias (hPa)
   - Center position from MSL minimum
   - Spatial pattern correlation

2. **10m Wind Speed (derived from 10u, 10v)**
   - Maximum wind speed (Aurora vs ERA5)
   - Wind speed bias (m/s)
   - Wind field RMSE over landfall region
   - Asymmetry pattern comparison

3. **700 hPa Geopotential (Z700)**
   - Minimum Z700 (tracker variable)
   - Upper-level structure verification
   - Pattern correlation

### Regional Domain for Field Comparison

**Landfall Region**:
- Latitude: 30-40°N (South Korea + surrounding waters)
- Longitude: 122-135°E (East China Sea + Korea + Sea of Japan)
- Captures approach, landfall, and recurvature area

---

## Data Requirements

### ERA5 Data Download

**Variables Required**:

**Surface-level** (single level):
- `2t`: 2-meter temperature
- `10u`: 10-meter u-wind component
- `10v`: 10-meter v-wind component
- `msl`: Mean sea level pressure

**Atmospheric** (pressure levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `t`: Temperature
- `u`: U-wind component
- `v`: V-wind component
- `q`: Specific humidity
- `z`: Geopotential height

**Static** (already available):
- `lsm`: Land-sea mask (0.25° resolution)
- `slt`: Soil type (0.25° resolution)
- `z`: Surface geopotential/topography (0.25° resolution)

### File Strategy

**Combined Initialization File** (for forecasts):
- **Filename**: `hinnamnor_2022_surface_combined.nc`, `hinnamnor_2022_atmospheric_combined.nc`
- **Time Range**: Aug 30, 2022 00:00 UTC → Sep 6, 2022 12:00 UTC
- **Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)
- **Purpose**: Contains all initialization times for Stage 1 and Stage 2

**Separate Verification File** (for landfall):
- **Filename**: `hinnamnor_2022_surface_landfall.nc`, `hinnamnor_2022_atmospheric_landfall.nc`
- **Time Range**: Sep 6, 2022 18:00 UTC (single timestep)
- **Purpose**: ERA5 "truth" for landfall field comparisons

**IBTrACS Observational Data**:
- **Source**: https://ncics.org/ibtracs/index.php?name=v04r01-2022239N22150
- **Storm ID**: 2022239N22150
- **Time Range**: Aug 28, 2022 → Sep 9, 2022
- **Format**: Will need to add to TC_utils.py hardcoded tracks or download CSV
- **Purpose**: Best track data for verification

---

## Key Differences from Sandy 2012 and Ian 2022

| Aspect | Sandy 2012 | Ian 2022 | Hinnamnor 2022 |
|--------|------------|----------|----------------|
| **Sample Status** | In-sample | Out-of-sample | Out-of-sample |
| **Basin** | Atlantic | Atlantic/Gulf | Western Pacific |
| **Peak Intensity** | 940 mb, 100 kt | 937 mb, 140 kt | 910 mb, 145 kt |
| **Size** | Very large | Compact | Large |
| **Track Pattern** | NE then NW hook | NW then N | W then sharp N recurve |
| **Landfall Intensity** | Hybrid, 940 mb | Major, ~940 mb | Weakened, ~970 mb |
| **Intensity Change** | Gradual hybrid transition | Rapid intensification | Rapid int. then weakening |
| **Unusual Feature** | Extratropical transition | RI in Gulf | Stalling + recurvature |
| **Max Lead Time** | 7 days | 6 days (genesis) | 7 days (peak intensity) |
| **Key Challenge** | Track anomaly | RI timing | Weakening + recurvature |

---

## Success Criteria

### Minimum Acceptable Performance
- 1-day lead: <100 km landfall error
- 3-day lead: <300 km landfall error
- 5-day lead: <500 km landfall error
- 7-day lead: <700 km landfall error (very challenging due to stalling/recurvature)
- Track captures northward turn (not continuing westward)

### Excellent Performance
- 1-day lead: <50 km landfall error
- 3-day lead: <200 km landfall error
- 5-day lead: <400 km landfall error
- 7-day lead: <600 km landfall error
- Correctly predicts recurvature timing
- Captures significant weakening trend

### Physical Consistency Checks
- MSL minimum 950-980 mb at landfall (realistic weakened intensity)
- Wind speed >25 m/s at landfall (typhoon force, weakened from peak)
- Track shows clear northward recurvature (not stuck in stall)
- Track remains continuous (no jumps during recurvature)

---

## Expected Aurora Challenges

Based on Sandy/Ian results and Hinnamnor's unique characteristics:

**1. Stalling Phase** (Sep 1-3):
- Hinnamnor stalled south of Okinawa
- Slow/erratic motion difficult for models to predict
- May impact timing of subsequent northward turn

**2. Recurvature Prediction** (Sep 3-6):
- Sharp northward turn into Korea
- Depends on synoptic pattern (trough interaction)
- Track regime change from westward to northward
- Critical for landfall location accuracy

**3. Weakening Trend** (Aug 31 → Sep 6):
- 145 kt → 75 kt (70 kt decrease in 5-6 days)
- Cooler waters + land interaction
- Aurora may underpredict weakening (as seen in Sandy/Ian)
- Expect MSL bias (too low/too strong)

**4. Western Pacific Basin**:
- Different from Atlantic (Sandy/Ian)
- Tests Aurora's basin-dependent skill
- Different environmental characteristics

**5. Large Spatial Scale**:
- Very large circulation
- May test Aurora's 0.25° resolution differently than compact Ian

**6. 7-Day Lead from Peak Intensity**:
- Initializing at Cat 5 peak
- Must predict entire weakening + track change sequence
- Most challenging initialization scenario

---

## Analysis Timeline

1. **IBTrACS Data**: Add Hinnamnor track to TC_utils.py
2. **ERA5 Download**: Download combined (Aug 30-Sep 6) and landfall (Sep 6 18Z) files
3. **Script Adaptation**: Adapt Sandy/Ian scripts for Hinnamnor
4. **Stage 1 Execution**: Run 1, 3, 5, 7-day lead forecasts
5. **Stage 1 Analysis**: Analyze results, identify best lead time
6. **Stage 2 Execution**: Run 4 initialization times at optimal lead
7. **Stage 2 Analysis**: Analyze initialization sensitivity
8. **Documentation**: Complete `HINNAMNOR_RESULTS.md` with findings
9. **Paper Integration**: Add to multi-event, multi-basin comparison

---

## Output Products

### Stage 1 Outputs (~10 figures + JSON)
- `hinnamnor_stage1_tracks.png` - Track comparison (4 lead times)
- `hinnamnor_stage1_errors.png` - Error evolution vs lead time
- `hinnamnor_1day_landfall_msl.png` - MSL field at landfall (1-day)
- `hinnamnor_1day_landfall_wind.png` - Wind field at landfall (1-day)
- `hinnamnor_3day_landfall_msl.png` - MSL field at landfall (3-day)
- `hinnamnor_3day_landfall_wind.png` - Wind field at landfall (3-day)
- `hinnamnor_5day_landfall_msl.png` - MSL field at landfall (5-day)
- `hinnamnor_5day_landfall_wind.png` - Wind field at landfall (5-day)
- `hinnamnor_7day_landfall_msl.png` - MSL field at landfall (7-day)
- `hinnamnor_7day_landfall_wind.png` - Wind field at landfall (7-day)
- `hinnamnor_stage1_lead_time_results.pkl` - Saved results
- `hinnamnor_stage1_lead_time_results.json` - Summary statistics

### Stage 2 Outputs (~10 figures + JSON)
- `hinnamnor_stage2_init_tracks.png` - Combined track comparison (4 init times)
- `hinnamnor_stage2_init_errors.png` - Error comparison across init times
- `hinnamnor_init00_landfall_msl.png` - MSL field (00 UTC init)
- `hinnamnor_init00_landfall_wind.png` - Wind field (00 UTC init)
- `hinnamnor_init06_landfall_msl.png` - MSL field (06 UTC init)
- `hinnamnor_init06_landfall_wind.png` - Wind field (06 UTC init)
- `hinnamnor_init12_landfall_msl.png` - MSL field (12 UTC init)
- `hinnamnor_init12_landfall_wind.png` - Wind field (12 UTC init)
- `hinnamnor_init18_landfall_msl.png` - MSL field (18 UTC init)
- `hinnamnor_init18_landfall_wind.png` - Wind field (18 UTC init)
- `hinnamnor_stage2_init_time_results.pkl` - Saved results
- `hinnamnor_stage2_init_time_results.json` - Summary statistics

**Total**: ~20 figures + 2 JSON summary files (matching Sandy/Ian)

---

## Next Steps

1. ✅ Create event folder: `/research/TC/2022_Hinnamnor/`
2. ✅ Create experimental design: `HINNAMNOR_EXPERIMENTAL_DESIGN.md`
3. ⬜ Add Hinnamnor track to `TC_utils.py`
4. ⬜ Create data workflow: `HINNAMNOR_DATA_WORKFLOW.md`
5. ⬜ Download ERA5 data (combined + landfall files)
6. ⬜ Create Stage 1 script: `hinnamnor_stage1_lead_day.py`
7. ⬜ Create Stage 2 script: `hinnamnor_stage2_init_time.py`
8. ⬜ Execute Stage 1 analysis
9. ⬜ Execute Stage 2 analysis
10. ⬜ Document results: `HINNAMNOR_RESULTS.md`
11. ⬜ Update master research plan

---

**Notes**:
- **Out-of-sample** case (2022 > 2020 Aurora training cutoff) → scientifically valid
- **Western Pacific basin** → tests Aurora's basin generalization
- **Unusual track** (stall + recurvature) → challenging prediction scenario
- **Peak Cat 5 → weakened landfall** → tests intensity change prediction
- **Multi-basin comparison** with Sandy/Ian will provide key insights for paper

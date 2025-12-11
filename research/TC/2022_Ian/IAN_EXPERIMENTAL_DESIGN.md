# Hurricane Ian 2022 - Experimental Design

**Event**: Hurricane Ian (2022)
**Target**: September 28, 2022 20:00 UTC (Florida landfall)
**Model**: Aurora 0.25° Pretrained
**Basin**: Atlantic (Caribbean → Gulf of Mexico → Florida)
**Status**: Out-of-sample (2022, after Aurora's 1979-2020 training period)

---

## Event Overview

### Hurricane Ian Characteristics

**Track Summary**:
- **Origin**: Sep 22, 2022 18:00 UTC (eastern Caribbean)
- **Peak Intensity**: Sep 28, 2022 12:00 UTC (140 kt, 937 mb)
- **Primary Landfall**: Sep 28, 2022 20:00 UTC (Florida, USA) ← **TARGET**
- **Storm End**: Oct 1, 2022 (extratropical transition)

**Landfall Events**:
1. Sep 27, 2022 08:00 UTC - Cuba landfall
2. **Sep 28, 2022 20:00 UTC - Florida landfall (PRIMARY TARGET)**
3. Sep 30, 2022 18:00 UTC - South Carolina landfall

**Why This Event?**:
- Out-of-sample test case (2022 vs Aurora's 1979-2020 training)
- Major US disaster ($112+ billion damage, 5th costliest on record)
- Rapid intensification in Gulf of Mexico (Sep 26-28)
- Clean landfall target for verification (similar to Sandy methodology)
- Compact, intense hurricane at landfall (vs Sandy's large, hybrid system)

---

## Target Selection

### Primary Target: Sep 28, 2022 20:00 UTC

**Landfall Position**: 26.80°N, 82.00°W (Florida west coast, near Fort Myers)

**Rationale**:
- Most destructive and operationally critical landfall
- Near peak intensity (8 hours after 937 mb minimum)
- W→E landfall trajectory (good for tracker, similar to Sandy)
- Clear verification target for field comparisons
- 6-hourly ERA5 data available at 18:00 and 00:00 (bracket landfall)

**Storm Characteristics at Target**:
- Intensity: ~140 kt sustained winds, ~940 mb central pressure
- Size: Compact, well-defined eye
- Motion: NNE at ~15 km/h
- Environment: Warm Gulf waters, low shear

---

## Stage 1: Lead Time Assessment

**Question**: How far in advance can Aurora predict Ian's Florida landfall?

**Approach**: Variable initialization date, fixed target (Sep 28, 2022 20:00 UTC)

### Configuration

| Lead Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours |
|-----------|------------------|-------------------------|----------------|----------------|
| **1-day** | Sep 27 18:00 UTC | 23.50°N, 83.30°W | 5 steps | 30h |
| **3-day** | Sep 25 18:00 UTC | 15.80°N, 80.10°W | 13 steps | 78h |
| **5-day** | Sep 23 18:00 UTC | 14.60°N, 70.60°W | 21 steps | 126h |
| **7-day** | Sep 21 18:00 UTC | N/A (storm not formed) | — | — |

**Note**: Ian formed on Sep 22 18:00 UTC, so **7-day lead is not possible**. We'll use **6-day lead** instead:

| Lead Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours |
|-----------|------------------|-------------------------|----------------|----------------|
| **6-day** | Sep 22 18:00 UTC | 12.30°N, 66.30°W | 25 steps | 150h |

### Updated Stage 1 Lead Times

| Lead Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours | Storm Stage |
|-----------|------------------|-------------------------|----------------|----------------|-------------|
| **1-day** | Sep 27 18:00 UTC | 23.50°N, 83.30°W | 5 steps | 30h | Approaching FL, intensifying |
| **3-day** | Sep 25 18:00 UTC | 15.80°N, 80.10°W | 13 steps | 78h | NW Caribbean, pre-intensification |
| **5-day** | Sep 23 18:00 UTC | 14.60°N, 70.60°W | 21 steps | 126h | Central Caribbean, tropical storm |
| **6-day** | Sep 22 18:00 UTC | 12.30°N, 66.30°W | 25 steps | 150h | Genesis, tropical depression |

**Target for All**: Sep 28, 2022 20:00 UTC (Florida landfall at 26.80°N, 82.00°W)

### Expected Challenges by Lead Time

**1-Day Lead** (Sep 27 18:00 UTC):
- Storm already in Gulf, approaching Florida
- Intensifying phase (increasing from ~120 kt to 140 kt)
- Short forecast, but rapid intensity change challenge

**3-Day Lead** (Sep 25 18:00 UTC):
- Pre-intensification phase in Caribbean
- Must predict turn northward and rapid intensification
- Critical forecast for operational warning

**5-Day Lead** (Sep 23 18:00 UTC):
- Early tropical storm stage
- Must predict entire Gulf track and intensification
- Tests Aurora's medium-range TC skill

**6-Day Lead** (Sep 22 18:00 UTC):
- Genesis stage (tropical depression)
- Full lifecycle prediction required
- Tests Aurora's ability to develop and track new systems

---

## Stage 2: Initialization Time Sensitivity

**Question**: How sensitive is Aurora's Ian prediction to initialization time of day?

**Approach**: Fixed initialization date (based on Stage 1 best lead time), variable initialization time

### Anticipated Configuration (3-Day Lead)

Based on Sandy's results (3-day was optimal for sensitivity testing), we'll likely use **Sep 25** initialization:

| Init Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours |
|-----------|------------------|-------------------------|----------------|----------------|
| **00 UTC** | Sep 25 00:00 UTC | 14.60°N, 77.20°W | 16 steps | 96h |
| **06 UTC** | Sep 25 06:00 UTC | 14.60°N, 78.30°W | 15 steps | 90h |
| **12 UTC** | Sep 25 12:00 UTC | 15.00°N, 79.40°W | 14 steps | 84h |
| **18 UTC** | Sep 25 18:00 UTC | 15.80°N, 80.10°W | 13 steps | 78h |

**Target for All**: Sep 28, 2022 20:00 UTC (Florida landfall)

**Note**: Final configuration will be determined after Stage 1 analysis. If 1-day or 5-day shows better performance, we'll adjust accordingly.

### Alternative Configurations

**If 1-Day Lead Optimal** (Sep 27 init):

| Init Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours |
|-----------|------------------|-------------------------|----------------|----------------|
| **00 UTC** | Sep 27 00:00 UTC | 20.80°N, 83.30°W | 8 steps | 48h |
| **06 UTC** | Sep 27 06:00 UTC | 21.80°N, 83.60°W | 7 steps | 42h |
| **12 UTC** | Sep 27 12:00 UTC | 22.60°N, 83.60°W | 6 steps | 36h |
| **18 UTC** | Sep 27 18:00 UTC | 23.50°N, 83.30°W | 5 steps | 30h |

**If 5-Day Lead Optimal** (Sep 23 init):

| Init Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Forecast Hours |
|-----------|------------------|-------------------------|----------------|----------------|
| **00 UTC** | Sep 23 00:00 UTC | 12.90°N, 67.20°W | 24 steps | 144h |
| **06 UTC** | Sep 23 06:00 UTC | 13.70°N, 68.10°W | 23 steps | 138h |
| **12 UTC** | Sep 23 12:00 UTC | 14.20°N, 69.30°W | 22 steps | 132h |
| **18 UTC** | Sep 23 18:00 UTC | 14.60°N, 70.60°W | 21 steps | 126h |

---

## Evaluation Metrics

### Track-Based Metrics (Tracker-Derived)

**Pre-Landfall Ocean Phase**:
- Track position error (km) at 24h, 48h, 72h lead times
- Mean track error over entire forecast
- Track error evolution vs lead time
- Position uncertainty (spread across init times)

**Landfall Metrics**:
- Landfall location error (km) - predicted vs observed (26.80°N, 82.00°W)
- Landfall timing error (hours) - if tracker captures it
- Landfall timing detection via longitude threshold (-82.0°W)

### Field-Based Metrics (Direct Comparison at Landfall)

**Primary Variables** (at Sep 28, 2022 18:00 and 00:00 UTC, bracketing 20:00 landfall):

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
- Latitude: 20-32°N (Gulf coast + surrounding)
- Longitude: 78-88°W (Florida + Gulf waters)
- Captures approach, landfall, and immediate inland penetration

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
- **Filename**: `era5_ian_2022_init_combined.nc`
- **Time Range**: Sep 22, 2022 00:00 UTC → Sep 28, 2022 12:00 UTC
- **Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)
- **Purpose**: Contains all initialization times for Stage 1 and Stage 2

**Separate Verification File** (for landfall):
- **Filename**: `era5_ian_2022_landfall_verification.nc`
- **Time Range**: Sep 28, 2022 18:00 UTC → Sep 29, 2022 06:00 UTC
- **Temporal Resolution**: 6-hourly
- **Purpose**: ERA5 "truth" for landfall field comparisons

**IBTrACS Observational Data**:
- **Source**: https://ncics.org/ibtracs/index.php?name=v04r01-2022266N12294
- **Time Range**: Sep 22, 2022 18:00 UTC → Sep 30, 2022 18:00 UTC
- **Format**: CSV or netCDF from IBTrACS database
- **Purpose**: Best track data for verification

---

## Key Differences from Sandy 2012

| Aspect | Hurricane Sandy 2012 | Hurricane Ian 2022 |
|--------|---------------------|-------------------|
| **Sample Status** | In-sample (Aurora training) | Out-of-sample (post-training) |
| **Scientific Validity** | Methodology demonstration | Primary science result |
| **Basin** | Atlantic Ocean | Caribbean → Gulf of Mexico |
| **Intensity** | Large, hybrid system | Compact, intense hurricane |
| **Peak Intensity** | 940 mb, 100 kt | 937 mb, 140 kt |
| **Size** | Very large wind field | Compact core, smaller field |
| **Track** | NE then NW (hook) | NW then N (straighter) |
| **Intensification** | Gradual | Rapid (Gulf waters) |
| **Max Lead Time** | 7 days | 6 days (genesis limit) |
| **Operational Challenge** | Unusual track (hybrid transition) | Rapid intensification timing |

---

## Success Criteria

### Minimum Acceptable Performance
- 1-day lead: <100 km landfall error
- 3-day lead: <300 km landfall error
- 5-day lead: <500 km landfall error
- Track captures Gulf entry and northward turn

### Excellent Performance
- 1-day lead: <50 km landfall error
- 3-day lead: <200 km landfall error
- 5-day lead: <350 km landfall error
- Correctly predicts rapid intensification phase

### Physical Consistency Checks
- MSL minimum <950 mb at landfall (realistic intensity)
- Wind speed >35 m/s at landfall (hurricane force)
- Warm core structure maintained (no premature transition)
- Track remains continuous (no jumps or tracker failures)

---

## Expected Aurora Challenges

Based on Sandy results and Ian's characteristics:

**1. Rapid Intensification** (Sep 26-28):
- Sandy showed systematic intensity underprediction
- Ian's rapid intensification may be even harder to capture
- Expect MSL bias (too high, too weak)

**2. Gulf of Mexico Dynamics**:
- Warm water loop current interaction
- Different from Sandy's Atlantic track
- Tests Aurora's basin-dependent skill

**3. Track Turn Prediction**:
- Must predict northward turn into Florida
- Critical for landfall location accuracy
- Tests Aurora's synoptic pattern recognition

**4. Compact Core Structure**:
- Small, intense eye vs Sandy's large field
- May test Aurora's 0.25° resolution limits
- Impacts intensity metrics

**5. Genesis Prediction** (6-day lead):
- Starting from tropical depression stage
- Tests Aurora's ability to develop systems from weak disturbances
- Most challenging lead time

---

## Analysis Timeline

1. **Data Download**: Download ERA5 combined and landfall verification files
2. **Script Adaptation**: Adapt Sandy's Stage 1 and Stage 2 scripts for Ian
3. **Stage 1 Execution**: Run 1-day, 3-day, 5-day, 6-day lead forecasts
4. **Stage 1 Analysis**: Analyze results, identify best lead time
5. **Stage 2 Execution**: Run 4 initialization times at optimal lead
6. **Stage 2 Analysis**: Analyze initialization sensitivity
7. **Documentation**: Complete `IAN_RESULTS.md` with findings
8. **Paper Integration**: Add Ian results to multi-event comparison

---

## Output Products

### Stage 1 Outputs
- `ian_stage1_tracks.png` - Track comparison (4 lead times)
- `ian_stage1_errors.png` - Error evolution vs lead time
- `ian_1day_landfall_msl.png` - MSL field at landfall (1-day)
- `ian_1day_landfall_wind.png` - Wind field at landfall (1-day)
- `ian_3day_landfall_msl.png` - MSL field at landfall (3-day)
- `ian_3day_landfall_wind.png` - Wind field at landfall (3-day)
- `ian_5day_landfall_msl.png` - MSL field at landfall (5-day)
- `ian_5day_landfall_wind.png` - Wind field at landfall (5-day)
- `ian_6day_landfall_msl.png` - MSL field at landfall (6-day)
- `ian_6day_landfall_wind.png` - Wind field at landfall (6-day)
- `ian_stage1_lead_time_results.json` - Summary statistics

### Stage 2 Outputs
- `ian_stage2_init_tracks.png` - Combined track comparison (4 init times)
- `ian_stage2_init_errors.png` - Error comparison across init times
- `ian_init00_landfall_msl.png` - MSL field (00 UTC init)
- `ian_init00_landfall_wind.png` - Wind field (00 UTC init)
- `ian_init06_landfall_msl.png` - MSL field (06 UTC init)
- `ian_init06_landfall_wind.png` - Wind field (06 UTC init)
- `ian_init12_landfall_msl.png` - MSL field (12 UTC init)
- `ian_init12_landfall_wind.png` - Wind field (12 UTC init)
- `ian_init18_landfall_msl.png` - MSL field (18 UTC init)
- `ian_init18_landfall_wind.png` - Wind field (18 UTC init)
- `ian_stage2_init_time_results.json` - Summary statistics

**Total**: ~20 figures + 2 JSON summary files (matching Sandy analysis)

---

## Next Steps

1. ✅ Create event folder: `/research/TC/2022_Ian/`
2. ✅ Create experimental design: `IAN_EXPERIMENTAL_DESIGN.md`
3. ⬜ Create data workflow: `IAN_DATA_WORKFLOW.md`
4. ⬜ Download ERA5 data (combined + landfall files)
5. ⬜ Adapt Stage 1 script: `ian_stage1_lead_day.py`
6. ⬜ Adapt Stage 2 script: `ian_stage2_init_time.py`
7. ⬜ Execute Stage 1 analysis
8. ⬜ Execute Stage 2 analysis
9. ⬜ Document results: `IAN_RESULTS.md`
10. ⬜ Update master research plan

---

**Notes**:
- This is an **out-of-sample** case (2022 > 2020 Aurora training cutoff) → scientifically valid
- Ian tests Aurora's rapid intensification prediction capability
- Compact, intense system vs Sandy's large hybrid → different challenge
- Results will provide key comparison point for paper's TC section

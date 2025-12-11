# Cyclone Amphan 2020 - Experimental Design

**Event**: Cyclone Amphan (2020)
**Target**: May 20, 2020 12:00 UTC (Bangladesh landfall)
**Model**: Aurora 0.25° Pretrained
**Basin**: North Indian Ocean (Bay of Bengal)
**Status**: In-sample (2020, last year of Aurora's 1979-2020 training period)

---

## Event Overview

### Cyclone Amphan Characteristics

**Track Summary**:
- **Genesis**: May 15, 2020 06:00 UTC (Bay of Bengal, near 9.5°N, 87.5°E)
- **Peak Intensity**: May 18, 2020 12:00 UTC (125 kt, 926 mb - Super Cyclonic Storm)
- **Primary Landfall**: May 20, 2020 12:00 UTC (Bangladesh, near 22.1°N, 88.4°E) ← **TARGET**
- **Dissipation**: May 21, 2020 12:00 UTC

**Notable Track Features**:
1. Genesis in central Bay of Bengal (May 15 06:00 UTC)
2. Rapid intensification to super cyclone (May 16-18: 35 kt → 125 kt)
3. Slight westward drift during peak intensity (May 18)
4. Northward acceleration toward Bangladesh (May 19-20)
5. Weakening before landfall (~85 kt at landfall vs 125 kt peak)

**Why This Event?**:
- In-sample boundary test (2020, last year of Aurora training)
- Most powerful cyclone in Bay of Bengal since Cyclone Sidr (2007)
- Clean landfall target on 6-hourly grid (12:00 UTC)
- Tests Aurora's North Indian Ocean TC skill (vs Atlantic/Pacific basins)
- Rapid intensification challenge in confined basin
- Pre-monsoon cyclone (different environment from post-monsoon)

---

## Target Selection

### Primary Target: May 20, 2020 12:00 UTC

**Landfall Position**: ~22.1°N, 88.4°E (Bangladesh, near West Bengal border)

**Rationale**:
- Most operationally significant landfall (Bangladesh/India population center)
- On 6-hourly grid (12:00 UTC) - perfect for Aurora
- Clear verification target for field comparisons
- Follows Sandy/Ian/Hinnamnor methodology (target = landfall time)

**Storm Characteristics at Target**:
- Intensity: ~85 kt, ~957 mb (weakened from peak 125 kt)
- Size: Large circulation, well-defined
- Motion: N/NNE at ~25-30 km/h
- Environment: Weakening due to land interaction

---

## Stage 1: Lead Time Assessment

**Question**: How far in advance can Aurora predict Amphan's Bangladesh landfall?

**Approach**: Variable initialization date, fixed target (May 20, 2020 12:00 UTC)

### Configuration

| Lead Time | Init Date & Time | Storm Stage | IBTrACS Position | Forecast Steps |
|-----------|------------------|-------------|------------------|----------------|
| **1-day** | May 19 12:00 UTC | Approaching Bangladesh, weakening | 17.3°N, 87.1°E | 3 steps (24h) |
| **3-day** | May 17 12:00 UTC | Rapid intensification phase | 11.9°N, 86.2°E | 11 steps (72h) |
| **5-day** | May 15 12:00 UTC | Genesis day, forming | 9.5°N, 87.0°E | 19 steps (120h) |
| **7-day** | May 13 12:00 UTC | Pre-genesis environment | 9.5°N, 87.5°E* | 27 steps (168h) |

**Target for All**: May 20, 2020 12:00 UTC (Bangladesh landfall)

**Note**: *7-day lead is pre-genesis (uses May 15 06:00 genesis position for tracker) - tests Aurora's ability to predict cyclone development from pre-genesis environment (similar to Ian's approach).

### Expected Challenges by Lead Time

**1-Day Lead** (May 19 12:00 UTC):
- Storm already approaching Bangladesh
- Weakening phase from peak intensity
- Short forecast, high accuracy expected

**3-Day Lead** (May 17 12:00 UTC):
- During rapid intensification phase
- Must predict peak intensity timing
- Critical for operational warning lead time
- Most interesting for initialization sensitivity (Stage 2)

**5-Day Lead** (May 15 12:00 UTC):
- Genesis day initialization
- Must predict full intensification cycle
- Tests Aurora's genesis → landfall skill
- Moderate track uncertainty expected

**7-Day Lead** (May 13 12:00 UTC):
- Pre-genesis environment (2 days before formation)
- Must predict cyclogenesis, intensification, and landfall
- Extremely challenging: tests Aurora's development prediction
- Uses genesis position for tracker (like Ian pre-genesis case)

---

## Stage 2: Initialization Time Sensitivity

**Question**: How sensitive is Aurora's Amphan prediction to initialization time of day?

**Approach**: Fixed lead time (based on Stage 1 best performance), variable initialization time

### Anticipated Configuration (3-Day Lead)

Based on Sandy/Ian/Hinnamnor results (3-day typically optimal for sensitivity testing):

**Initialization Date**: May 17, 2020 (3 days before landfall)

| Init Time | Init Date & Time | IBTrACS Position | Forecast Steps | Forecast Hours |
|-----------|------------------|------------------|----------------|----------------|
| **00 UTC** | May 17 00:00 UTC | 11.2°N, 86.1°E | 14 steps | 90h |
| **06 UTC** | May 17 06:00 UTC | 11.5°N, 86.2°E | 13 steps | 84h |
| **12 UTC** | May 17 12:00 UTC | 11.9°N, 86.2°E | 12 steps | 78h |
| **18 UTC** | May 17 18:00 UTC | 12.5°N, 86.4°E | 11 steps | 72h |

**Target for All**: May 20, 2020 12:00 UTC (Bangladesh landfall)

**Note**: Final Stage 2 configuration determined after Stage 1 analysis.

### Alternative Configurations

**If 1-Day Lead Optimal** (May 19 init):
- 00, 06, 12, 18 UTC on May 19
- Very short lead but high accuracy expected

**If 5-Day Lead Optimal** (May 15 init):
- 00, 06, 12, 18 UTC on May 15
- Genesis day - interesting sensitivity test for cyclone development

---

## Evaluation Metrics

### Track-Based Metrics (Tracker-Derived)

**Pre-Landfall Ocean Phase**:
- Track position error (km) at 24h, 48h, 72h lead times
- Mean track error over entire forecast
- Track error evolution vs lead time
- Position uncertainty (spread across init times)

**Landfall Metrics**:
- Landfall location error (km) - predicted vs observed (~22.1°N, 88.4°E)
- Landfall timing error (hours)
- Track continuity during northward acceleration (May 19-20)

### Field-Based Metrics (Direct Comparison at Landfall)

**Primary Variables** (at May 20, 2020 12:00 UTC):

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
- Latitude: 15-30°N (Bangladesh + Bay of Bengal)
- Longitude: 80-95°E (Bay of Bengal + Bangladesh/India)
- Captures approach and landfall area

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
- `v`: V-component
- `q`: Specific humidity
- `z`: Geopotential height

**Static** (already available):
- `lsm`: Land-sea mask (0.25° resolution)
- `slt`: Soil type (0.25° resolution)
- `z`: Surface geopotential/topography (0.25° resolution)

### File Strategy

**Combined Initialization File** (for forecasts):
- **Filename**: `amphan_2020_surface_combined.nc`, `amphan_2020_atmospheric_combined.nc`
- **Time Range**: May 13, 2020 00:00 UTC → May 20, 2020 06:00 UTC
- **Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)
- **Purpose**: Contains all initialization times for Stage 1 and Stage 2

**Separate Verification File** (for landfall):
- **Filename**: `amphan_2020_surface_landfall.nc`, `amphan_2020_atmospheric_landfall.nc`
- **Time Range**: May 20, 2020 12:00 UTC (single timestep)
- **Purpose**: ERA5 "truth" for landfall field comparisons

**IBTrACS Observational Data**:
- **Source**: https://ncics.org/ibtracs/index.php?name=v04r01-2020136N10088
- **Storm ID**: 2020136N10088
- **Time Range**: May 15, 2020 → May 21, 2020
- **Format**: Added to TC_utils.py hardcoded tracks (6-hourly from 3-hourly source)
- **Purpose**: Best track data for verification

---

## Key Differences from Other TC Cases

| Aspect | Sandy 2012 | Ian 2022 | Hinnamnor 2022 | Amphan 2020 |
|--------|------------|----------|----------------|-------------|
| **Sample Status** | In-sample | Out-of-sample | Out-of-sample | In-sample (boundary) |
| **Basin** | Atlantic | Atlantic/Gulf | Western Pacific | North Indian Ocean |
| **Peak Intensity** | 940 mb, 100 kt | 937 mb, 140 kt | 910 mb, 145 kt | 926 mb, 125 kt |
| **Size** | Very large | Compact | Large | Large |
| **Track Pattern** | NE then NW hook | NW then N | W then sharp N | N then NNE |
| **Landfall Intensity** | Hybrid, 940 mb | Major, ~940 mb | Weakened, ~970 mb | Weakened, ~957 mb |
| **Intensity Change** | Gradual hybrid | Rapid intensification | RI then weakening | RI then weakening |
| **Unusual Feature** | ET transition | RI in Gulf | Stalling + recurvature | Pre-monsoon RI |
| **Max Lead Time** | 7 days | 7 days (pre-genesis) | 7 days (peak) | 7 days (pre-genesis) |
| **Key Challenge** | Track anomaly | RI timing | Weakening + recurvature | Genesis + RI |
| **X-axis Hours** | 00, 12 UTC | 06, 18 UTC | 18 UTC (Stage 1) | 00, 12 UTC |

---

## Success Criteria

### Minimum Acceptable Performance
- 1-day lead: <100 km landfall error
- 3-day lead: <300 km landfall error
- 5-day lead: <500 km landfall error
- 7-day lead: <700 km landfall error (very challenging, pre-genesis)
- Track captures northward acceleration (May 19-20)

### Excellent Performance
- 1-day lead: <50 km landfall error
- 3-day lead: <200 km landfall error
- 5-day lead: <400 km landfall error
- 7-day lead: <600 km landfall error
- Correctly predicts rapid intensification timing
- Captures weakening trend before landfall

### Physical Consistency Checks
- MSL minimum 950-965 mb at landfall (realistic weakened intensity)
- Wind speed >25 m/s at landfall (cyclone force, weakened from peak)
- Track shows clear northward acceleration (May 19-20)
- Track remains continuous (no jumps)

---

## Expected Aurora Challenges

Based on Sandy/Ian/Hinnamnor results and Amphan's unique characteristics:

**1. Pre-Genesis Initialization** (7-day lead):
- Amphan formed May 15 06:00 UTC
- 7-day init (May 13 12:00) is pre-genesis
- Must predict cyclogenesis from environmental conditions
- Similar to Ian's pre-genesis challenge

**2. Rapid Intensification** (May 16-18):
- 35 kt → 125 kt in ~48 hours
- Peak super cyclone intensity May 18 12:00 UTC
- Aurora may underpredict peak intensity (as seen in Ian/Hinnamnor)
- Critical for 3-day and 5-day leads

**3. Weakening Trend** (May 18 → May 20):
- 125 kt → 85 kt before landfall
- Land interaction + shelf waters
- Aurora may overpredict intensity at landfall
- Expect MSL bias (too low/too strong)

**4. Bay of Bengal Basin**:
- Different from Atlantic (Sandy/Ian) and Pacific (Hinnamnor)
- Confined basin with complex land boundaries
- Tests Aurora's basin generalization to North Indian Ocean
- Different environmental characteristics (pre-monsoon)

**5. In-Sample Boundary Case**:
- 2020 is last year of Aurora training
- May show better performance than out-of-sample events
- Important for understanding temporal generalization

**6. Track Complexity**:
- Slight westward drift at peak (May 18)
- Northward acceleration (May 19-20)
- Must predict timing of northward turn
- Critical for landfall location accuracy

---

## Analysis Timeline

1. ✅ **IBTrACS Data**: Add Amphan track to TC_utils.py
2. ✅ **Directory Setup**: Create 2020_Amphan folder structure
3. ✅ **Scripts Created**: download_amphan_complete.py, combine_amphan_data.py
4. ✅ **Stage 1 Script**: amphan_stage1_lead_day.py
5. ✅ **Stage 2 Script**: amphan_stage2_init_time.py
6. ⬜ **ERA5 Download**: Download combined (May 13-20) and landfall (May 20 12Z) files
7. ⬜ **Stage 1 Execution**: Run 1, 3, 5, 7-day lead forecasts
8. ⬜ **Stage 1 Analysis**: Analyze results, identify best lead time
9. ⬜ **Stage 2 Execution**: Run 4 initialization times at optimal lead
10. ⬜ **Stage 2 Analysis**: Analyze initialization sensitivity
11. ⬜ **Documentation**: Complete `AMPHAN_RESULTS.md` with findings
12. ⬜ **Paper Integration**: Add to multi-event, multi-basin comparison

---

## Output Products

### Stage 1 Outputs (~10 figures + results)
- `amphan_stage1_tracks.png` - Track comparison (4 lead times)
- `amphan_stage1_errors.png` - Error evolution vs lead time
- `amphan_1day_landfall_msl.png` - MSL field at landfall (1-day)
- `amphan_1day_landfall_wind.png` - Wind field at landfall (1-day)
- `amphan_3day_landfall_msl.png` - MSL field at landfall (3-day)
- `amphan_3day_landfall_wind.png` - Wind field at landfall (3-day)
- `amphan_5day_landfall_msl.png` - MSL field at landfall (5-day)
- `amphan_5day_landfall_wind.png` - Wind field at landfall (5-day)
- `amphan_7day_landfall_msl.png` - MSL field at landfall (7-day)
- `amphan_7day_landfall_wind.png` - Wind field at landfall (7-day)
- `amphan_stage1_lead_time_results.pkl` - Saved results

### Stage 2 Outputs (~10 figures + results)
- `amphan_stage2_init_tracks.png` - Combined track comparison (4 init times)
- `amphan_stage2_init_errors.png` - Error comparison across init times
- `amphan_init00_landfall_msl.png` - MSL field (00 UTC init)
- `amphan_init00_landfall_wind.png` - Wind field (00 UTC init)
- `amphan_init06_landfall_msl.png` - MSL field (06 UTC init)
- `amphan_init06_landfall_wind.png` - Wind field (06 UTC init)
- `amphan_init12_landfall_msl.png` - MSL field (12 UTC init)
- `amphan_init12_landfall_wind.png` - Wind field (12 UTC init)
- `amphan_init18_landfall_msl.png` - MSL field (18 UTC init)
- `amphan_init18_landfall_wind.png` - Wind field (18 UTC init)
- `amphan_stage2_init_time_results.pkl` - Saved results

### CSV Export
- All results automatically exported to `/research/TC/TC_result_metrics.csv`
- Includes: TC_Name, Stage, Lead_Day_or_Init_Time, Track_Error_24h_km, Track_Error_48h_km, Track_Error_72h_km, MSL_Error_hPa, Wind_Error_ms, Position_Error_Landfall_km

**Total**: ~20 figures + CSV export (matching Sandy/Ian/Hinnamnor)

---

## Research Significance

### Multi-Basin Comparison

Amphan adds North Indian Ocean to the basin diversity:
- **Atlantic**: Sandy 2012 (in-sample)
- **Atlantic/Gulf**: Ian 2022 (out-of-sample)
- **Western Pacific**: Hinnamnor 2022 (out-of-sample)
- **North Indian Ocean**: Amphan 2020 (in-sample boundary) ← **NEW**

### In-Sample Boundary Test

- 2020 is the last year of Aurora's training period (1979-2020)
- Tests temporal generalization at training boundary
- Comparison with out-of-sample events (Ian, Hinnamnor) will reveal:
  - Whether 2020 shows better performance than 2022 events
  - Aurora's ability to predict events near training cutoff
  - Importance of training data recency

### Pre-Genesis Development

- Like Ian, 7-day lead is pre-genesis
- Tests Aurora's cyclogenesis prediction from environmental conditions
- Different basin (Bay of Bengal vs Caribbean)
- Adds to sample size for pre-genesis prediction assessment

### Rapid Intensification

- Amphan's RI (35 kt → 125 kt in 48h) adds to RI case study
- Comparison with Ian's RI will inform Aurora's RI prediction skill
- Different basin and environmental conditions

---

## Next Steps

1. ✅ Create event folder: `/research/TC/2020_Amphan/`
2. ✅ Create experimental design: `AMPHAN_EXPERIMENTAL_DESIGN.md`
3. ✅ Add Amphan track to `TC_utils.py`
4. ✅ Create download script: `download_amphan_complete.py`
5. ✅ Create combine script: `combine_amphan_data.py`
6. ✅ Create Stage 1 script: `amphan_stage1_lead_day.py`
7. ✅ Create Stage 2 script: `amphan_stage2_init_time.py`
8. ⬜ Download ERA5 data (combined + landfall files)
9. ⬜ Execute Stage 1 analysis
10. ⬜ Execute Stage 2 analysis
11. ⬜ Document results: `AMPHAN_RESULTS.md`
12. ⬜ Update master research plan

---

**Notes**:
- **In-sample boundary** case (2020, last year of training) → tests temporal generalization
- **North Indian Ocean basin** → tests Aurora's basin generalization (4th basin)
- **Pre-genesis initialization** (7-day) → tests cyclogenesis prediction (like Ian)
- **Rapid intensification** → tests Aurora's RI skill in confined Bay of Bengal
- **Multi-basin comparison** with Sandy/Ian/Hinnamnor will provide key insights for paper
- **X-axis hours**: 00 UTC and 12 UTC (like Sandy, different from Ian/Hinnamnor)

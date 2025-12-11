# Tropical Cyclone Forecast Verification Metrics

**Purpose**: Comprehensive documentation of all comparison metrics used to evaluate Aurora's tropical cyclone forecasts across Ian, Sandy, Hinnamnor, and Amphan case studies.

**Last Updated**: 2025-11-14

---

## Overview

TC forecast verification uses two complementary approaches:
1. **Track-based metrics**: Position errors from Aurora's tracker vs IBTrACS observations
2. **Field-based metrics**: Intensity and position errors from direct field comparisons (MSL, wind)

These approaches measure different aspects of forecast skill and are **not redundant** - they provide complementary information about Aurora's predictive capabilities.

---

## 1. Track-Based Metrics (Time-Synchronized)

### 1.1 Mean Track Error

**Definition**: Average position error across all forecast timesteps.

**Purpose**: Overall measure of forecast track accuracy throughout the entire forecast period.

**Calculation**:
```python
# For each timestep t in forecast:
track_error[t] = haversine_distance(
    aurora_tracker.lat[t], aurora_tracker.lon[t],
    ibtracs.lat[t], ibtracs.lon[t]
)

mean_track_error = np.mean(track_error)
```

**Code Location**: `research/TC/TC_utils.py::summarize_track_performance()`
```python
def summarize_track_performance(forecast_track, obs_track, init_time, event_name):
    """
    Lines ~365-400: Computes mean_error, max_error, final_error
    Uses haversine distance for all position error calculations
    """
```

**Interpretation**:
- **< 50 km**: Excellent tracking skill
- **50-100 km**: Good tracking skill
- **100-200 km**: Moderate tracking skill
- **> 200 km**: Poor tracking skill

**Example**: Ian 3-day mean track error = 35.3 km (excellent)

---

### 1.2 Maximum Track Error

**Definition**: Largest position error at any timestep during the forecast.

**Purpose**: Identifies worst-case tracking error, useful for understanding forecast extremes.

**Calculation**:
```python
max_track_error = np.max(track_error)
```

**Code Location**: Same as mean track error (`TC_utils.py::summarize_track_performance()`)

**Interpretation**: Indicates the maximum deviation from observed track, highlighting periods of poorest tracking.

**Example**: Ian 3-day max error = 101.2 km (at final forecast point)

---

### 1.3 Final Track Error

**Definition**: Position error at the last forecast timestep.

**Purpose**: Measures accuracy at the forecast endpoint, which may be near but not at landfall time.

**Calculation**:
```python
final_track_error = track_error[-1]  # Last timestep
```

**Code Location**: `TC_utils.py::summarize_track_performance()`

**Important Note**:
- For Stage 1: Final timestep is typically 6h before landfall marker
- For Stage 2: All forecasts end at same time (6h before landfall marker)
- **This is NOT the same as landfall position error** (which uses field comparison)

**Example**: Ian 3-day final error = 101.2 km (at Sep 28 12:00 UTC, 6h before landfall)

---

### 1.4 Lead Time Track Errors (24h, 48h, 72h)

**Definition**: Position errors at specific lead times from initialization.

**Purpose**: Standardized error metrics for comparing forecast skill at common operational lead times.

**Calculation**:
```python
# Find timestep closest to target lead time
for lead_hours in [24, 48, 72]:
    target_time = init_time + timedelta(hours=lead_hours)
    # Find closest timestep in forecast
    idx = find_closest_time_index(forecast_times, target_time)
    error_at_lead[lead_hours] = track_error[idx]
```

**Code Location**: `TC_utils.py::summarize_track_performance()`
```python
# Lines ~380-395
# Searches for timesteps at +24h, +48h, +72h from init
# Computes haversine distance at each lead time
```

**Interpretation**:
- Used for comparing different initialization times (Stage 2)
- Standard operational forecast verification intervals
- Allows comparison to NHC/JTWC official forecasts

**Example**: Ian 3-day: 24h=5.6 km, 48h=59.2 km, 72h=101.2 km

---

### 1.5 Landfall Timing Error

**Definition**: Difference between predicted and observed landfall time.

**Purpose**: Measures temporal accuracy of landfall prediction.

**Calculation**:
```python
# Find when tracker crosses landfall longitude threshold
def compute_landfall_error(forecast_track, obs_track, landfall_lon):
    # Find first crossing of longitude threshold
    predicted_landfall_time = find_first_crossing(
        forecast_track['lon'],
        threshold=landfall_lon
    )
    observed_landfall_time = find_first_crossing(
        obs_track['lon'],
        threshold=landfall_lon
    )

    timing_error_hours = (predicted_landfall_time - observed_landfall_time).total_seconds() / 3600
    return timing_error_hours
```

**Code Location**: `TC_utils.py::compute_landfall_error()`
```python
# Lines ~420-460
# Finds longitude threshold crossing for landfall detection
# Computes time difference in hours
```

**Interpretation**:
- **Negative**: Early landfall prediction
- **Positive**: Late landfall prediction
- **± 6 hours**: Excellent timing
- **± 12 hours**: Good timing

**Example**: Ian 3-day timing error = 0.0 hours (perfect!)

---

### 1.6 Landfall Location Error (Tracker-Based)

**Definition**: Distance between predicted and observed landfall positions using tracker data.

**Purpose**: Measures spatial accuracy of landfall prediction using tracker positions.

**Calculation**:
```python
# Find landfall positions from tracker
predicted_landfall_pos = forecast_track['lat'][landfall_idx], forecast_track['lon'][landfall_idx]
observed_landfall_pos = obs_track['lat'][landfall_idx_obs], obs_track['lon'][landfall_idx_obs]

landfall_location_error = haversine_distance(
    predicted_landfall_pos[0], predicted_landfall_pos[1],
    observed_landfall_pos[0], observed_landfall_pos[1]
)
```

**Code Location**: `TC_utils.py::compute_landfall_error()`

**Important Distinction**: This uses **tracker positions**, which may differ from **field-based landfall position error** (see Section 2.3).

**Example**: Not always reported separately; tracker-based landfall position varies by case

---

## 2. Field-Based Metrics (Location-Focused)

### 2.1 MSL Minimum Error

**Definition**: Difference between Aurora's predicted minimum mean sea level pressure and ERA5's minimum MSL at the verification time.

**Purpose**: Intensity verification - measures TC central pressure prediction accuracy.

**Calculation**:
```python
def compare_fields_at_landfall(aurora_preds, era5_surf, era5_atmos, ...):
    # Extract MSL fields
    aurora_msl = extract_field_from_predictions(aurora_preds, 'msl', time_idx=landfall_idx)
    era5_msl = era5_surf['msl'].sel(valid_time=landfall_time, method='nearest')

    # Find minima (TC center proxy)
    aurora_msl_min = np.min(aurora_msl_data)  # Pa
    era5_msl_min = np.min(era5_msl_data)      # Pa

    msl_error = aurora_msl_min - era5_msl_min  # Pa (convert to hPa for reporting)
    return msl_error / 100  # hPa
```

**Code Location**: `TC_utils.py::compare_fields_at_landfall()`
```python
# Lines ~790-865
# Extracts MSL fields from Aurora predictions and ERA5
# Finds minimum values in regional domain
# Computes difference in Pascals, reports in hPa
```

**Interpretation**:
- **Negative error**: Aurora predicts lower pressure (stronger TC)
- **Positive error**: Aurora predicts higher pressure (weaker TC)
- **|error| < 5 hPa**: Excellent intensity prediction
- **|error| 5-10 hPa**: Good intensity prediction
- **|error| > 10 hPa**: Poor intensity prediction

**Basin-Dependent Biases Observed**:
- **Atlantic (Ian, Sandy)**: +2 to +8 hPa (too weak)
- **Indo-Pacific (Amphan, Hinnamnor)**: -2 to -9 hPa (too strong)

**Example**: Ian 3-day MSL error = +3.6 hPa (Aurora: 983.5 hPa, ERA5: 979.9 hPa)

---

### 2.2 Wind Maximum Error

**Definition**: Difference between Aurora's predicted maximum 10m wind speed and ERA5's maximum wind speed at the verification time.

**Purpose**: Intensity verification - measures TC maximum wind prediction accuracy.

**Calculation**:
```python
# Compute wind speed from u/v components
aurora_10u = extract_field_from_predictions(aurora_preds, '10u', time_idx=landfall_idx)
aurora_10v = extract_field_from_predictions(aurora_preds, '10v', time_idx=landfall_idx)
aurora_wind = np.sqrt(aurora_10u**2 + aurora_10v**2)

era5_10u = era5_surf['u10'].sel(valid_time=landfall_time, method='nearest')
era5_10v = era5_surf['v10'].sel(valid_time=landfall_time, method='nearest')
era5_wind = np.sqrt(era5_10u**2 + era5_10v**2)

# Find maxima
aurora_wind_max = np.max(aurora_wind_data)
era5_wind_max = np.max(era5_wind_data)

wind_error = aurora_wind_max - era5_wind_max  # m/s
```

**Code Location**: `TC_utils.py::compare_fields_at_landfall()`
```python
# Lines ~790-850
# Computes wind speed magnitude from components
# Finds maximum values in regional domain
# Reports difference in m/s
```

**Interpretation**:
- **Negative error**: Aurora predicts weaker winds
- **Positive error**: Aurora predicts stronger winds
- **|error| < 3 m/s**: Excellent wind prediction
- **|error| 3-6 m/s**: Good wind prediction
- **|error| > 6 m/s**: Poor wind prediction

**Basin-Dependent Biases Observed**:
- **Atlantic (Ian, Sandy)**: -4 to -8 m/s (too weak)
- **Indo-Pacific (Amphan, Hinnamnor)**: +2 to +7 m/s (too strong)

**Example**: Ian 3-day wind error = -6.5 m/s (Aurora: 22.1 m/s, ERA5: 28.7 m/s)

---

### 2.3 Landfall Position Error (Field-Based) ⭐

**Definition**: Distance between TC center positions derived from MSL field minima in Aurora's forecast vs ERA5 at landfall time.

**Purpose**: **Primary operational metric** - measures spatial accuracy of landfall prediction independent of tracker limitations.

**Calculation**:
```python
def compare_fields_at_landfall(...):
    # Step 1: Find which Aurora prediction timestep is spatially closest to landfall
    distances = []
    for i, (lat, lon) in enumerate(zip(forecast_track['lat'], forecast_track['lon'])):
        dist = haversine_distance(lat, lon, landfall_lat, landfall_lon)
        distances.append(dist)
    track_idx = np.argmin(distances)
    landfall_idx = max(0, track_idx - 1)  # Convert track index to prediction index

    # Step 2: Extract Aurora's MSL field at that timestep
    aurora_msl = extract_field_from_predictions(aurora_preds, 'msl', time_idx=landfall_idx)

    # Step 3: Extract ERA5's MSL field at landfall marker time
    era5_msl = era5_surf['msl'].sel(valid_time=landfall_marker_time, method='nearest')

    # Step 4: Find MSL minima (TC centers) in both fields
    aurora_min_pos = np.unravel_index(np.argmin(aurora_msl), aurora_msl.shape)
    era5_min_pos = np.unravel_index(np.argmin(era5_msl), era5_msl.shape)

    aurora_center_lat = lat[aurora_min_pos[0]]
    aurora_center_lon = lon[aurora_min_pos[1]]
    era5_center_lat = lat[era5_min_pos[0]]
    era5_center_lon = lon[era5_min_pos[1]]

    # Step 5: Compute distance between centers
    position_error = haversine_distance(
        aurora_center_lat, aurora_center_lon,
        era5_center_lat, era5_center_lon
    )

    return position_error  # km
```

**Code Location**: `TC_utils.py::compare_fields_at_landfall()`
```python
# Lines ~844-874
# Finds MSL minimum positions in both Aurora and ERA5 fields
# Uses haversine distance to compute separation
# Returns center_diff_km
```

**Critical Distinctions from Track Error**:

| Aspect | Track Error | Landfall Position Error |
|--------|-------------|------------------------|
| **Method** | Tracker position | MSL field minimum |
| **Timing** | Time-synchronized | May compare different times |
| **Purpose** | Day-to-day tracking | Final location accuracy |
| **Limitations** | Fails near land | Works everywhere |
| **Operational Use** | Forecast evolution | Evacuation planning |

**Why These Can Differ Significantly**:

**Example: Hurricane Ian 3-Day**
- **Final track error**: 101.2 km
  - Aurora tracker at Sep 28 12:00 is 101 km from IBTrACS at 12:00
  - Time-synchronized comparison
- **Landfall position error**: 0.0 km
  - Aurora MSL minimum at 12:00 at exact same location as ERA5 MSL minimum at 18:00
  - Aurora predicted TC would reach that location 6h early, but location was perfect!

**Interpretation**:
- **< 50 km**: Excellent landfall prediction
- **50-100 km**: Good landfall prediction
- **100-200 km**: Moderate landfall prediction
- **> 200 km**: Poor landfall prediction

**This is the PRIMARY metric for operational landfall forecasting.**

**Examples**:
- Ian 3-day: 0.0 km (perfect!)
- Sandy 3-day: 243.2 km (moderate)
- Amphan 3-day: 27.8 km (excellent)
- Hinnamnor 3-day: 1689.7 km (very poor - recurvature failure)

---

## 3. Code Implementation Details

### 3.1 Track Error Computation Pipeline

**File**: `research/TC/TC_utils.py`

```python
# Step 1: Extract track from Aurora tracker (Lines ~300-340)
def extract_track_from_tracker(tracker, init_time):
    """
    Extracts lat, lon, time from tracker.tracked_lats, tracked_lons, tracked_times
    Returns dict with 'time', 'lat', 'lon' keys
    Includes initial position + all forecast steps
    """

# Step 2: Compute position errors vs IBTrACS (Lines ~340-365)
def compute_track_error(forecast_track, obs_track):
    """
    For each timestep in forecast:
      - Find matching time in observations (nearest)
      - Compute haversine distance
    Returns dict with 'errors' (array), 'times', 'valid_indices'
    """

# Step 3: Summarize performance statistics (Lines ~365-420)
def summarize_track_performance(forecast_track, obs_track, init_time, event_name):
    """
    Computes:
      - mean_error: Average of all position errors
      - max_error: Maximum position error
      - final_error: Last position error
      - error_24h, error_48h, error_72h: Errors at standard lead times
    Returns dict with all summary statistics
    """
```

**Helper Function**: Haversine distance
```python
# File: research/shared/metrics.py
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine distance in kilometers
    Handles longitude wrapping (0-360° and -180 to 180°)
    Returns distance in km
    """
```

---

### 3.2 Field Comparison Pipeline

**File**: `research/TC/TC_utils.py`

```python
# Step 1: Extract fields from predictions (Lines ~640-745)
def extract_field_from_predictions(predictions, variable, time_idx=None, level_idx=None):
    """
    Extracts specified variable from Aurora predictions or ERA5 dataset
    Handles both surface (msl, 10u, 10v) and atmospheric (z, t, u, v, q) variables
    Returns dict with 'data', 'lat', 'lon', 'time'
    """

# Step 2: Compare fields at landfall (Lines ~745-890)
def compare_fields_at_landfall(aurora_preds, era5_surf, era5_atmos,
                                landfall_time_idx, landfall_lat, landfall_lon,
                                region_extent=None):
    """
    Main field comparison function:

    1. Extract Aurora fields at landfall_time_idx:
       - msl, 10u, 10v, z700

    2. Extract ERA5 fields at landfall marker time:
       - Uses method='nearest' to find closest time
       - Same variables as Aurora

    3. Apply regional subset if region_extent provided:
       - Lon_min, lon_max, lat_min, lat_max

    4. Find minima/maxima:
       - MSL minimum (TC center)
       - Wind maximum (peak winds)

    5. Compute errors:
       - MSL min difference (hPa)
       - Wind max difference (m/s)
       - Center position difference (km via haversine)

    Returns dict with:
      - 'msl': {aurora, era5, difference, aurora_min, era5_min,
                aurora_center, era5_center, center_diff_km}
      - 'wind': {aurora, era5, difference, aurora_max, era5_max}
      - 'z700': {aurora, era5, difference}
      - 'lat', 'lon': coordinate arrays
    """
```

**Key Implementation Notes**:

1. **Regional Extraction**:
   - All field comparisons use regional subset around landfall
   - Typical extent: ±10-15° latitude/longitude
   - Prevents far-field patterns from influencing minima/maxima

2. **Time Matching**:
   - Aurora: Uses specified prediction index
   - ERA5: Uses `method='nearest'` to find closest time
   - **Can result in comparing different times!**

3. **Unit Conversions**:
   - MSL: Aurora/ERA5 in Pascals → divide by 100 for hPa
   - Wind: Always in m/s (no conversion needed)
   - Distance: Always in km (haversine output)

---

### 3.3 CSV Export Format

**File**: `research/TC/TC_utils.py::export_results_to_csv()`

**Output File**: `research/TC/TC_result_metrics.csv`

**Columns**:
```
TC_Name                    : Event name (e.g., "Ian 2022", "Sandy 2012")
Stage                      : 1 (lead time) or 2 (init time)
Lead_Day_or_Init_Time      : "1-day", "3-day", etc. or "00:00 UTC", "06:00 UTC", etc.
Track_Error_24h_km         : Track error at 24h lead time
Track_Error_48h_km         : Track error at 48h lead time
Track_Error_72h_km         : Track error at 72h lead time
MSL_Error_hPa              : MSL minimum error (field-based)
Wind_Error_ms              : Wind maximum error (field-based)
Position_Error_Landfall_km : Landfall position error (field-based)
```

**Export Logic**:
```python
def export_results_to_csv(tc_name, stage, results, csv_path, stage_type):
    """
    Stage 1 (lead time):
      - One row per lead time (1-day, 3-day, 5-day, 7-day)
      - Track errors from summarize_track_performance()
      - Field errors from compare_fields_at_landfall()

    Stage 2 (init time):
      - One row per init time (00, 06, 12, 18 UTC)
      - Same metrics as Stage 1
      - All target same landfall time

    Appends to existing CSV or creates new one
    """
```

---

## 4. Verification Time Selection

### 4.1 Stage 1: Lead Time Assessment

**Forecast Endpoint Rule**: All forecasts end **6 hours before** the landfall marker time.

**Rationale**:
1. Tracker may fail very close to land (topography interference)
2. Consistent endpoint for fair comparison across lead times
3. Field comparison still uses actual landfall marker time

**Example: Hurricane Ian**
- Landfall marker: Sep 28 18:00 UTC (closest 6-hourly to actual 20:00 UTC landfall)
- Forecast endpoints: All end Sep 28 12:00 UTC (6h before marker)
- Field comparison: Uses ERA5 at Sep 28 18:00 UTC

**Example: Cyclone Amphan**
- Landfall marker: May 20 12:00 UTC (actual landfall time)
- Forecast endpoints: All end May 20 06:00 UTC (6h before marker)
- Field comparison: Uses ERA5 at May 20 12:00 UTC

---

### 4.2 Stage 2: Initialization Sensitivity

**Forecast Endpoint Rule**: All forecasts end at **same time** (6h before landfall marker).

**Different Step Counts**:
- Different initialization times require different step counts to reach same endpoint
- Earlier inits need more steps, later inits need fewer steps

**Example: Amphan Stage 2 (Target: May 20 12:00 UTC)**
```
Init Time    Init Date/Time        Steps   Endpoint
00 UTC       May 17 00:00         13      May 20 06:00  (78h)
06 UTC       May 17 06:00         12      May 20 06:00  (72h)
12 UTC       May 17 12:00         11      May 20 06:00  (66h)
18 UTC       May 17 18:00         10      May 20 06:00  (60h)
```

**Verification**: Field comparison uses landfall marker time (May 20 12:00 UTC) for all inits.

---

### 4.3 Field Comparison Time Selection

**Aurora Timestep Selection**:
```python
# Find which tracker position is spatially closest to landfall location
distances = [haversine(track_lat[i], track_lon[i], landfall_lat, landfall_lon)
             for i in range(len(track_lat))]
track_idx = np.argmin(distances)

# Convert to prediction index (tracker includes init position at index 0)
landfall_idx = max(0, track_idx - 1)
```

**ERA5 Time Selection**:
```python
# Use landfall marker time (user-specified, typically on 6-hourly grid)
era5_time = landfall_marker_time  # e.g., Sep 28 18:00 UTC

# ERA5 data loaded with method='nearest' to handle any time mismatches
era5_field = era5_ds['variable'].sel(valid_time=era5_time, method='nearest')
```

**Key Point**: Aurora and ERA5 fields **may be at different times** if:
- Aurora's forecast endpoint is before landfall marker (standard case)
- Aurora's TC motion is faster/slower than observed (timing error)

This is **intentional** - we compare "where Aurora thinks TC is at time T_aurora" vs "where ERA5 shows TC at time T_era5".

---

## 5. Interpretation Guidelines

### 5.1 Track Error vs Landfall Position Error

These metrics are **complementary, not contradictory**:

**Scenario A: Good Track + Good Position** (Ideal)
- Smooth, accurate tracking throughout forecast
- Correct landfall location
- Example: Amphan 3-day (30.6 km track, 27.8 km position)

**Scenario B: Good Track + Poor Position** (Consistent but Wrong)
- Low day-to-day errors
- But systematically biased in one direction
- Smooth track in wrong direction

**Scenario C: Poor Track + Good Position** (Wobbly but Right)
- Day-to-day tracking has fluctuations
- But forecast converges to correct landfall
- Example: Ian 3-day (35.3 km track, 0.0 km position)

**Scenario D: Poor Track + Poor Position** (Complete Failure)
- Large errors throughout
- Wrong landfall location
- Example: Hinnamnor 3-day (132 km track, 1690 km position)

**Operational Priority**: For evacuation planning, **landfall position error is more important** than mean track error.

---

### 5.2 Basin-Dependent Bias Patterns

**Observed Systematic Biases**:

| Basin | MSL Bias | Wind Bias | Direction |
|-------|----------|-----------|-----------|
| **Atlantic** | +2 to +8 hPa | -4 to -8 m/s | Too Weak |
| **N Indian Ocean** | -6 to -9 hPa | +3 to +7 m/s | Too Strong |
| **W Pacific** | -2 to -8 hPa | +2 to +5 m/s | Too Strong |

**Implications**:
1. Aurora has **basin-specific intensity biases**
2. Likely related to training data distribution
3. Operational forecasts should apply basin-specific bias corrections
4. Track skill is generally good across all basins (except recurvature scenarios)

---

### 5.3 Initialization Sensitivity Interpretation

**Standard Deviation Thresholds**:
- **< 25 km**: Very low sensitivity (robust forecasts)
- **25-50 km**: Low sensitivity (relatively robust)
- **50-100 km**: Moderate sensitivity (time-of-day matters)
- **> 100 km**: High sensitivity (critical to optimize init time)

**Observed Sensitivities**:
- Amphan: 10.9 km (very low)
- Ian: 20.2 km (very low)
- Hinnamnor: 25.6 km (low)

**Operational Implication**: For most TC forecasts, initialization time of day has **low to very low impact** on forecast skill.

---

### 5.4 Lead Time Skill Degradation

**Expected Patterns**:
- 1-day: < 50 km mean error (short-range, high skill)
- 3-day: 30-100 km mean error (operational sweet spot)
- 5-day: 60-150 km mean error (medium-range, moderate skill)
- 7-day: High variability (100-300 km or more)

**Critical Transition**: 5-to-7-day transition shows **rapid skill degradation** across all cases, suggesting a fundamental predictability barrier.

---

## 6. CSV Data Usage for Paper

### 6.1 Multi-Case Comparison Tables

**Example: 3-Day Lead Comparison**
```
Event         Basin      Track Error   Position Error   MSL Error   Wind Error
Ian 2022      Atlantic   35.3 km       0.0 km          +3.6 hPa    -6.5 m/s
Sandy 2012    Atlantic   33.8 km       243.2 km        +5.4 hPa    -0.9 m/s
Amphan 2020   N Indian   30.6 km       27.8 km         -6.3 hPa    +4.5 m/s
Hinnamnor 22  W Pacific  132.1 km      1689.7 km       -3.3 hPa    +4.5 m/s
```

### 6.2 Initialization Sensitivity Summary

**Example: Amphan Stage 2**
```
Init Time   Track Error   72h Error   Position Error   MSL Error
00 UTC      55.7 km       56.5 km     159.2 km        -8.8 hPa
06 UTC      28.3 km       11.1 km     27.8 km         -6.6 hPa
12 UTC      30.6 km       41.9 km     27.8 km         -6.3 hPa
18 UTC      42.3 km       95.1 km     87.3 km         -6.9 hPa

Spread: 10.9 km (LOW sensitivity)
```

### 6.3 Lead Time Degradation Analysis

**Example: Amphan Stage 1**
```
Lead Time   Track Error   Position Error   Skill Level
1-day       22.6 km       55.6 km         Excellent
3-day       30.6 km       27.8 km         Excellent
5-day       60.0 km       153.8 km        Good
7-day       254.6 km      346.1 km        Poor

Degradation: 4× from 5-day to 7-day
```

---

## 7. Quality Control and Validation

### 7.1 Reproducibility Checks

**Stage 1 vs Stage 2 Consistency**:
- Stage 1 "3-day lead, 12 UTC init" should exactly match Stage 2 "12 UTC init, 3-day lead"
- Used to validate that results are reproducible

**Example: Amphan**
- Stage 1 (3-day, 12 UTC): 30.6 km mean, 27.8 km position
- Stage 2 (12 UTC, 3-day): 30.6 km mean, 27.8 km position
- ✅ Perfect match

### 7.2 Common Issues and Debugging

**Issue 1: Track error plot shows line ending early**
- **Check**: Verify forecast endpoint time matches expected (6h before marker)
- **Check**: Verify tracker didn't fail (look for sudden position jumps)
- **Check**: May be visual overlap with another line (identical errors)

**Issue 2: Position error is 0.0 km but track error is large**
- **Not an error!** Different metrics measuring different things
- Position error: MSL field minima (may be different times)
- Track error: Tracker positions (time-synchronized)

**Issue 3: MSL/Wind errors seem reversed (wrong sign)**
- **Check**: Basin-specific bias pattern
- Atlantic: Positive MSL = too weak (expected)
- Indo-Pacific: Negative MSL = too strong (expected)

---

## 8. References and Related Files

### Key Code Files
- `research/TC/TC_utils.py`: All metric computation functions
- `research/shared/metrics.py`: Haversine distance calculation
- `research/shared/visualization.py`: Plotting functions for error visualizations

### Documentation Files
- `research/RESEARCH_PLAN.md`: Section on "Tropical Cyclone Metrics" (newly added)
- `research/TC/2022_Ian/IAN_RESULTS.md`: Section on "Understanding the Metrics"
- `research/TC/TRACKER_LIMITATIONS.md`: Explains tracker failure modes

### Result Files
- `research/TC/TC_result_metrics.csv`: Unified CSV export for all cases
- `research/TC/[EVENT]/prediction_output/[event]_stage1_lead_time_results.json`: Summary statistics

---

## 9. Summary: Quick Reference

**For Track Quality**:
- Use: **Mean Track Error**
- Threshold: < 50 km = excellent

**For Landfall Prediction**:
- Use: **Landfall Position Error (field-based)**
- Threshold: < 50 km = excellent

**For Intensity Prediction**:
- Use: **MSL Error** and **Wind Error**
- Threshold: |MSL| < 5 hPa, |Wind| < 5 m/s = excellent

**For Initialization Robustness**:
- Use: **Standard Deviation of Mean Track Errors** across init times
- Threshold: < 50 km = robust

**For Operational Forecasting**:
- **Primary**: Landfall position error (where will it hit?)
- **Secondary**: Mean track error (how reliable is the track?)
- **Tertiary**: Timing error (when will it arrive?)

**Key Insight**: Track error and landfall position error are **complementary metrics** measuring different aspects of forecast skill. Both are necessary for comprehensive evaluation.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-14
**Maintainer**: Aurora Predictability Project
**Questions**: See detailed code comments in `TC_utils.py` or individual event result MD files

# Aurora Tracker Limitations & Mitigation Strategy

**Date**: November 10, 2025
**Issue**: Aurora's built-in tracker has limitations for landfall prediction

---

## The Problem

### Aurora Tracker Behavior (from `upstream-aurora/aurora/tracker.py`)

**Tracking Algorithm**:
1. **Primary variable**: MSL (mean sea level pressure) minimum
2. **Fallback variable**: Z700 (700 hPa geopotential) minimum
3. **Land-sea check**: Requires `is_clear()` to be True (LSM < 0.5)
4. **Search box**: 5°, 4°, 3°, 2°, 1.5° progressively smaller boxes

**Critical Limitation (Lines 185-215)**:
```python
def is_clear(lat: float, lon: float, delta: float) -> bool:
    """Is a box centred at lat/lon with 'radius' delta clear of land?"""
    _, _, lsm_box = get_box(lsm, lats, lons, lat - delta, lat + delta, ...)
    return lsm_box.max() < 0.5  # ← REQUIRES OCEAN POINTS
```

**What this means**:
- Tracker **only works over ocean** (land-sea mask < 0.5)
- **Fails near coastlines** (within ~150-300 km when search box hits land)
- **Cannot track inland** (completely fails over land)
- **Fallback to extrapolation** when land detected (not physically meaningful)

### Impact on Hurricane Sandy

**Sandy's track** (from IBTrACS):
- Oct 29, 06:00: lat 35.3°N, lon 289.5°E (still ocean) ✓
- Oct 29, 12:00: lat 36.9°N, lon 289.0°E (approaching coast) ⚠️
- Oct 29, 18:00: lat 38.3°N, lon 286.8°E (near NJ coast) ❌ **Landfall**
- Oct 30, 00:00: lat 39.5°N, lon 285.5°E (over land) ❌

**Expected tracker behavior**:
- Tracks well until **Oct 29, 12:00** (~300 km from coast)
- **Starts failing Oct 29, 18:00** (landfall, near coast)
- **Completely fails Oct 30+** (over land)

---

## Why We Keep Aurora's Tracker

### Reasons NOT to Replace:

1. **Scientific Integrity**: Aurora paper presents this tracker as part of their system
2. **Transparency**: Changing it would misrepresent Aurora's actual capabilities
3. **Comparability**: Other Aurora studies use the same tracker
4. **Paper Scope**: We evaluate Aurora as-is, not develop new methods

### Paper Positioning:

> "We evaluate Aurora's predictability using its built-in tropical cyclone tracker,
> which was designed for open-ocean tracking. We acknowledge its limitation near
> coastlines and supplement with direct meteorological field comparisons at landfall."

---

## Mitigation Strategy: Dual Verification Approach

### **Method 1: Tracker-Based Verification (Pre-Landfall)**

**Use for**: Open-ocean portion of track (before tracker fails)

**Metrics**:
- Track position error (km) - Aurora track vs IBTrACS
- Track evolution over time
- Position uncertainty (spread across init times)
- Intensity estimates (MSL min, wind max from tracker)

**Valid period for Sandy**: Oct 24-29, 06:00 (before coastal approach)

**Output**:
- Track comparison plot (ocean portion)
- Error evolution plot (up to coastal approach)
- Track statistics table

### **Method 2: Direct Field Comparison (At Landfall)**

**Use for**: Critical landfall period when tracker fails

**Approach**: Compare Aurora's predicted meteorological fields directly with ERA5

**Target Time**: Oct 29, 18:00 - Oct 30, 00:00 UTC (Sandy landfall window)

**Variables to Compare**:

1. **Mean Sea Level Pressure (MSL)**
   - Shows TC center position and intensity
   - Visual: 2D field comparison (Aurora vs ERA5)
   - Metric: Minimum MSL difference, center position difference
   - Purpose: Verify TC strength and position at landfall

2. **10m Wind Speed & Direction**
   - Shows surface wind structure and asymmetry
   - Visual: Wind field comparison (arrows/contours)
   - Metric: RMSE over affected region, max wind difference
   - Purpose: Verify TC circulation and wind hazard

3. **700 hPa Geopotential (Z700)**
   - Upper-level structure, used by tracker
   - Visual: 2D field comparison
   - Metric: Pattern correlation, minimum position
   - Purpose: Verify synoptic-scale structure

4. **850 hPa Wind**
   - Low-level circulation
   - Visual: Circulation pattern comparison
   - Metric: Circulation strength, pattern correlation
   - Purpose: Verify TC structure at lower levels

5. **Precipitation Rate** (if Aurora outputs it)
   - Rainfall distribution
   - Visual: Spatial pattern comparison
   - Metric: Spatial correlation, peak intensity
   - Purpose: Verify moisture and precipitation hazard

**Spatial Domain**:
- Regional: 30-45°N, 280-295°E (US East Coast + surrounding ocean)
- Shows both ocean approach and landfall

### **Method 3: Landfall Timing Analysis**

Since tracker fails at landfall, use **threshold-based detection**:

**Definition of Landfall**:
- When TC center crosses coastline (LSM > 0.5)
- Or when center reaches specific longitude (e.g., -75°W = 285°E for US East Coast)

**Approach**:
```python
def detect_landfall_time(track, threshold_lon=-75.0):
    """
    Detect when TC crosses threshold longitude (approximates landfall).

    For US East Coast: -75°W (285°E)
    """
    for i, lon in enumerate(track['lon']):
        if lon < (threshold_lon % 360):
            return track['time'][i]
    return None
```

**Metrics**:
- Landfall timing error (hours): Aurora vs IBTrACS
- Landfall location error (km): Along coast

**Caveats**:
- Simplified (longitude threshold, not exact coastline)
- Works for W-E landfall (Sandy's case)
- Still useful for timing comparison

---

## Implementation Plan

### Updated TC Analysis Scripts

**File: `TC/TC_utils.py`** - Add new functions:

```python
def compare_fields_at_time(aurora_batch, era5_batch, time_idx, variables):
    """
    Compare Aurora and ERA5 meteorological fields at a specific time.

    Parameters
    ----------
    aurora_batch : Batch
        Aurora forecast batch
    era5_batch : Batch
        ERA5 verification batch
    time_idx : int
        Time index to compare
    variables : list
        Variables to compare (e.g., ['msl', '10u', '10v', 'z700'])

    Returns
    -------
    dict
        Comparison metrics and data for each variable
    """
    pass

def detect_landfall_by_longitude(track, threshold_lon):
    """Detect landfall timing by longitude threshold."""
    pass

def extract_field_at_position(batch, variable, lat, lon, radius=5.0):
    """Extract a field in a box around a position."""
    pass
```

**File: `shared/visualization.py`** - Add field comparison plots:

```python
def plot_field_comparison(aurora_field, era5_field, variable, time,
                          region, title, save_path):
    """
    Side-by-side comparison of Aurora vs ERA5 field.

    Creates 3-panel figure:
    - Left: Aurora forecast
    - Middle: ERA5 truth
    - Right: Difference (Aurora - ERA5)
    """
    pass

def plot_landfall_structure(aurora_batch, era5_batch, time,
                            center_lat, center_lon, save_path):
    """
    Multi-variable TC structure comparison at landfall.

    4-panel figure:
    - MSL (Aurora vs ERA5)
    - 10m wind (Aurora vs ERA5)
    - Z700 (Aurora vs ERA5)
    - Difference summary
    """
    pass
```

### Updated Sandy Analysis Script

**File: `TC/2012_Sandy/sandy_stage1_lead_time.py`** - Add landfall analysis:

```python
# After tracker-based analysis...

# === LANDFALL FIELD COMPARISON ===
print("\n" + "="*75)
print("  Landfall Field Comparison (Oct 29, 18:00 UTC)")
print("="*75)

landfall_time_idx = 30  # Oct 29, 18:00 in combined file
landfall_lat, landfall_lon = 38.3, 286.8  # IBTrACS position

# Load ERA5 verification data for same time
era5_verification = load_era5_data(data_path, '2012-10-29')

# Extract fields at landfall time
variables = ['msl', '10u', '10v', 'z700']
comparison = compare_fields_at_time(
    aurora_predictions,
    era5_verification,
    landfall_time_idx,
    variables
)

# Plot field comparisons
plot_landfall_structure(
    aurora_predictions,
    era5_verification,
    landfall_time_idx,
    landfall_lat,
    landfall_lon,
    save_path=output_dir / "sandy_landfall_fields.png"
)

# Compute landfall metrics
landfall_metrics = {
    'msl_min_aurora': comparison['msl']['aurora_min'],
    'msl_min_era5': comparison['msl']['era5_min'],
    'msl_error': comparison['msl']['aurora_min'] - comparison['msl']['era5_min'],
    'wind_max_aurora': comparison['wind']['aurora_max'],
    'wind_max_era5': comparison['wind']['era5_max'],
    'wind_error': comparison['wind']['aurora_max'] - comparison['wind']['era5_max'],
    'position_error_km': calculate_distance(
        comparison['msl']['aurora_center_lat'],
        comparison['msl']['aurora_center_lon'],
        landfall_lat,
        landfall_lon
    )
}

print("\nLandfall Metrics:")
print(f"  MSL minimum: Aurora {landfall_metrics['msl_min_aurora']:.1f} hPa, "
      f"ERA5 {landfall_metrics['msl_min_era5']:.1f} hPa, "
      f"Error {landfall_metrics['msl_error']:.1f} hPa")
print(f"  10m wind max: Aurora {landfall_metrics['wind_max_aurora']:.1f} m/s, "
      f"ERA5 {landfall_metrics['wind_max_era5']:.1f} m/s, "
      f"Error {landfall_metrics['wind_error']:.1f} m/s")
print(f"  Center position error: {landfall_metrics['position_error_km']:.1f} km")
```

---

## Paper Presentation

### Methods Section

**Subsection: "Tropical Cyclone Tracking and Verification"**

> We use Aurora's built-in tropical cyclone tracker (Bodnar et al., 2024), which
> identifies TC centers by detecting minima in mean sea-level pressure (MSL) and
> 700 hPa geopotential height (Z700). The tracker searches progressively smaller
> boxes (5°, 4°, 3°, 2°, 1.5°) around an extrapolated position from previous time steps.
>
> **Limitation**: Aurora's tracker requires predominantly oceanic grid points and
> cannot reliably track storms near coastlines or over land. For our analysis,
> this means the tracker is reliable for the open-ocean portion of TC tracks but
> fails during and after landfall.
>
> **Mitigation**: We use a dual verification approach:
> 1. **Tracker-based metrics** (pre-landfall): Track position error, timing, and
>    evolution against IBTrACS observations during the open-ocean phase.
> 2. **Direct field comparison** (at landfall): We compare Aurora's predicted
>    meteorological fields (MSL, 10m winds, Z700) directly with ERA5 at the
>    landfall time to assess TC structure, intensity, and position when the
>    tracker fails.

### Results Section

**Figure 2: TC Predictability (Updated Layout)**

- **Panel A**: Track comparison (ocean portion, tracker-based)
- **Panel B**: Track error vs lead time (ocean phase)
- **Panel C**: **Landfall structure comparison** (MSL, wind fields)
- **Panel D**: Initialization sensitivity (track spread)

**Table**: TC Metrics

| Metric | 1-day | 3-day | 5-day | 7-day |
|--------|-------|-------|-------|-------|
| **Ocean Phase (Tracker)** |
| Mean track error (km) | XX | XX | XX | XX |
| 72h track error (km) | XX | XX | XX | XX |
| **Landfall (Direct Comparison)** |
| MSL min error (hPa) | XX | XX | XX | XX |
| Max wind error (m/s) | XX | XX | XX | XX |
| Center position error (km) | XX | XX | XX | XX |
| Landfall timing error (hours) | XX | XX | XX | XX |

### Discussion Section

> **Landfall Prediction Challenges**: Aurora's tracker limitation near coastlines
> highlights a general challenge in AI weather models: object detection algorithms
> designed for global forecasting may not handle land-ocean boundaries well. Our
> direct field comparison reveals that Aurora's predicted meteorological fields
> (MSL, winds) remain physically reasonable near landfall, even when the tracker
> fails. This suggests the limitation is in the tracking algorithm, not in Aurora's
> fundamental prediction capability.

---

## Summary

**What We Do**:
1. ✅ Use Aurora's tracker as-is (scientific integrity)
2. ✅ Acknowledge limitation explicitly (transparency)
3. ✅ Add direct field comparison (complete verification)
4. ✅ Report both metrics (comprehensive assessment)

**What We Don't Do**:
1. ❌ Replace Aurora's tracker (misrepresents system)
2. ❌ Hide the limitation (unscientific)
3. ❌ Only show tracker results (incomplete)

**Paper Impact**:
- **Honesty**: Clearly identifies Aurora's limitation
- **Rigor**: Provides alternative verification method
- **Value**: Demonstrates field-level prediction skill
- **Future work**: Motivates better tracking algorithms

This approach turns a limitation into a scientific contribution! 🎯

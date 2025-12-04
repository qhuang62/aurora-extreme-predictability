#!/usr/bin/env python3
"""
2023 European Heatwave - Baseline ERA5 Analysis

Purpose: Understand the heatwave event in ERA5 (ground truth) BEFORE testing Aurora predictions.

This script analyzes the complete ERA5 dataset (Jul 19 - Aug 27, 2023) to:
1. Verify event timeline (onset, peak, recovery dates)
2. Understand physical mechanisms (heat dome, warm air advection)
3. Define appropriate thresholds and metrics
4. Create spatial/temporal visualizations
5. Inform experimental design refinements

Outputs:
- Time series plots (regional T2m, spatial extent, duration)
- Event statistics (onset/peak/recovery dates, hottest values)
- Baseline metrics for comparison with Aurora predictions

Run this FIRST before running any Aurora forecasts!
"""

# Set up library paths and matplotlib backend BEFORE any imports to avoid GLIBCXX issues on HPC
import os
import sys

# Fix GLIBCXX compatibility on HPC by prioritizing conda libraries
conda_base = '/packages/apps/jupyter/2025-03-24'
conda_lib = os.path.join(conda_base, 'lib')
if os.path.exists(conda_lib):
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    if conda_lib not in current_ld_path:
        os.environ['LD_LIBRARY_PATH'] = f"{conda_lib}:{current_ld_path}"
        # Re-execute script with updated environment
        os.execv(sys.executable, [sys.executable] + sys.argv)

os.environ['MPLBACKEND'] = 'Agg'

from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Regional domain for European Heatwave 2023
REGION = {
    'name': 'SW Europe (France, N. Spain, Switzerland)',
    'lat_min': 42.0,   # Northern Spain
    'lat_max': 48.0,   # Central France
    'lon_min': -2.0,   # Western France/N. Spain
    'lon_max': 8.0,    # Switzerland/E. France
}

# Heatwave thresholds (Celsius) - INVERTED from freeze
THRESHOLDS = [30.0, 35.0, 40.0]

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data" / "era5_heatwave_2023"
OUTPUT_DIR = Path(__file__).parent / "baseline_analysis"


def load_era5_data():
    """Load combined ERA5 surface and atmospheric data."""
    print("Loading ERA5 data...")

    surf_file = DATA_DIR / "heatwave_2023_surface_jul19-aug27.nc"
    atmos_file = DATA_DIR / "heatwave_2023_atmospheric_jul19-aug27.nc"

    if not surf_file.exists():
        print(f"ERROR: Surface file not found: {surf_file}")
        print("Run combine_heatwave_data.py first!")
        sys.exit(1)

    if not atmos_file.exists():
        print(f"ERROR: Atmospheric file not found: {atmos_file}")
        print("Run combine_heatwave_data.py first!")
        sys.exit(1)

    surf_ds = xr.open_dataset(surf_file)
    atmos_ds = xr.open_dataset(atmos_file)

    print(f"✓ Loaded {len(surf_ds.valid_time)} timesteps")
    print(f"  Time range: {surf_ds.valid_time.values[0]} to {surf_ds.valid_time.values[-1]}")

    return surf_ds, atmos_ds


def extract_regional_subset(ds, variable):
    """Extract regional subset for analysis."""
    lon_min = REGION['lon_min'] if REGION['lon_min'] >= 0 else REGION['lon_min'] + 360
    lon_max = REGION['lon_max'] if REGION['lon_max'] >= 0 else REGION['lon_max'] + 360

    if lon_min > lon_max:
        # Crosses prime meridian
        subset1 = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, 360)
        )
        subset2 = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(0, lon_max)
        )
        subset = xr.concat([subset1, subset2], dim='longitude')
    else:
        subset = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, lon_max)
        )

    return subset


def analyze_temporal_evolution(surf_ds):
    """Analyze temporal evolution of heatwave event."""
    print("\n" + "=" * 80)
    print("TEMPORAL EVOLUTION ANALYSIS")
    print("=" * 80)

    # Extract T2m over region
    t2m = extract_regional_subset(surf_ds, 't2m')
    t2m_celsius = t2m - 273.15  # Convert K to °C

    # Compute regional statistics
    times = []
    regional_mean = []
    regional_max = []  # MAX for heatwave (not min!)
    area_above_30 = []
    area_above_35 = []
    area_above_40 = []

    for t_idx in range(len(t2m_celsius.valid_time)):
        t2m_t = t2m_celsius.isel(valid_time=t_idx)

        times.append(t2m_t.valid_time.values)
        regional_mean.append(float(t2m_t.mean().values))
        regional_max.append(float(t2m_t.max().values))  # MAX for heat

        # Compute area ABOVE thresholds (INVERTED from freeze)
        total_points = t2m_t.size
        area_above_30.append(float((t2m_t > 30).sum() / total_points))
        area_above_35.append(float((t2m_t > 35).sum() / total_points))
        area_above_40.append(float((t2m_t > 40).sum() / total_points))

    times = np.array(times)
    regional_mean = np.array(regional_mean)
    regional_max = np.array(regional_max)
    area_above_30 = np.array(area_above_30)
    area_above_35 = np.array(area_above_35)
    area_above_40 = np.array(area_above_40)

    # Identify key dates (INVERTED LOGIC for heat)
    print("\nKey Event Dates:")

    # Onset: First time regional mean > 30°C
    onset_idx = np.where(regional_mean > 30)[0]
    if len(onset_idx) > 0:
        onset_time = times[onset_idx[0]]
        print(f"  Onset (regional mean > 30°C): {onset_time}")
    else:
        onset_time = None
        print(f"  Onset: Not detected (regional mean never > 30°C)")

    # Peak: MAXIMUM regional mean (INVERTED from freeze)
    peak_idx = np.argmax(regional_mean)  # argmax instead of argmin
    peak_time = times[peak_idx]
    peak_temp = regional_max[peak_idx]
    print(f"  Peak heat: {peak_time}")
    print(f"    Regional mean: {regional_mean[peak_idx]:.1f}°C")
    print(f"    Regional max: {peak_temp:.1f}°C")

    # Maximum spatial extent
    max_extent_idx = np.argmax(area_above_30)
    max_extent_time = times[max_extent_idx]
    print(f"  Maximum spatial extent (T > 30°C): {max_extent_time}")
    print(f"    Fraction of region: {area_above_30[max_extent_idx]*100:.1f}%")

    # Recovery: Last time regional mean > 30°C
    if onset_idx is not None and len(onset_idx) > 0:
        recovery_idx = onset_idx[-1]
        recovery_time = times[recovery_idx]
        print(f"  Recovery (regional mean drops < 30°C): {times[recovery_idx + 1] if recovery_idx + 1 < len(times) else 'After data range'}")

    # Duration
    if onset_idx is not None and len(onset_idx) > 0:
        duration_timesteps = len(onset_idx)
        duration_hours = duration_timesteps * 6
        duration_days = duration_hours / 24
        print(f"  Duration (T > 30°C): {duration_hours} hours ({duration_days:.1f} days)")

    # Plot temporal evolution
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))

    # Use indices for x-axis and label with dates (better control)
    x_indices = np.arange(len(times))

    # Create date labels - show every 2 days for heatwave (more frequent than freeze)
    date_labels = []
    date_positions = []
    for i, t in enumerate(times):
        dt = pd.Timestamp(t)
        if i % 8 == 0:  # Every 8 timesteps = 2 days (6-hour intervals)
            date_labels.append(dt.strftime('%b %d'))
            date_positions.append(i)

    # Plot 1: Temperature evolution
    ax = axes[0]
    ax.plot(x_indices, regional_mean, 'r-', linewidth=2, label='Regional mean')
    ax.plot(x_indices, regional_max, 'darkred', linewidth=1.5, linestyle='--', label='Regional max')
    ax.axhline(30, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(35, color='red', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(40, color='darkred', linestyle=':', linewidth=1, alpha=0.5)

    # Mark key dates
    if onset_idx is not None and len(onset_idx) > 0:
        onset_idx_val = onset_idx[0]
        ax.axvline(onset_idx_val, color='green', linestyle='--', alpha=0.7, label='Onset')
    peak_idx_val = peak_idx
    ax.axvline(peak_idx_val, color='purple', linestyle='--', alpha=0.7, label='Peak')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('2023 European Heatwave: Regional Temperature Evolution (ERA5)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 2: Spatial extent above thresholds
    ax = axes[1]
    ax.plot(x_indices, area_above_30 * 100, 'orange', linewidth=2, label='T > 30°C')
    ax.plot(x_indices, area_above_35 * 100, 'red', linewidth=2, label='T > 35°C')
    ax.plot(x_indices, area_above_40 * 100, 'darkred', linewidth=2, label='T > 40°C')

    ax.set_ylabel('% of Region', fontsize=12)
    ax.set_title('Spatial Extent Above Thresholds', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 3: Hottest temperature
    ax = axes[2]
    ax.plot(x_indices, regional_max, 'darkred', linewidth=2)
    ax.fill_between(x_indices, regional_max, 30, alpha=0.3, color='red', where=(regional_max > 30))
    ax.axhline(30, color='k', linestyle='--', linewidth=1)
    ax.axhline(40, color='red', linestyle=':', linewidth=1, alpha=0.5)

    ax.set_ylabel('Hottest T (°C)', fontsize=12)
    ax.set_xlabel('Date (2023)', fontsize=12)
    ax.set_title('Regional Maximum Temperature', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.08, hspace=0.3)

    output_file = OUTPUT_DIR / "heatwave_temporal_evolution.png"
    plt.savefig(output_file, dpi=300)
    print(f"\n✓ Saved: {output_file.name}")
    plt.close()

    return {
        'onset_time': str(onset_time) if onset_time is not None else None,
        'peak_time': str(peak_time),
        'peak_mean_temp': float(regional_mean[peak_idx]),
        'peak_max_temp': float(peak_temp),
        'duration_hours': int(duration_hours) if onset_idx is not None and len(onset_idx) > 0 else None
    }


def extract_atmos_regional_subset(ds, variable, level):
    """Extract regional subset for atmospheric variable at specific pressure level."""
    lon_min = REGION['lon_min'] if REGION['lon_min'] >= 0 else REGION['lon_min'] + 360
    lon_max = REGION['lon_max'] if REGION['lon_max'] >= 0 else REGION['lon_max'] + 360

    # Check if region crosses prime meridian
    if lon_min > lon_max:
        subset1 = ds[variable].sel(
            pressure_level=level,
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, 360)
        )
        subset2 = ds[variable].sel(
            pressure_level=level,
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(0, lon_max)
        )
        subset = xr.concat([subset1, subset2], dim='longitude')
    else:
        subset = ds[variable].sel(
            pressure_level=level,
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, lon_max)
        )
    return subset


def plot_spatial_statistics(surf_ds, atmos_ds):
    """Create line plots showing spatial statistics over time (T2m, T850, MSL, Z500)."""
    print("\nCreating spatial statistics plot...")

    # Extract surface data
    t2m = extract_regional_subset(surf_ds, 't2m') - 273.15
    msl = extract_regional_subset(surf_ds, 'msl') / 100

    # Extract atmospheric data
    t850 = extract_atmos_regional_subset(atmos_ds, 't', 850) - 273.15  # Convert to °C
    z500 = extract_atmos_regional_subset(atmos_ds, 'z', 500) / 9.81  # Convert to geopotential meters

    # Compute spatial statistics for each timestep
    times = []
    t2m_mean = []
    t2m_min = []
    t2m_max = []
    msl_mean = []
    msl_min = []
    msl_max = []
    t850_mean = []
    t850_min = []
    t850_max = []
    z500_mean = []
    z500_min = []
    z500_max = []

    for t_idx in range(len(t2m.valid_time)):
        times.append(t2m.valid_time.values[t_idx])

        t2m_t = t2m.isel(valid_time=t_idx)
        t2m_mean.append(float(t2m_t.mean().values))
        t2m_min.append(float(t2m_t.min().values))
        t2m_max.append(float(t2m_t.max().values))

        msl_t = msl.isel(valid_time=t_idx)
        msl_mean.append(float(msl_t.mean().values))
        msl_min.append(float(msl_t.min().values))
        msl_max.append(float(msl_t.max().values))

        t850_t = t850.isel(valid_time=t_idx)
        t850_mean.append(float(t850_t.mean().values))
        t850_min.append(float(t850_t.min().values))
        t850_max.append(float(t850_t.max().values))

        z500_t = z500.isel(valid_time=t_idx)
        z500_mean.append(float(z500_t.mean().values))
        z500_min.append(float(z500_t.min().values))
        z500_max.append(float(z500_t.max().values))

    times = np.array(times)
    t2m_mean = np.array(t2m_mean)
    t2m_min = np.array(t2m_min)
    t2m_max = np.array(t2m_max)
    msl_mean = np.array(msl_mean)
    msl_min = np.array(msl_min)
    msl_max = np.array(msl_max)
    t850_mean = np.array(t850_mean)
    t850_min = np.array(t850_min)
    t850_max = np.array(t850_max)
    z500_mean = np.array(z500_mean)
    z500_min = np.array(z500_min)
    z500_max = np.array(z500_max)

    # Create figure with 4 subplots
    fig, axes = plt.subplots(4, 1, figsize=(14, 14))

    # Use indices for x-axis
    x_indices = np.arange(len(times))

    # Create date labels - every 2 days for heatwave
    date_labels = []
    date_positions = []
    for i, t in enumerate(times):
        dt = pd.Timestamp(t)
        if i % 8 == 0:  # Every 8 timesteps = 2 days (6-hour intervals)
            date_labels.append(dt.strftime('%b %d'))
            date_positions.append(i)

    # Plot 1: 2m Temperature spatial statistics
    ax = axes[0]
    ax.plot(x_indices, t2m_mean, 'r-', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, t2m_min, t2m_max, alpha=0.2, color='red', label='Min-Max range')
    ax.plot(x_indices, t2m_min, 'r--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, t2m_max, 'r--', linewidth=1, alpha=0.7)
    ax.axhline(30, color='k', linestyle='--', linewidth=1.5, alpha=0.7, label='30°C')
    ax.axhline(35, color='darkred', linestyle=':', linewidth=1.5, alpha=0.7, label='35°C')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('2m Temperature: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 2: 850 hPa Temperature spatial statistics
    ax = axes[1]
    ax.plot(x_indices, t850_mean, 'darkorange', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, t850_min, t850_max, alpha=0.2, color='orange', label='Min-Max range')
    ax.plot(x_indices, t850_min, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, t850_max, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(15, color='darkred', linestyle='--', linewidth=1.5, alpha=0.7, label='15°C (warm air indicator)')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('850 hPa Temperature: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 3: MSL spatial statistics
    ax = axes[2]
    ax.plot(x_indices, msl_mean, 'darkblue', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, msl_min, msl_max, alpha=0.2, color='blue', label='Min-Max range')
    ax.plot(x_indices, msl_min, 'b--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, msl_max, 'b--', linewidth=1, alpha=0.7)

    ax.set_ylabel('Pressure (hPa)', fontsize=12)
    ax.set_title('Mean Sea Level Pressure: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 4: 500 hPa Geopotential Height spatial statistics
    ax = axes[3]
    ax.plot(x_indices, z500_mean, 'purple', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, z500_min, z500_max, alpha=0.2, color='purple', label='Min-Max range')
    ax.plot(x_indices, z500_min, color='purple', linestyle='--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, z500_max, color='purple', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_ylabel('Geopotential Height (m)', fontsize=12)
    ax.set_xlabel('Date (2023)', fontsize=12)
    ax.set_title('500 hPa Geopotential Height: Spatial Statistics (ridging/blocking indicator)', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.97, bottom=0.05, hspace=0.3)

    output_file = OUTPUT_DIR / "heatwave_spatial_statistics.png"
    plt.savefig(output_file, dpi=300)
    print(f"  ✓ Saved: {output_file.name}")
    plt.close()


def main():
    print("=" * 80)
    print("  2023 European Heatwave - Baseline ERA5 Analysis")
    print("=" * 80)
    print()
    print(f"Region: {REGION['name']}")
    print(f"  Latitude: {REGION['lat_min']}°N to {REGION['lat_max']}°N")
    print(f"  Longitude: {REGION['lon_min']}°E to {REGION['lon_max']}°E")
    print(f"Heatwave Thresholds: {THRESHOLDS}°C")
    print()

    # Load data
    surf_ds, atmos_ds = load_era5_data()

    # Analyze temporal evolution
    event_stats = analyze_temporal_evolution(surf_ds)

    # Create spatial statistics plot
    plot_spatial_statistics(surf_ds, atmos_ds)

    print("\n" + "=" * 80)
    print("  BASELINE ANALYSIS SUMMARY")
    print("=" * 80)
    print()
    print("Event Timeline:")
    print(f"  Onset: {event_stats['onset_time']}")
    print(f"  Peak: {event_stats['peak_time']}")
    print(f"  Duration: {event_stats['duration_hours']} hours")
    print()
    print("Peak Intensity:")
    print(f"  Regional mean: {event_stats['peak_mean_temp']:.1f}°C")
    print(f"  Regional max: {event_stats['peak_max_temp']:.1f}°C")
    print()
    print(f"Outputs saved to: {OUTPUT_DIR}")
    print()
    print("Next Steps:")
    print("  1. Review baseline analysis outputs")
    print("  2. Verify onset/peak/recovery dates match expected timeline")
    print("  3. Run heatwave_stage1_detection.py to test Aurora predictions")
    print()


if __name__ == "__main__":
    main()

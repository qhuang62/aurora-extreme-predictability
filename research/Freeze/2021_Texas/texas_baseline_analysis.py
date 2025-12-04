#!/usr/bin/env python3
"""
Texas 2021 Freeze - Baseline ERA5 Analysis

Purpose: Understand the freeze event in ERA5 (ground truth) BEFORE testing Aurora predictions.

This script analyzes the complete ERA5 dataset (Jan 24 - Feb 21, 2021) to:
1. Verify event timeline (onset, peak, recovery dates)
2. Understand physical mechanisms (Arctic outbreak, cold air advection)
3. Define appropriate thresholds and metrics
4. Create spatial/temporal visualizations
5. Inform experimental design refinements

Outputs:
- Time series plots (regional T2m, spatial extent, duration)
- Spatial evolution GIFs (T2m and MSL separately)
- Event statistics (onset/peak/recovery dates, coldest values)
- Physical mechanism analysis (blocking patterns, jet stream)

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
import matplotlib.animation as animation
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from datetime import datetime, timedelta

# Regional domain for Texas 2021 Freeze
REGION = {
    'name': 'Texas and Southern US',
    'lat_min': 25.0,   # 25°N
    'lat_max': 37.0,   # 37°N
    'lon_min': -107.0, # 107°W
    'lon_max': -93.0,  # 93°W
}

# Freeze thresholds (Celsius)
THRESHOLDS = [0.0, -5.0, -10.0]

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data" / "era5_texas_2021"
OUTPUT_DIR = Path(__file__).parent / "baseline_analysis"

def load_era5_data():
    """Load combined ERA5 surface and atmospheric data."""
    print("Loading ERA5 data...")

    surf_file = DATA_DIR / "texas_2021_surface_jan24-feb21.nc"
    atmos_file = DATA_DIR / "texas_2021_atmospheric_jan24-feb21.nc"

    if not surf_file.exists():
        print(f"ERROR: Surface file not found: {surf_file}")
        print("Run combine_texas_data.py first!")
        sys.exit(1)

    if not atmos_file.exists():
        print(f"ERROR: Atmospheric file not found: {atmos_file}")
        print("Run combine_texas_data.py first!")
        sys.exit(1)

    surf_ds = xr.open_dataset(surf_file)
    atmos_ds = xr.open_dataset(atmos_file)

    print(f"✓ Loaded {len(surf_ds.valid_time)} timesteps")
    print(f"  Time range: {surf_ds.valid_time.values[0]} to {surf_ds.valid_time.values[-1]}")

    return surf_ds, atmos_ds


def extract_regional_subset(ds, variable):
    """Extract regional subset for analysis."""
    # Handle longitude wrapping (convert negative to 0-360 if needed)
    lon_min = REGION['lon_min'] if REGION['lon_min'] >= 0 else REGION['lon_min'] + 360
    lon_max = REGION['lon_max'] if REGION['lon_max'] >= 0 else REGION['lon_max'] + 360

    # Check if region crosses prime meridian (lon_min > lon_max in 0-360 coords)
    if lon_min > lon_max:
        # Need to extract two regions and concatenate them
        # Region 1: lon_min to 360
        subset1 = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, 360)
        )
        # Region 2: 0 to lon_max
        subset2 = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(0, lon_max)
        )
        # Concatenate along longitude dimension
        subset = xr.concat([subset1, subset2], dim='longitude')
    else:
        # Simple case: region doesn't cross prime meridian
        subset = ds[variable].sel(
            latitude=slice(REGION['lat_max'], REGION['lat_min']),
            longitude=slice(lon_min, lon_max)
        )

    return subset


def analyze_temporal_evolution(surf_ds):
    """Analyze temporal evolution of freeze event."""
    print("\n" + "=" * 80)
    print("TEMPORAL EVOLUTION ANALYSIS")
    print("=" * 80)

    # Extract T2m over region
    t2m = extract_regional_subset(surf_ds, 't2m')
    t2m_celsius = t2m - 273.15  # Convert K to °C

    # Compute regional statistics
    times = []
    regional_mean = []
    regional_min = []
    area_below_0 = []
    area_below_minus5 = []
    area_below_minus10 = []

    for t_idx in range(len(t2m_celsius.valid_time)):
        t2m_t = t2m_celsius.isel(valid_time=t_idx)

        times.append(t2m_t.valid_time.values)
        regional_mean.append(float(t2m_t.mean().values))
        regional_min.append(float(t2m_t.min().values))

        # Compute area below thresholds (fraction of grid points)
        total_points = t2m_t.size
        area_below_0.append(float((t2m_t < 0).sum() / total_points))
        area_below_minus5.append(float((t2m_t < -5).sum() / total_points))
        area_below_minus10.append(float((t2m_t < -10).sum() / total_points))

    times = np.array(times)
    regional_mean = np.array(regional_mean)
    regional_min = np.array(regional_min)
    area_below_0 = np.array(area_below_0)
    area_below_minus5 = np.array(area_below_minus5)
    area_below_minus10 = np.array(area_below_minus10)

    # Identify key dates
    print("\nKey Event Dates:")

    # Onset: First time regional mean < 0°C
    onset_idx = np.where(regional_mean < 0)[0]
    if len(onset_idx) > 0:
        onset_time = times[onset_idx[0]]
        print(f"  Onset (regional mean < 0°C): {onset_time}")
    else:
        onset_time = None
        print(f"  Onset: Not detected (regional mean never < 0°C)")

    # Peak: Minimum regional mean
    peak_idx = np.argmin(regional_mean)
    peak_time = times[peak_idx]
    peak_temp = regional_min[peak_idx]
    print(f"  Peak cold: {peak_time}")
    print(f"    Regional mean: {regional_mean[peak_idx]:.1f}°C")
    print(f"    Regional min: {peak_temp:.1f}°C")

    # Maximum spatial extent
    max_extent_idx = np.argmax(area_below_0)
    max_extent_time = times[max_extent_idx]
    print(f"  Maximum spatial extent (T < 0°C): {max_extent_time}")
    print(f"    Fraction of region: {area_below_0[max_extent_idx]*100:.1f}%")

    # Recovery: Last time regional mean < 0°C
    if onset_idx is not None and len(onset_idx) > 0:
        recovery_idx = onset_idx[-1]
        recovery_time = times[recovery_idx]
        print(f"  Recovery (regional mean returns > 0°C): {times[recovery_idx + 1] if recovery_idx + 1 < len(times) else 'After data range'}")

    # Duration
    if onset_idx is not None and len(onset_idx) > 0:
        duration_timesteps = len(onset_idx)
        duration_hours = duration_timesteps * 6
        print(f"  Duration (regional mean < 0°C): {duration_hours}h ({duration_hours/24:.1f} days)")

    return {
        'times': times,
        'regional_mean': regional_mean,
        'regional_min': regional_min,
        'area_below_0': area_below_0,
        'area_below_minus5': area_below_minus5,
        'area_below_minus10': area_below_minus10,
        'onset_time': onset_time,
        'peak_time': peak_time,
        'peak_temp': peak_temp,
    }


def plot_temporal_evolution(stats):
    """Create time series plots of freeze evolution."""
    print("\nCreating temporal evolution plots...")

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Use indices for x-axis and label with dates
    x_indices = np.arange(len(stats['times']))

    # Create date labels - show every 3 days
    date_labels = []
    date_positions = []
    for i, t in enumerate(stats['times']):
        dt = pd.Timestamp(t)
        if i % 12 == 0:  # Every 12 timesteps = 3 days (6-hour intervals)
            date_labels.append(dt.strftime('%b %d'))
            date_positions.append(i)

    # Plot 1: Regional temperature
    ax = axes[0]
    ax.plot(x_indices, stats['regional_mean'], 'b-', linewidth=2, label='Regional mean')
    ax.plot(x_indices, stats['regional_min'], 'r--', linewidth=1.5, label='Regional min')
    ax.axhline(0, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(-5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(-10, color='gray', linestyle=':', linewidth=1, alpha=0.5)

    # Mark key dates
    if stats['onset_time'] is not None:
        onset_idx = np.where(stats['times'] == stats['onset_time'])[0][0]
        ax.axvline(onset_idx, color='green', linestyle='--', alpha=0.7, label='Onset')
    peak_idx = np.where(stats['times'] == stats['peak_time'])[0][0]
    ax.axvline(peak_idx, color='red', linestyle='--', alpha=0.7, label='Peak')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('Texas 2021 Freeze: Regional Temperature Evolution (ERA5)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 2: Spatial extent below thresholds
    ax = axes[1]
    ax.plot(x_indices, stats['area_below_0'] * 100, 'b-', linewidth=2, label='T < 0°C')
    ax.plot(x_indices, stats['area_below_minus5'] * 100, 'orange', linewidth=2, label='T < -5°C')
    ax.plot(x_indices, stats['area_below_minus10'] * 100, 'r-', linewidth=2, label='T < -10°C')

    ax.set_ylabel('% of Region', fontsize=12)
    ax.set_title('Spatial Extent Below Thresholds', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 3: Coldest temperature
    ax = axes[2]
    ax.plot(x_indices, stats['regional_min'], 'darkblue', linewidth=2)
    ax.fill_between(x_indices, stats['regional_min'], 0, alpha=0.3, color='blue')
    ax.axhline(0, color='k', linestyle='--', linewidth=1)

    ax.set_ylabel('Coldest T (°C)', fontsize=12)
    ax.set_xlabel('Date (2021)', fontsize=12)
    ax.set_title('Regional Minimum Temperature', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Use subplots_adjust for layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.08, hspace=0.3)

    output_file = OUTPUT_DIR / "texas_temporal_evolution.png"
    plt.savefig(output_file, dpi=300)
    print(f"  ✓ Saved: {output_file.name}")
    plt.close()


def extract_atmos_regional_subset(ds, variable, level):
    """Extract regional subset for atmospheric variable at specific pressure level."""
    lon_min = REGION['lon_min'] if REGION['lon_min'] >= 0 else REGION['lon_min'] + 360
    lon_max = REGION['lon_max'] if REGION['lon_max'] >= 0 else REGION['lon_max'] + 360

    # Check if region crosses prime meridian (lon_min > lon_max in 0-360 coords)
    if lon_min > lon_max:
        # Need to extract two regions and concatenate them
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


def create_spatial_statistics_plot(surf_ds, atmos_ds):
    """Create line plots showing spatial statistics over time."""
    print("\nCreating spatial statistics plot...")

    # Extract data
    t2m = extract_regional_subset(surf_ds, 't2m') - 273.15
    msl = extract_regional_subset(surf_ds, 'msl') / 100

    # Extract atmospheric data (CRITICAL: Use correct Aurora indices)
    # Aurora levels: (1000, 925, 850, 700, 600, 500, ...)
    # 850 hPa = index 2, 500 hPa = index 5
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

    # Create date labels
    date_labels = []
    date_positions = []
    for i, t in enumerate(times):
        dt = pd.Timestamp(t)
        if i % 12 == 0:  # Every 3 days
            date_labels.append(dt.strftime('%b %d'))
            date_positions.append(i)

    # Plot 1: Temperature spatial statistics
    ax = axes[0]
    ax.plot(x_indices, t2m_mean, 'b-', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, t2m_min, t2m_max, alpha=0.2, color='blue', label='Min-Max range')
    ax.plot(x_indices, t2m_min, 'b--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, t2m_max, 'b--', linewidth=1, alpha=0.7)
    ax.axhline(0, color='k', linestyle='--', linewidth=1.5, alpha=0.7, label='0°C')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('2m Temperature: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 2: 850 hPa Temperature spatial statistics
    ax = axes[1]
    ax.plot(x_indices, t850_mean, 'darkgreen', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, t850_min, t850_max, alpha=0.2, color='green', label='Min-Max range')
    ax.plot(x_indices, t850_min, 'g--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, t850_max, 'g--', linewidth=1, alpha=0.7)
    ax.axhline(-5, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='-5°C (freeze indicator)')

    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('850 hPa Temperature: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    # Plot 3: MSL spatial statistics
    ax = axes[2]
    ax.plot(x_indices, msl_mean, 'darkred', linewidth=2.5, label='Regional mean')
    ax.fill_between(x_indices, msl_min, msl_max, alpha=0.2, color='red', label='Min-Max range')
    ax.plot(x_indices, msl_min, 'r--', linewidth=1, alpha=0.7)
    ax.plot(x_indices, msl_max, 'r--', linewidth=1, alpha=0.7)

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
    ax.set_xlabel('Date (2021)', fontsize=12)
    ax.set_title('500 hPa Geopotential Height: Spatial Statistics', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(date_positions)
    ax.set_xticklabels(date_labels)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.97, bottom=0.05, hspace=0.3)

    output_file = OUTPUT_DIR / "texas_spatial_statistics.png"
    plt.savefig(output_file, dpi=300)
    print(f"  ✓ Saved: {output_file.name}")
    plt.close()


def main():
    """Run complete baseline analysis."""
    print("=" * 80)
    print("  Texas 2021 Freeze - Baseline ERA5 Analysis")
    print("=" * 80)
    print()
    print("Purpose: Understand the freeze event BEFORE testing Aurora predictions")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    surf_ds, atmos_ds = load_era5_data()

    # Temporal analysis
    stats = analyze_temporal_evolution(surf_ds)

    # Create plots
    plot_temporal_evolution(stats)

    # Create spatial statistics plot
    create_spatial_statistics_plot(surf_ds, atmos_ds)

    print("\n" + "=" * 80)
    print("  ✓ Baseline Analysis Complete!")
    print("=" * 80)
    print()
    print("Outputs saved to:", OUTPUT_DIR)
    print("  - texas_temporal_evolution.png (temporal statistics)")
    print("  - texas_spatial_statistics.png (spatial mean/min/max over time)")
    print()
    print("Next steps:")
    print("  1. Review temporal evolution plot to verify event timeline")
    print("  2. Identify ONSET, PEAK, and RECOVERY dates from the output above")
    print("  3. Update texas_stage1_detection.py with correct dates")
    print("  4. Run Stage 1 Aurora predictions (texas_stage1_detection.py)")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Combine individual ERA5 files for Texas 2021 Freeze into continuous timeseries.

Data range: Jan 24 - Feb 21, 2021 (29 days, 116 timesteps at 6-hourly)
Covers all initialization times and full event verification period.

Memory-efficient version: Loads files one at a time with progress tracking.
"""

import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta

def combine_data():
    """Combine Jan 24 - Feb 21, 2021 data files into single continuous files."""

    data_dir = Path(__file__).parent

    print("=" * 80)
    print("  Combining Jan 24 - Feb 21, 2021 ERA5 Data for Texas Freeze")
    print("=" * 80)
    print()

    # Generate date range (Jan 24 - Feb 21, 2021)
    start_date = datetime(2021, 1, 24)
    end_date = datetime(2021, 2, 21)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Check which files exist
    print("Checking available data files...")
    surface_files = []
    atmos_files = []
    missing_dates = []

    for date_str in dates:
        surf_file = data_dir / f"{date_str}-surface-level.nc"
        atmos_file = data_dir / f"{date_str}-atmospheric.nc"

        dt = datetime.strptime(date_str, '%Y-%m-%d')

        if surf_file.exists() and atmos_file.exists():
            surface_files.append(surf_file)
            atmos_files.append(atmos_file)
            print(f"  ✓ {dt.strftime('%b %d, %Y')}: Found both files")
        else:
            missing_dates.append(date_str)
            print(f"  ✗ {dt.strftime('%b %d, %Y')}: Missing files")
            if not surf_file.exists():
                print(f"      Missing: {surf_file.name}")
            if not atmos_file.exists():
                print(f"      Missing: {atmos_file.name}")

    if missing_dates:
        print(f"\n⚠ WARNING: {len(missing_dates)} dates missing!")
        print("  Missing dates:", ', '.join(missing_dates))
        print()
        response = input("Continue combining available data? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    if len(surface_files) < 2:
        print("\nERROR: Not enough data files found!")
        print("Run download script first to download all dates.")
        return

    print(f"\nFound {len(surface_files)} complete days of data.")
    print()

    # Combine surface data
    print("1. Combining surface-level data...")
    surf_datasets = []
    for f in surface_files:
        ds = xr.open_dataset(f)
        dt_str = f.name.split('-surface-level.nc')[0]
        dt = datetime.strptime(dt_str, '%Y-%m-%d')
        print(f"   Loading {dt.strftime('%b %d, %Y')}: {len(ds.valid_time)} timesteps")
        surf_datasets.append(ds)

    print("   Concatenating datasets...")
    combined_surf = xr.concat(surf_datasets, dim='valid_time')

    print(f"   ✓ Combined: {len(combined_surf.valid_time)} timesteps")
    print(f"   Time range: {combined_surf.valid_time.values[0]} to {combined_surf.valid_time.values[-1]}")

    # Save
    output_surf = data_dir / "texas_2021_surface_jan24-feb21.nc"
    print(f"   Saving to: {output_surf.name}")
    combined_surf.to_netcdf(output_surf)

    surf_size_mb = output_surf.stat().st_size / (1024**2)
    print(f"   ✓ Saved: {output_surf.name} ({surf_size_mb:.1f} MB)")
    print()

    # Combine atmospheric data
    print("2. Combining atmospheric data...")
    atmos_datasets = []
    for f in atmos_files:
        ds = xr.open_dataset(f)
        dt_str = f.name.split('-atmospheric.nc')[0]
        dt = datetime.strptime(dt_str, '%Y-%m-%d')
        print(f"   Loading {dt.strftime('%b %d, %Y')}: {len(ds.valid_time)} timesteps")
        atmos_datasets.append(ds)

    print("   Concatenating datasets...")
    combined_atmos = xr.concat(atmos_datasets, dim='valid_time')

    print(f"   ✓ Combined: {len(combined_atmos.valid_time)} timesteps")
    print(f"   Time range: {combined_atmos.valid_time.values[0]} to {combined_atmos.valid_time.values[-1]}")

    # Save
    output_atmos = data_dir / "texas_2021_atmospheric_jan24-feb21.nc"
    print(f"   Saving to: {output_atmos.name}")
    combined_atmos.to_netcdf(output_atmos)

    atmos_size_mb = output_atmos.stat().st_size / (1024**2)
    print(f"   ✓ Saved: {output_atmos.name} ({atmos_size_mb:.1f} MB)")
    print()

    # Verify
    print("3. Verifying combined files...")
    verify_surf = xr.open_dataset(output_surf)
    verify_atmos = xr.open_dataset(output_atmos)

    print(f"   Surface timesteps: {len(verify_surf.valid_time)}")
    print(f"   First 5 timesteps:")
    for i in range(min(5, len(verify_surf.valid_time))):
        t = verify_surf.valid_time.values[i]
        print(f"     [{i:2d}] {t}")
    print(f"   ...")
    print(f"   Atmospheric timesteps: {len(verify_atmos.valid_time)}")
    print()

    print("=" * 80)
    print("  ✓ Data Combination Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  • Combined {len(surface_files)} days of data")
    print(f"  • Total timesteps: {len(verify_surf.valid_time)} (6-hourly)")
    print(f"  • Date range: Jan 24 - Feb 21, 2021")
    print(f"  • Output files:")
    print(f"      {output_surf.name}")
    print(f"      {output_atmos.name}")
    print()
    print("Next steps:")
    print("  1. Run texas_baseline_analysis.py to identify onset/peak/recovery dates")
    print("  2. Update texas_stage1_detection.py with actual dates")
    print("  3. Run Stage 1 predictions")
    print()


if __name__ == "__main__":
    combine_data()

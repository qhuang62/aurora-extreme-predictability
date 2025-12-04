#!/usr/bin/env python3
"""
Combine Jul 19 - Aug 27, 2023 ERA5 data into single files with continuous timesteps.

After running this, the combined files will have ~160 timesteps:
  Jul 19-31:  13 days × 4 = 52 timesteps
  Aug 1-27:   27 days × 4 = 108 timesteps
  Total:      160 timesteps

This enables:
  • Stage 1: All 4 lead times (1, 7, 14, 21 days) targeting Aug 9 onset
    - 21-day: Init Jul 19, 12 UTC (time_idx 2)
    - 14-day: Init Jul 26, 12 UTC (time_idx 30)
    - 7-day: Init Aug 2, 12 UTC (time_idx 58)
    - 1-day: Init Aug 8, 12 UTC (time_idx 82)
  • Full verification: Aug 1 - Aug 27 (onset → peak → recovery)
    - Aug 9: Onset day (time_idx 86)
    - Aug 23-24: Peak days (time_idx 142-146)
    - Aug 26: Recovery assessment (time_idx 154)
"""

import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta

def combine_data():
    """Combine Jul 19 - Aug 27, 2023 data files into single continuous files."""

    data_dir = Path(__file__).parent

    print("=" * 80)
    print("  Combining Jul 19 - Aug 27, 2023 ERA5 Data for European Heatwave")
    print("=" * 80)
    print()

    # Generate date range (Jul 19 - Aug 27, 2023)
    start_date = datetime(2023, 7, 19)
    end_date = datetime(2023, 8, 27)

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
        print("Run download_heatwave_complete.py first to download all dates.")
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
    output_surf = data_dir / "heatwave_2023_surface_jul19-aug27.nc"
    print(f"   Saving to: {output_surf.name}")
    combined_surf.to_netcdf(output_surf)
    print(f"   ✓ Saved: {output_surf.name}")
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
    output_atmos = data_dir / "heatwave_2023_atmospheric_jul19-aug27.nc"
    print(f"   Saving to: {output_atmos.name}")
    combined_atmos.to_netcdf(output_atmos)
    print(f"   ✓ Saved: {output_atmos.name}")
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
    print(f"   Key initialization times:")
    # Find Jul 19, Jul 26, Aug 2, Aug 8 at 12 UTC
    for i, t in enumerate(verify_surf.valid_time.values):
        t_dt = str(t)
        if ('2023-07-19' in t_dt and '12:00' in t_dt):
            print(f"     [{i:2d}] {t} ← 21-day lead init")
        elif ('2023-07-26' in t_dt and '12:00' in t_dt):
            print(f"     [{i:2d}] {t} ← 14-day lead init")
        elif ('2023-08-02' in t_dt and '12:00' in t_dt):
            print(f"     [{i:2d}] {t} ← 7-day lead init")
        elif ('2023-08-08' in t_dt and '12:00' in t_dt):
            print(f"     [{i:2d}] {t} ← 1-day lead init")
        elif '2023-08-09' in t_dt and '00:00' in t_dt:
            print(f"     [{i:2d}] {t} ← ONSET (Aug 9 00 UTC)")
        elif '2023-08-23' in t_dt and '12:00' in t_dt:
            print(f"     [{i:2d}] {t} ← PEAK (Aug 23 12 UTC)")
        elif '2023-08-24' in t_dt and '12:00' in t_dt:
            print(f"     [{i:2d}] {t} ← PEAK (Aug 24 12 UTC)")
        elif '2023-08-26' in t_dt and '00:00' in t_dt:
            print(f"     [{i:2d}] {t} ← RECOVERY (Aug 26 00 UTC)")

    print()
    print(f"   Atmospheric timesteps: {len(verify_atmos.valid_time)}")
    print()

    print("=" * 80)
    print("  ✓ Data Combination Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  • Combined {len(surface_files)} days of data")
    print(f"  • Total timesteps: {len(verify_surf.valid_time)} (6-hourly)")
    print(f"  • Date range: Jul 19 - Aug 27, 2023")
    print(f"  • Output files:")
    print(f"      {output_surf.name}")
    print(f"      {output_atmos.name}")
    print()
    print("Now you can run Stage 1 analysis:")
    print("  • 21-day lead: Init Jul 19, 12 UTC → Predict Aug 9 onset")
    print("  • 14-day lead: Init Jul 26, 12 UTC → Predict Aug 9 onset")
    print("  • 7-day lead: Init Aug 2, 12 UTC → Predict Aug 9 onset")
    print("  • 1-day lead: Init Aug 8, 12 UTC → Predict Aug 9 onset")
    print()
    print("Research Question: Can Aurora predict heatwave occurrence at subseasonal leads?")
    print()
    print("Individual daily files are preserved. You can delete them if needed.")
    print()


if __name__ == "__main__":
    combine_data()

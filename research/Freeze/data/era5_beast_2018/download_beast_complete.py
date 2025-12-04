#!/usr/bin/env python3
"""
Download complete ERA5 data for Beast from the East (Feb 3 - Mar 2, 2018).

This downloads all dates needed for the two-stage freeze analysis:
  Stage 1 - Detection & Predictability Horizon:
    • Feb 3: 21-day lead (init Feb 3 → predict Feb 24 onset)
    • Feb 10: 14-day lead (init Feb 10 → predict Feb 24 onset)
    • Feb 17: 7-day lead (init Feb 17 → predict Feb 24 onset)
    • Feb 23: 1-day lead (init Feb 23 → predict Feb 24 onset)

  Verification:
    • Feb 22 - Mar 2: Continuous verification period
      - Feb 24: Onset (cold air arrival, T2m < 0°C)
      - Mar 1: Peak (coldest day, maximum spatial extent)
      - Mar 4-5: Recovery (warming begins)

  Stage 2 - Characterization (to be determined from Stage 1 results):
    • Detailed spatial/physical analysis at best lead time from Stage 1

Data range: Feb 3 - Mar 2, 2018 (28 days, ~112 timesteps at 6-hourly)
"""

import cdsapi
from pathlib import Path
from datetime import datetime, timedelta

def download_beast_complete():
    """Download complete Beast from East dataset (Feb 3 - Mar 2, 2018)."""

    c = cdsapi.Client()
    output_dir = Path(__file__).parent

    # Generate list of dates to download (Feb 3 - Mar 2, 2018)
    start_date = datetime(2018, 2, 3)
    end_date = datetime(2018, 3, 2)

    dates_to_download = []
    current_date = start_date
    while current_date <= end_date:
        dates_to_download.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    print("=" * 80)
    print("  Downloading Complete ERA5 Data for Beast from the East")
    print("  February 3 - March 2, 2018 (6-hourly)")
    print("  Total: {} days".format(len(dates_to_download)))
    print("=" * 80)
    print()
    print("Scientific rationale:")
    print("  • Stage 1: Test 1, 7, 14, 21 day lead times targeting Feb 24 onset")
    print("  • Verification: Full event (onset Feb 24 → peak Mar 1 → recovery Mar 5)")
    print("  • Research Question: Can Aurora predict freeze occurrence at subseasonal leads?")
    print()

    for date_str in dates_to_download:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        year = dt.strftime('%Y')
        month = dt.strftime('%m')
        day = dt.strftime('%d')

        print(f"\n{'=' * 80}")
        print(f"  Downloading {dt.strftime('%B %d, %Y')} (6-hourly: 00, 06, 12, 18 UTC)")
        print(f"{'=' * 80}\n")

        # Check if files already exist (RESUME CAPABILITY)
        surface_file = output_dir / f"{date_str}-surface-level.nc"
        atmos_file = output_dir / f"{date_str}-atmospheric.nc"

        if surface_file.exists() and atmos_file.exists():
            print(f"  ✓ {dt.strftime('%b %d')}: Already downloaded, skipping")
            continue

        # Surface-level variables
        if not surface_file.exists():
            print(f"  [{dt.strftime('%b %d')}] Downloading surface-level variables...")
            try:
                c.retrieve(
                    'reanalysis-era5-single-levels',
                    {
                        'product_type': 'reanalysis',
                        'format': 'netcdf',
                        'variable': [
                            '2m_temperature',
                            '10m_u_component_of_wind',
                            '10m_v_component_of_wind',
                            'mean_sea_level_pressure',
                        ],
                        'year': year,
                        'month': month,
                        'day': day,
                        'time': ['00:00', '06:00', '12:00', '18:00'],
                    },
                    str(surface_file)
                )
                print(f"    ✓ Saved: {surface_file.name}")
            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                continue
        else:
            print(f"  [{dt.strftime('%b %d')}] ✓ Surface file exists, skipping")

        # Atmospheric variables (pressure levels)
        if not atmos_file.exists():
            print(f"  [{dt.strftime('%b %d')}] Downloading atmospheric variables...")
            try:
                c.retrieve(
                    'reanalysis-era5-pressure-levels',
                    {
                        'product_type': 'reanalysis',
                        'format': 'netcdf',
                        'variable': [
                            'temperature',
                            'u_component_of_wind',
                            'v_component_of_wind',
                            'specific_humidity',
                            'geopotential',
                        ],
                        'pressure_level': [
                            '50', '100', '150', '200', '250',
                            '300', '400', '500', '600', '700',
                            '850', '925', '1000',
                        ],
                        'year': year,
                        'month': month,
                        'day': day,
                        'time': ['00:00', '06:00', '12:00', '18:00'],
                    },
                    str(atmos_file)
                )
                print(f"    ✓ Saved: {atmos_file.name}")
            except Exception as e:
                print(f"    ✗ ERROR: {e}")
                continue
        else:
            print(f"  [{dt.strftime('%b %d')}] ✓ Atmospheric file exists, skipping")

        print(f"  [{dt.strftime('%b %d')}] ✓ Complete!")

    print("\n" + "=" * 80)
    print("  ✓ Download Complete!")
    print("=" * 80)
    print()
    print("Downloaded {} days of data (Feb 3 - Mar 2, 2018)".format(len(dates_to_download)))
    print()
    print("Next steps:")
    print("  1. Run combine_beast_data.py to merge all dates into single files")
    print("  2. Combined files will have ~112 timesteps (28 days × 4/day)")
    print("  3. Then run beast_stage1_detection.py to test freeze predictability")
    print()


if __name__ == "__main__":
    download_beast_complete()

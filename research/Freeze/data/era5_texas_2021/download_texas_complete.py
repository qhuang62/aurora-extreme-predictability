#!/usr/bin/env python3
"""
Download complete ERA5 data for 2021 Texas Freeze (Jan 24 - Feb 21, 2021).

This downloads all dates needed for the two-stage freeze analysis:
  Stage 1 - Detection & Predictability Horizon:
    • Jan 24: 21-day lead (init Jan 24 → predict Feb 14 onset)
    • Jan 31: 14-day lead (init Jan 31 → predict Feb 14 onset)
    • Feb 7: 7-day lead (init Feb 7 → predict Feb 14 onset)
    • Feb 13: 1-day lead (init Feb 13 → predict Feb 14 onset)

  Verification:
    • Feb 12 - Feb 21: Continuous verification period
      - Feb 14: Onset (Arctic front arrival, T2m < 0°C)
      - Feb 16: Peak (statewide power failure, coldest day)
      - Feb 19-20: Recovery (warming begins)

  Stage 2 - Characterization (to be determined from Stage 1 results):
    • Detailed spatial/physical analysis at best lead time from Stage 1

Event details:
  - Out-of-sample (2021, beyond Aurora's training period 1979-2020)
  - Unprecedented Arctic outbreak for Texas
  - Power grid failure, 246 deaths
  - Wind chill critical (combine T2m + 10m winds)

Data range: Jan 24 - Feb 21, 2021 (29 days, ~116 timesteps at 6-hourly)
"""

import cdsapi
from pathlib import Path
from datetime import datetime, timedelta

def download_texas_complete():
    """Download complete Texas Freeze dataset (Jan 24 - Feb 21, 2021)."""

    c = cdsapi.Client()
    output_dir = Path(__file__).parent

    # Generate list of dates to download (Jan 24 - Feb 21, 2021)
    start_date = datetime(2021, 1, 24)
    end_date = datetime(2021, 2, 21)

    dates_to_download = []
    current_date = start_date
    while current_date <= end_date:
        dates_to_download.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    print("=" * 80)
    print("  Downloading Complete ERA5 Data for 2021 Texas Freeze")
    print("  January 24 - February 21, 2021 (6-hourly)")
    print("  Total: {} days".format(len(dates_to_download)))
    print("=" * 80)
    print()
    print("Scientific rationale:")
    print("  • OUT-OF-SAMPLE event (2021, beyond Aurora training 1979-2020)")
    print("  • Stage 1: Test 1, 7, 14, 21 day lead times targeting Feb 14 onset")
    print("  • Verification: Full event (onset Feb 14 → peak Feb 16 → recovery Feb 20)")
    print("  • Research Question: Can Aurora predict unprecedented Texas freeze?")
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
    print("Downloaded {} days of data (Jan 24 - Feb 21, 2021)".format(len(dates_to_download)))
    print()
    print("Next steps:")
    print("  1. Keep files as individual daily files for now")
    print("  2. Wait until Beast from East (2018) analysis is complete")
    print("  3. Apply lessons learned to Texas event analysis")
    print("  4. Run combine_texas_data.py when ready to analyze")
    print()


if __name__ == "__main__":
    download_texas_complete()

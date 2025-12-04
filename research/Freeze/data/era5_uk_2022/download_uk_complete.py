#!/usr/bin/env python3
"""
Download complete ERA5 data for 2022 UK Cold Wave (Nov 17 - Dec 19, 2022).

This downloads all dates needed for the two-stage freeze analysis:
  Stage 1 - Detection & Predictability Horizon:
    • Nov 17: 21-day lead (init Nov 17 → predict Dec 8 onset)
    • Nov 24: 14-day lead (init Nov 24 → predict Dec 8 onset)
    • Dec 1: 7-day lead (init Dec 1 → predict Dec 8 onset)
    • Dec 7: 1-day lead (init Dec 7 → predict Dec 8 onset)

  Verification:
    • Dec 6 - Dec 19: Continuous verification period
      - Dec 8: Onset (cold snap begins, T2m < 0°C)
      - Dec 12: Peak (widespread snow/ice, coldest day)
      - Dec 16-17: Recovery (warming begins)

  Stage 2 - Characterization (to be determined from Stage 1 results):
    • Detailed spatial/physical analysis at best lead time from Stage 1

Event details:
  - Out-of-sample (2022, well beyond Aurora's training period 1979-2020)
  - Winter cold wave (different from Beast's late Feb/early March timing)
  - Tests Aurora's cold season predictability
  - UK/Ireland focus (smaller region than Beast from East)

Data range: Nov 17 - Dec 19, 2022 (33 days, ~132 timesteps at 6-hourly)
"""

import cdsapi
from pathlib import Path
from datetime import datetime, timedelta

def download_uk_complete():
    """Download complete UK Cold Wave dataset (Nov 17 - Dec 19, 2022)."""

    c = cdsapi.Client()
    output_dir = Path(__file__).parent

    # Generate list of dates to download (Nov 17 - Dec 19, 2022)
    start_date = datetime(2022, 11, 17)
    end_date = datetime(2022, 12, 19)

    dates_to_download = []
    current_date = start_date
    while current_date <= end_date:
        dates_to_download.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    print("=" * 80)
    print("  Downloading Complete ERA5 Data for 2022 UK Cold Wave")
    print("  November 17 - December 19, 2022 (6-hourly)")
    print("  Total: {} days".format(len(dates_to_download)))
    print("=" * 80)
    print()
    print("Scientific rationale:")
    print("  • OUT-OF-SAMPLE event (2022, well beyond Aurora training 1979-2020)")
    print("  • Stage 1: Test 1, 7, 14, 21 day lead times targeting Dec 8 onset")
    print("  • Verification: Full event (onset Dec 8 → peak Dec 12 → recovery Dec 17)")
    print("  • Research Question: Can Aurora predict UK winter cold waves?")
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
    print("Downloaded {} days of data (Nov 17 - Dec 19, 2022)".format(len(dates_to_download)))
    print()
    print("Next steps:")
    print("  1. Keep files as individual daily files for now")
    print("  2. Wait until Beast from East (2018) analysis is complete")
    print("  3. Apply lessons learned to UK event analysis")
    print("  4. Run combine_uk_data.py when ready to analyze")
    print()


if __name__ == "__main__":
    download_uk_complete()

#!/usr/bin/env python3
"""
Download complete ERA5 data for 2023 European Heatwave (Jul 19 - Aug 27, 2023).

This downloads all dates needed for the two-stage heatwave analysis:
  Stage 1 - Detection & Predictability Horizon:
    • Jul 19: 21-day lead (init Jul 19 → predict Aug 9 onset)
    • Jul 26: 14-day lead (init Jul 26 → predict Aug 9 onset)
    • Aug 2: 7-day lead (init Aug 2 → predict Aug 9 onset)
    • Aug 8: 1-day lead (init Aug 8 → predict Aug 9 onset)

  Verification:
    • Aug 1 - Aug 27: Continuous verification period
      - Aug 9: Onset (warm air arrival, T2m > 30°C)
      - Aug 23-24: Peak (hottest days, maximum spatial extent)
      - Aug 26: Recovery (cooling begins)

  Stage 2 - Characterization (to be determined from Stage 1 results):
    • Detailed spatial/physical analysis at best lead time from Stage 1

Data range: Jul 19 - Aug 27, 2023 (40 days, ~160 timesteps at 6-hourly)
"""

import cdsapi
from pathlib import Path
from datetime import datetime, timedelta

def download_heatwave_complete():
    """Download complete European Heatwave 2023 dataset (Jul 19 - Aug 27, 2023)."""

    c = cdsapi.Client()
    output_dir = Path(__file__).parent

    # Generate list of dates to download (Jul 19 - Aug 27, 2023)
    start_date = datetime(2023, 7, 19)
    end_date = datetime(2023, 8, 27)

    dates_to_download = []
    current_date = start_date
    while current_date <= end_date:
        dates_to_download.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    print("=" * 80)
    print("  Downloading Complete ERA5 Data for 2023 European Heatwave")
    print("  July 19 - August 27, 2023 (6-hourly)")
    print("  Total: {} days".format(len(dates_to_download)))
    print("=" * 80)
    print()
    print("Scientific rationale:")
    print("  • Stage 1: Test 1, 7, 14, 21 day lead times targeting Aug 9 onset")
    print("  • Verification: Full event (onset Aug 9 → peak Aug 23-24 → recovery Aug 26)")
    print("  • Research Question: Can Aurora predict heatwave occurrence at subseasonal leads?")
    print("  • Complements freeze events: Tests Aurora on opposite temperature extreme")
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
    print("Downloaded {} days of data (Jul 19 - Aug 27, 2023)".format(len(dates_to_download)))
    print()
    print("Next steps:")
    print("  1. Run combine_heatwave_data.py to merge all dates into single files")
    print("  2. Combined files will have ~160 timesteps (40 days × 4/day)")
    print("  3. Then run heatwave_stage1_detection.py to test heatwave predictability")
    print()


if __name__ == "__main__":
    download_heatwave_complete()

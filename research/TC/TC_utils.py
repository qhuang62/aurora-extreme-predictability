"""
Tropical Cyclone (TC) specific utilities.

This module contains functions specific to TC analysis:
- IBTrACS data loading
- Track extraction from Aurora predictions
- TC-specific metrics (track error, landfall timing)
- TC-specific visualizations
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


def load_ibtracs_track(storm_name, year, data_path=None):
    """
    Load IBTrACS observational track data.

    Parameters
    ----------
    storm_name : str
        Storm name (e.g., 'SANDY', 'NANMADOL', 'IAN')
    year : int
        Storm year
    data_path : Path or str or None, optional
        Path to IBTrACS data. If None, returns hardcoded track if available.

    Returns
    -------
    dict
        Dictionary with keys:
        - 'time': list of datetime objects
        - 'lat': list of float (degrees N)
        - 'lon': list of float (degrees E, 0-360)
        - 'name': storm name
        - 'year': storm year

    Notes
    -----
    If data_path is provided, will attempt to read from IBTrACS NetCDF file.
    Otherwise, returns hardcoded tracks for known storms.
    """
    storm_key = f"{storm_name.upper()}_{year}"

    # Hardcoded tracks for completed events
    # Source: IBTrACS (International Best Track Archive for Climate Stewardship)
    # https://ncics.org/ibtracs/
    TRACKS = {
        'SANDY_2012': {
            # Hurricane Sandy track data from IBTrACS v04r01
            # Storm ID: 2012296N14283
            # Source: https://ncics.org/ibtracs/index.php?name=v04r01-2012296N14283
            # Period: Oct 22-31, 2012 (6-hourly observations)
            # Coordinates: Latitude (°N), Longitude (0-360°E, converted from -180-180°W)
            'time': [
                "2012-10-22 00:00", "2012-10-22 06:00", "2012-10-22 12:00", "2012-10-22 18:00",
                "2012-10-23 00:00", "2012-10-23 06:00", "2012-10-23 12:00", "2012-10-23 18:00",
                "2012-10-24 00:00", "2012-10-24 06:00", "2012-10-24 12:00", "2012-10-24 18:00",
                "2012-10-25 00:00", "2012-10-25 06:00", "2012-10-25 12:00",
                "2012-10-25 18:00", "2012-10-26 00:00", "2012-10-26 06:00",
                "2012-10-26 12:00", "2012-10-26 18:00", "2012-10-27 00:00",
                "2012-10-27 06:00", "2012-10-27 12:00", "2012-10-27 18:00",
                "2012-10-28 00:00", "2012-10-28 06:00", "2012-10-28 12:00",
                "2012-10-28 18:00", "2012-10-29 00:00", "2012-10-29 06:00",
                "2012-10-29 12:00", "2012-10-29 18:00", "2012-10-30 00:00",
                "2012-10-30 06:00", "2012-10-30 12:00", "2012-10-30 18:00",
                "2012-10-31 00:00"
            ],
            'lat': [
                # Oct 22-23 (early stage over Caribbean)
                13.9, 13.5, 13.1, 12.7, 12.6, 12.9, 13.4, 14.0,
                # Oct 24-31 (intensification, northward turn, landfall, dissipation)
                14.7, 15.6, 16.6, 17.7, 18.9, 20.1, 21.7, 23.3, 24.8, 25.7,
                26.4, 27.0, 27.5, 28.1, 28.8, 29.7, 30.5, 31.3, 32.0,
                32.8, 33.9, 35.3, 36.9, 38.3, 39.5, 39.9, 40.1, 40.4, 40.7
            ],
            'lon': [
                # Oct 22-23: -77.8°W to -77.6°W (converted to 0-360°E)
                282.2, 281.8, 281.4, 281.3, 281.6, 281.9, 282.1, 282.4,
                # Oct 24-31: Northward track along US East Coast
                282.7, 282.9, 283.1, 283.3, 283.6, 284.0, 284.5, 284.7, 284.1,
                283.6, 283.1, 282.8, 282.9, 283.1, 283.5, 284.4, 285.3,
                286.1, 287.0, 288.0, 289.0, 289.5, 289.0, 286.8, 285.5,
                283.8, 282.2, 281.1, 280.2
            ]
        },
        'NANMADOL_2022': {
            'time': [
                "2022-09-17 12:00", "2022-09-17 18:00", "2022-09-18 00:00",
                "2022-09-18 06:00", "2022-09-18 12:00", "2022-09-18 18:00",
                "2022-09-19 00:00", "2022-09-19 06:00", "2022-09-19 12:00"
            ],
            'lat': [
                27.5, 28.2, 28.9, 29.7, 30.6, 31.6, 32.7, 34.0, 35.5
            ],
            'lon': [
                132.0, 131.8, 131.6, 131.3, 131.0, 130.7, 130.4, 130.2, 130.1
            ]
        },
        'IAN_2022': {
            # Hurricane Ian track data from IBTrACS v04r01
            # Storm ID: 2022266N12294
            # Source: https://ncics.org/ibtracs/index.php?name=v04r01-2022266N12294
            # Period: Sep 22-30, 2022 (6-hourly observations)
            # Landfall: Sep 28, 2022 20:00 UTC (Florida, USA)
            # Coordinates: Latitude (°N), Longitude (0-360°E, converted from -180-180°W)
            'time': [
                # Sep 22 (genesis)
                "2022-09-22 18:00",
                # Sep 23
                "2022-09-23 00:00", "2022-09-23 06:00", "2022-09-23 12:00", "2022-09-23 18:00",
                # Sep 24
                "2022-09-24 00:00", "2022-09-24 06:00", "2022-09-24 12:00", "2022-09-24 18:00",
                # Sep 25
                "2022-09-25 00:00", "2022-09-25 06:00", "2022-09-25 12:00", "2022-09-25 18:00",
                # Sep 26
                "2022-09-26 00:00", "2022-09-26 06:00", "2022-09-26 12:00", "2022-09-26 18:00",
                # Sep 27
                "2022-09-27 00:00", "2022-09-27 06:00", "2022-09-27 12:00", "2022-09-27 18:00",
                # Sep 28 (landfall day, peak intensity at 12:00 UTC: 140 kt, 937 mb)
                "2022-09-28 00:00", "2022-09-28 06:00", "2022-09-28 12:00", "2022-09-28 18:00",
                # Sep 29 (post-landfall)
                "2022-09-29 00:00", "2022-09-29 06:00", "2022-09-29 12:00", "2022-09-29 18:00",
                # Sep 30 (transition)
                "2022-09-30 00:00", "2022-09-30 06:00", "2022-09-30 12:00", "2022-09-30 18:00"
            ],
            'lat': [
                # Sep 22-23 (genesis, tropical storm)
                12.30, 12.90, 13.70, 14.20, 14.60,
                # Sep 24 (tropical storm)
                14.70, 14.70, 14.50, 14.40,
                # Sep 25 (approaching Gulf)
                14.60, 14.60, 15.00, 15.80,
                # Sep 26 (entering Gulf, intensifying)
                16.80, 17.70, 18.70, 19.70,
                # Sep 27 (rapid intensification)
                20.80, 21.80, 22.60, 23.50,
                # Sep 28 (major hurricane, landfall)
                24.40, 25.20, 26.00, 26.60,
                # Sep 29 (inland, weakening)
                27.20, 27.70, 28.40, 28.90,
                # Sep 30 (extratropical transition)
                29.60, 30.30, 31.50, 33.30
            ],
            'lon': [
                # Sep 22-23: -66.30°W to -70.60°W (converted to 0-360°E)
                293.70, 292.80, 291.90, 290.70, 289.40,
                # Sep 24: Westward over Caribbean
                288.30, 287.10, 285.60, 284.20,
                # Sep 25: NW Caribbean
                282.80, 281.70, 280.60, 279.90,
                # Sep 26: Entering Gulf
                279.10, 278.30, 277.60, 277.00,
                # Sep 27: Gulf of Mexico, northward turn
                276.70, 276.40, 276.40, 276.70,
                # Sep 28: Approaching and making landfall (20:00 UTC landfall ~26.80°N, 278.0°E)
                277.00, 277.10, 277.30, 277.60,
                # Sep 29: Inland over Florida
                278.30, 278.90, 279.40, 279.90,
                # Sep 30: Moving northeast
                280.60, 280.90, 281.00, 280.80
            ]
        },
        'HINNAMNOR_2022': {
            # Typhoon Hinnamnor track data from IBTrACS v04r01
            # Storm ID: 2022239N22150
            # Source: https://ncics.org/ibtracs/index.php?name=v04r01-2022239N22150
            # Period: Aug 28 - Sep 9, 2022 (6-hourly observations)
            # Landfall: Sep 6, 2022 18:00 UTC (South Korea, near Geoje)
            # Peak Intensity: Aug 30-31, 2022 (145 kt, 910 mb - Category 5 super typhoon)
            # Coordinates: Latitude (°N), Longitude (already in 0-360°E for Western Pacific)
            'time': [
                # Aug 28 (formation east of Japan)
                "2022-08-28 00:00", "2022-08-28 06:00", "2022-08-28 12:00", "2022-08-28 18:00",
                # Aug 29 (rapid intensification)
                "2022-08-29 00:00", "2022-08-29 06:00", "2022-08-29 12:00", "2022-08-29 18:00",
                # Aug 30 (peak Cat 5 intensity)
                "2022-08-30 00:00", "2022-08-30 06:00", "2022-08-30 12:00", "2022-08-30 18:00",
                # Aug 31 (weakening begins)
                "2022-08-31 00:00", "2022-08-31 06:00", "2022-08-31 12:00", "2022-08-31 18:00",
                # Sep 1 (stalling phase begins)
                "2022-09-01 00:00", "2022-09-01 06:00", "2022-09-01 12:00", "2022-09-01 18:00",
                # Sep 2 (stalling continues)
                "2022-09-02 00:00", "2022-09-02 06:00", "2022-09-02 12:00", "2022-09-02 18:00",
                # Sep 3 (stalling ends, northward turn begins)
                "2022-09-03 00:00", "2022-09-03 06:00", "2022-09-03 12:00", "2022-09-03 18:00",
                # Sep 4 (accelerating northward)
                "2022-09-04 00:00", "2022-09-04 06:00", "2022-09-04 12:00", "2022-09-04 18:00",
                # Sep 5 (rapid northward movement)
                "2022-09-05 00:00", "2022-09-05 06:00", "2022-09-05 12:00", "2022-09-05 18:00",
                # Sep 6 (landfall day, South Korea)
                "2022-09-06 00:00", "2022-09-06 06:00", "2022-09-06 12:00", "2022-09-06 18:00",
                # Sep 7 (extratropical transition)
                "2022-09-07 00:00", "2022-09-07 06:00", "2022-09-07 12:00", "2022-09-07 18:00",
                # Sep 8 (extratropical)
                "2022-09-08 00:00", "2022-09-08 06:00", "2022-09-08 12:00", "2022-09-08 18:00",
                # Sep 9 (dissipating)
                "2022-09-09 00:00"
            ],
            'lat': [
                # Aug 28: Formation and early development
                25.00, 25.90, 26.70, 27.20,
                # Aug 29: Rapid intensification
                27.30, 27.40, 27.30, 27.10,
                # Aug 30: Peak intensity (Cat 5)
                26.80, 26.80, 26.60, 26.30,
                # Aug 31: Weakening, westward drift
                25.90, 25.40, 24.70, 23.70,
                # Sep 1: Stalling phase (21-22°N)
                22.50, 21.80, 21.30, 21.30,
                # Sep 2: Stalling continues (21-22°N)
                21.50, 21.90, 22.20, 22.50,
                # Sep 3: Northward turn begins (23-25°N)
                23.00, 23.70, 24.30, 25.10,
                # Sep 4: Accelerating north (26-29°N)
                26.00, 27.00, 27.70, 28.60,
                # Sep 5: Rapid acceleration (30-34°N)
                29.80, 31.00, 32.40, 34.20,
                # Sep 6: Landfall and extratropical transition (36-48°N)
                36.40, 39.80, 44.10, 47.80,
                # Sep 7: Extratropical (53-57°N)
                52.60, 54.70, 55.80, 56.80,
                # Sep 8: Extratropical (58-60°N)
                58.00, 58.40, 58.90, 59.80,
                # Sep 9: Dissipating
                61.70
            ],
            'lon': [
                # Aug 28: East of Japan
                150.30, 149.40, 148.40, 146.90,
                # Aug 29: Westward movement
                145.30, 143.20, 141.20, 139.20,
                # Aug 30: Peak intensity, westward drift
                137.30, 135.40, 133.60, 131.90,
                # Aug 31: Approaching East China Sea
                130.30, 129.00, 127.70, 126.40,
                # Sep 1: Stalling phase (125-126°E)
                125.70, 125.50, 125.50, 125.50,
                # Sep 2: Stalling continues (124-125°E)
                125.40, 125.00, 124.70, 124.70,
                # Sep 3: Slight northwestward drift (124-125°E)
                124.70, 124.70, 124.80, 124.60,
                # Sep 4: Northward turn (124-125°E)
                124.60, 124.70, 124.60, 124.70,
                # Sep 5: Approaching Korea (125-128°E)
                124.90, 125.60, 126.60, 128.10,
                # Sep 6: Landfall and rapid eastward movement (130-139°E)
                130.50, 133.60, 137.10, 139.00,
                # Sep 7: Extratropical track (138-141°E)
                138.50, 139.10, 139.10, 140.80,
                # Sep 8: Extratropical (143-149°E)
                142.90, 145.00, 147.10, 149.40,
                # Sep 9: Dissipating
                149.90
            ]
        },
        'AMPHAN_2020': {
            # Cyclone Amphan track data from IBTrACS v04r01
            # Storm ID: 2020136N10088
            # Source: https://ncics.org/ibtracs/index.php?name=v04r01-2020136N10088
            # Period: May 15 - May 21, 2020 (6-hourly observations from 3-hourly source)
            # Landfall: May 20, 2020 12:00 UTC (Bangladesh, near 22.1°N, 88.4°E)
            # Peak Intensity: May 18, 2020 12:00 UTC (125 kt, 926 mb - Super Cyclone)
            # Coordinates: Latitude (°N), Longitude (already in °E for Bay of Bengal)
            'time': [
                # May 15 (genesis at 06:00 UTC)
                "2020-05-15 06:00", "2020-05-15 12:00", "2020-05-15 18:00",
                # May 16 (tropical storm)
                "2020-05-16 00:00", "2020-05-16 06:00", "2020-05-16 12:00", "2020-05-16 18:00",
                # May 17 (rapid intensification begins)
                "2020-05-17 00:00", "2020-05-17 06:00", "2020-05-17 12:00", "2020-05-17 18:00",
                # May 18 (peak super cyclone intensity)
                "2020-05-18 00:00", "2020-05-18 06:00", "2020-05-18 12:00", "2020-05-18 18:00",
                # May 19 (weakening, approaching Bangladesh)
                "2020-05-19 00:00", "2020-05-19 06:00", "2020-05-19 12:00", "2020-05-19 18:00",
                # May 20 (landfall day at 12:00 UTC)
                "2020-05-20 00:00", "2020-05-20 06:00", "2020-05-20 12:00",
                # May 21 (post-landfall dissipation)
                "2020-05-21 00:00", "2020-05-21 06:00", "2020-05-21 12:00"
            ],
            'lat': [
                # May 15: Genesis and early development
                9.50, 9.50, 9.50,
                # May 16: Slow northward drift
                9.80, 10.30, 10.60, 10.90,
                # May 17: Rapid intensification
                11.20, 11.50, 11.90, 12.50,
                # May 18: Peak intensity (super cyclone)
                13.20, 13.40, 14.10, 14.90,
                # May 19: Weakening, northward acceleration
                15.60, 16.50, 17.30, 18.30,
                # May 20: Landfall at Bangladesh (12:00 UTC at 22.1°N)
                19.20, 20.60, 22.10,
                # May 21: Post-landfall
                24.60, 25.40, 25.40
            ],
            'lon': [
                # May 15: Bay of Bengal
                87.50, 87.00, 86.60,
                # May 16: Westward drift
                86.40, 86.10, 86.20, 86.10,
                # May 17: Slight northward movement
                86.10, 86.20, 86.20, 86.40,
                # May 18: Peak intensity
                86.40, 86.20, 86.40, 86.60,
                # May 19: Approaching Bangladesh coast
                86.80, 87.00, 87.10, 87.20,
                # May 20: Landfall (12:00 UTC at 88.4°E)
                87.50, 88.00, 88.40,
                # May 21: Inland
                89.60, 90.10, 89.60
            ]
        }
    }

    if data_path is not None:
        # TODO: Implement IBTrACS NetCDF reading
        raise NotImplementedError("IBTrACS NetCDF reading not yet implemented")

    if storm_key not in TRACKS:
        raise ValueError(f"No hardcoded track for {storm_key}. Available: {list(TRACKS.keys())}")

    track_data = TRACKS[storm_key].copy()

    # Convert time strings to datetime objects
    track_data['time'] = [datetime.strptime(t, "%Y-%m-%d %H:%M") for t in track_data['time']]
    track_data['name'] = storm_name.upper()
    track_data['year'] = year

    return track_data


def extract_track_from_tracker(tracker, init_time):
    """
    Extract track from Aurora Tracker object.

    Parameters
    ----------
    tracker : aurora.Tracker
        Tracker object after running forecast
    init_time : datetime
        Initialization time (not used, kept for compatibility)

    Returns
    -------
    dict
        Dictionary with keys:
        - 'time': list of datetime objects
        - 'lat': list of float
        - 'lon': list of float

    Notes
    -----
    Aurora tracker stores tracked positions in:
    - tracker.tracked_lats
    - tracker.tracked_lons
    - tracker.tracked_times
    Can also use tracker.results() which returns a pandas DataFrame.
    """
    # Check if tracker has any tracked positions
    if not hasattr(tracker, 'tracked_lats') or len(tracker.tracked_lats) == 0:
        print("Warning: Tracker has no tracked positions!")
        return {'time': [], 'lat': [], 'lon': []}

    # Get results as DataFrame
    try:
        df = tracker.results()

        # DataFrame has columns: time, lat, lon, msl, wind
        track = {
            'time': df['time'].tolist(),
            'lat': df['lat'].tolist(),
            'lon': df['lon'].tolist()
        }

        return track

    except Exception as e:
        print(f"Warning: Could not extract track from tracker: {e}")

        # Fallback: use attributes directly
        track = {
            'time': list(tracker.tracked_times) if hasattr(tracker, 'tracked_times') else [],
            'lat': list(tracker.tracked_lats) if hasattr(tracker, 'tracked_lats') else [],
            'lon': list(tracker.tracked_lons) if hasattr(tracker, 'tracked_lons') else []
        }

        return track


def compute_track_error(forecast_track, obs_track, interpolate_obs=True):
    """
    Compute track error at each forecast timestep.

    Parameters
    ----------
    forecast_track : dict
        Forecast track with 'time', 'lat', 'lon'
    obs_track : dict
        Observed track with 'time', 'lat', 'lon'
    interpolate_obs : bool, optional
        Interpolate observed track to forecast times (default: True)

    Returns
    -------
    dict
        Dictionary with keys:
        - 'lead_times': array of lead times in hours
        - 'errors': array of position errors in km
        - 'valid_times': list of valid forecast times

    Notes
    -----
    Uses haversine distance to compute great circle distance.
    If observed track doesn't cover full forecast period, returns
    errors only for overlapping times.
    """
    from shared.metrics import calculate_distance

    if len(forecast_track['time']) == 0:
        return {'lead_times': np.array([]), 'errors': np.array([]), 'valid_times': []}

    errors = []
    lead_times = []
    valid_times = []

    forecast_times = forecast_track['time']
    forecast_lats = forecast_track['lat']
    forecast_lons = forecast_track['lon']

    obs_times = obs_track['time']
    obs_lats = np.array(obs_track['lat'])
    obs_lons = np.array(obs_track['lon'])

    init_time = forecast_times[0]

    for i, (fcst_time, fcst_lat, fcst_lon) in enumerate(zip(forecast_times, forecast_lats, forecast_lons)):
        # Find corresponding observed position
        if interpolate_obs:
            # Linear interpolation
            if fcst_time < obs_times[0]:
                # Before genesis: use genesis position (first observation)
                obs_lat = obs_lats[0]
                obs_lon = obs_lons[0]
            elif fcst_time > obs_times[-1]:
                # After dissipation: use last observation
                obs_lat = obs_lats[-1]
                obs_lon = obs_lons[-1]
            else:
                # Within observed period: interpolate
                # Find surrounding times
                obs_times_seconds = [(t - obs_times[0]).total_seconds() for t in obs_times]
                fcst_time_seconds = (fcst_time - obs_times[0]).total_seconds()

                # Interpolate lat/lon
                obs_lat = np.interp(fcst_time_seconds, obs_times_seconds, obs_lats)
                obs_lon = np.interp(fcst_time_seconds, obs_times_seconds, obs_lons)
        else:
            # Find closest time
            if fcst_time < obs_times[0]:
                # Before genesis: use genesis position (first observation)
                obs_lat = obs_lats[0]
                obs_lon = obs_lons[0]
            elif fcst_time > obs_times[-1]:
                # After dissipation: use last observation
                obs_lat = obs_lats[-1]
                obs_lon = obs_lons[-1]
            else:
                # Within observed period: find closest
                time_diffs = [abs((t - fcst_time).total_seconds()) for t in obs_times]
                closest_idx = np.argmin(time_diffs)

                # Only use if within 3 hours
                if time_diffs[closest_idx] > 3*3600:
                    continue

                obs_lat = obs_lats[closest_idx]
                obs_lon = obs_lons[closest_idx]

        # Compute distance error
        error_km = calculate_distance(fcst_lat, fcst_lon, obs_lat, obs_lon)

        errors.append(error_km)
        lead_time_hours = (fcst_time - init_time).total_seconds() / 3600
        lead_times.append(lead_time_hours)
        valid_times.append(fcst_time)

    return {
        'lead_times': np.array(lead_times),
        'errors': np.array(errors),
        'valid_times': valid_times
    }


def compute_landfall_error(forecast_track, obs_track, landfall_threshold_lon=-80.0):
    """
    Compute landfall timing and location error.

    Parameters
    ----------
    forecast_track : dict
        Forecast track
    obs_track : dict
        Observed track
    landfall_threshold_lon : float, optional
        Longitude threshold for landfall (default: -80.0 for US East Coast)

    Returns
    -------
    dict
        Dictionary with keys:
        - 'forecast_landfall_time': datetime or None
        - 'observed_landfall_time': datetime or None
        - 'timing_error_hours': float or None
        - 'location_error_km': float or None

    Notes
    -----
    Landfall is defined as crossing the landfall_threshold_lon.
    For US East Coast landfalls, use -80.0 (280.0 in 0-360 format).
    """
    from shared.metrics import calculate_distance

    def find_landfall(track, threshold_lon):
        """Find first time crossing threshold longitude"""
        for i in range(len(track['lon']) - 1):
            lon1 = track['lon'][i]
            lon2 = track['lon'][i+1]

            # Convert to -180 to 180 if needed
            if lon1 > 180:
                lon1 = lon1 - 360
            if lon2 > 180:
                lon2 = lon2 - 360

            # Check if crossed threshold (moving westward)
            if lon1 > threshold_lon and lon2 <= threshold_lon:
                # Interpolate to find exact crossing
                return {
                    'time': track['time'][i],
                    'lat': track['lat'][i],
                    'lon': track['lon'][i]
                }

        return None

    fcst_landfall = find_landfall(forecast_track, landfall_threshold_lon)
    obs_landfall = find_landfall(obs_track, landfall_threshold_lon)

    result = {
        'forecast_landfall_time': fcst_landfall['time'] if fcst_landfall else None,
        'observed_landfall_time': obs_landfall['time'] if obs_landfall else None,
        'timing_error_hours': None,
        'location_error_km': None
    }

    if fcst_landfall and obs_landfall:
        # Timing error
        timing_diff = fcst_landfall['time'] - obs_landfall['time']
        result['timing_error_hours'] = timing_diff.total_seconds() / 3600

        # Location error
        result['location_error_km'] = calculate_distance(
            fcst_landfall['lat'], fcst_landfall['lon'],
            obs_landfall['lat'], obs_landfall['lon']
        )

    return result


def summarize_track_performance(forecast_track, obs_track, init_time, event_name):
    """
    Generate comprehensive track performance summary.

    Parameters
    ----------
    forecast_track : dict
        Forecast track
    obs_track : dict
        Observed track
    init_time : datetime
        Initialization time
    event_name : str
        Event name for reporting

    Returns
    -------
    dict
        Summary statistics

    Example
    -------
    >>> summary = summarize_track_performance(
    ...     forecast_track, obs_track,
    ...     datetime(2012, 10, 24, 12),
    ...     "Hurricane Sandy"
    ... )
    >>> print(f"24h error: {summary['error_24h']:.1f} km")
    >>> print(f"Max error: {summary['max_error']:.1f} km")
    """
    errors_data = compute_track_error(forecast_track, obs_track)

    if len(errors_data['errors']) == 0:
        return None

    lead_times = errors_data['lead_times']
    errors = errors_data['errors']

    summary = {
        'event_name': event_name,
        'init_time': init_time,
        'forecast_length_hours': lead_times[-1] if len(lead_times) > 0 else 0,
        'mean_error': np.mean(errors),
        'max_error': np.max(errors),
        'final_error': errors[-1] if len(errors) > 0 else None,
    }

    # Add errors at specific lead times
    for target_hours in [24, 48, 72, 96, 120]:
        idx = np.argmin(np.abs(lead_times - target_hours))
        if np.abs(lead_times[idx] - target_hours) < 12:  # Within 12 hours
            summary[f'error_{target_hours}h'] = errors[idx]
        else:
            summary[f'error_{target_hours}h'] = None

    return summary


def extract_field_from_predictions(predictions, variable, time_idx=None, level_idx=None):
    """
    Extract a meteorological field from Aurora predictions.

    Parameters
    ----------
    predictions : list of dict or list of aurora.Batch
        List of prediction batches (either saved dicts or Batch objects)
    variable : str
        Variable name ('msl', '10u', '10v', 'z', 't', etc.)
    time_idx : int or None, optional
        Time index to extract. If None, extracts all times.
    level_idx : int or None, optional
        Pressure level index for atmospheric variables.
        Required for atmos variables, ignored for surface variables.

    Returns
    -------
    dict
        Dictionary with keys:
        - 'data': numpy array (2D if single time, 3D if all times)
        - 'lat': latitude array
        - 'lon': longitude array
        - 'time': datetime or list of datetimes

    Example
    -------
    >>> # Extract MSL at landfall time (time_idx=30)
    >>> msl = extract_field_from_predictions(preds, 'msl', time_idx=30)
    >>> # Extract 850 hPa winds
    >>> u850 = extract_field_from_predictions(preds, 'u', time_idx=30, level_idx=10)
    """
    if len(predictions) == 0:
        raise ValueError("Predictions list is empty")

    # Determine if we have dict or Batch objects
    first_pred = predictions[0]
    is_dict = isinstance(first_pred, dict)

    if time_idx is not None:
        if time_idx >= len(predictions):
            raise ValueError(f"time_idx {time_idx} out of range (only {len(predictions)} timesteps)")
        pred = predictions[time_idx]
    else:
        pred = predictions

    # Surface variables
    surf_vars = ['msl', '2t', '10u', '10v']
    # Atmospheric variables
    atmos_vars = ['z', 't', 'u', 'v', 'q']

    if variable in surf_vars:
        if time_idx is not None:
            if is_dict:
                data = pred['surf_vars'][variable][0, 0]  # Remove batch and time dims
                lat = pred['metadata']['lat']
                lon = pred['metadata']['lon']
                time = pred['metadata']['time'][0]
            else:
                data = pred.surf_vars[variable][0, 0].cpu().numpy()
                lat = pred.metadata.lat.cpu().numpy()
                lon = pred.metadata.lon.cpu().numpy()
                time = pred.metadata.time[0]
        else:
            # Extract all times
            if is_dict:
                data = np.stack([p['surf_vars'][variable][0, 0] for p in predictions], axis=0)
                lat = predictions[0]['metadata']['lat']
                lon = predictions[0]['metadata']['lon']
                time = [p['metadata']['time'][0] for p in predictions]
            else:
                data = np.stack([p.surf_vars[variable][0, 0].cpu().numpy() for p in predictions], axis=0)
                lat = predictions[0].metadata.lat.cpu().numpy()
                lon = predictions[0].metadata.lon.cpu().numpy()
                time = [p.metadata.time[0] for p in predictions]

    elif variable in atmos_vars:
        if level_idx is None:
            raise ValueError(f"level_idx required for atmospheric variable '{variable}'")

        if time_idx is not None:
            if is_dict:
                data = pred['atmos_vars'][variable][0, 0, level_idx]
                lat = pred['metadata']['lat']
                lon = pred['metadata']['lon']
                time = pred['metadata']['time'][0]
            else:
                data = pred.atmos_vars[variable][0, 0, level_idx].cpu().numpy()
                lat = pred.metadata.lat.cpu().numpy()
                lon = pred.metadata.lon.cpu().numpy()
                time = pred.metadata.time[0]
        else:
            # Extract all times
            if is_dict:
                data = np.stack([p['atmos_vars'][variable][0, 0, level_idx] for p in predictions], axis=0)
                lat = predictions[0]['metadata']['lat']
                lon = predictions[0]['metadata']['lon']
                time = [p['metadata']['time'][0] for p in predictions]
            else:
                data = np.stack([p.atmos_vars[variable][0, 0, level_idx].cpu().numpy() for p in predictions], axis=0)
                lat = predictions[0].metadata.lat.cpu().numpy()
                lon = predictions[0].metadata.lon.cpu().numpy()
                time = [p.metadata.time[0] for p in predictions]
    else:
        raise ValueError(f"Unknown variable '{variable}'. Must be one of {surf_vars + atmos_vars}")

    return {
        'data': data,
        'lat': lat,
        'lon': lon,
        'time': time
    }


def compare_fields_at_landfall(aurora_predictions, era5_surf_ds, era5_atmos_ds,
                                landfall_time_idx, landfall_lat, landfall_lon,
                                region_extent=None):
    """
    Compare Aurora and ERA5 meteorological fields at landfall time.

    Parameters
    ----------
    aurora_predictions : list of dict or list of aurora.Batch
        Aurora predictions
    era5_surf_ds : xarray.Dataset
        ERA5 surface variables
    era5_atmos_ds : xarray.Dataset
        ERA5 atmospheric variables
    landfall_time_idx : int
        Index of landfall time in predictions
    landfall_lat : float
        Landfall latitude
    landfall_lon : float
        Landfall longitude
    region_extent : list or None, optional
        [lon_min, lon_max, lat_min, lat_max] for regional extraction

    Returns
    -------
    dict
        Comparison results with keys:
        - 'msl': {aurora, era5, difference, aurora_min, era5_min, center_diff_km}
        - 'wind': {aurora, era5, difference, aurora_max, era5_max}
        - 'z700': {aurora, era5, difference}
        - 'lat': latitude array
        - 'lon': longitude array
        - 'landfall_position': (lat, lon)

    Example
    -------
    >>> comparison = compare_fields_at_landfall(
    ...     preds, era5_surf, era5_atmos,
    ...     time_idx=30, landfall_lat=38.3, landfall_lon=286.8,
    ...     region_extent=[280, 295, 30, 45]
    ... )
    """
    import xarray as xr
    from shared.metrics import calculate_distance

    # Extract Aurora fields
    print(f"Extracting Aurora fields at time index {landfall_time_idx}...")
    aurora_msl = extract_field_from_predictions(aurora_predictions, 'msl', time_idx=landfall_time_idx)
    aurora_10u = extract_field_from_predictions(aurora_predictions, '10u', time_idx=landfall_time_idx)
    aurora_10v = extract_field_from_predictions(aurora_predictions, '10v', time_idx=landfall_time_idx)

    # Z700 is at index 9 in pressure levels (50, 100, 150, 200, 250, 300, 400, 500, 600, 700)
    aurora_z700 = extract_field_from_predictions(aurora_predictions, 'z', time_idx=landfall_time_idx, level_idx=9)

    # Compute wind speed
    aurora_wind = np.sqrt(aurora_10u['data']**2 + aurora_10v['data']**2)

    # Extract ERA5 fields at same time
    print(f"Extracting ERA5 fields...")
    # Find corresponding time in ERA5
    time_val = aurora_msl['time']

    era5_msl_data = era5_surf_ds['msl'].sel(valid_time=time_val, method='nearest').values
    era5_10u_data = era5_surf_ds['u10'].sel(valid_time=time_val, method='nearest').values
    era5_10v_data = era5_surf_ds['v10'].sel(valid_time=time_val, method='nearest').values
    era5_wind = np.sqrt(era5_10u_data**2 + era5_10v_data**2)

    # Z700 from ERA5
    era5_z700_data = era5_atmos_ds['z'].sel(
        valid_time=time_val,
        pressure_level=700,
        method='nearest'
    ).values

    # Get coordinates
    lat = aurora_msl['lat']
    lon = aurora_msl['lon']

    # Regional subset if requested
    if region_extent is not None:
        lon_min, lon_max, lat_min, lat_max = region_extent
        lat_mask = (lat >= lat_min) & (lat <= lat_max)
        lon_mask = (lon >= lon_min) & (lon <= lon_max)

        lat = lat[lat_mask]
        lon = lon[lon_mask]

        aurora_msl_data = aurora_msl['data'][np.ix_(lat_mask, lon_mask)]
        aurora_wind_data = aurora_wind[np.ix_(lat_mask, lon_mask)]
        aurora_z700_data = aurora_z700['data'][np.ix_(lat_mask, lon_mask)]

        era5_msl_data = era5_msl_data[np.ix_(lat_mask, lon_mask)]
        era5_wind_data = era5_wind[np.ix_(lat_mask, lon_mask)]
        era5_z700_data = era5_z700_data[np.ix_(lat_mask, lon_mask)]
    else:
        aurora_msl_data = aurora_msl['data']
        aurora_wind_data = aurora_wind
        aurora_z700_data = aurora_z700['data']

    # Find minima/maxima
    aurora_msl_min = np.min(aurora_msl_data)
    era5_msl_min = np.min(era5_msl_data)

    aurora_wind_max = np.max(aurora_wind_data)
    era5_wind_max = np.max(era5_wind_data)

    # Find center positions (MSL minimum)
    aurora_min_pos = np.unravel_index(np.argmin(aurora_msl_data), aurora_msl_data.shape)
    era5_min_pos = np.unravel_index(np.argmin(era5_msl_data), era5_msl_data.shape)

    aurora_center_lat = lat[aurora_min_pos[0]]
    aurora_center_lon = lon[aurora_min_pos[1]]
    era5_center_lat = lat[era5_min_pos[0]]
    era5_center_lon = lon[era5_min_pos[1]]

    center_diff_km = calculate_distance(
        aurora_center_lat, aurora_center_lon,
        era5_center_lat, era5_center_lon
    )

    return {
        'msl': {
            'aurora': aurora_msl_data,
            'era5': era5_msl_data,
            'difference': aurora_msl_data - era5_msl_data,
            'aurora_min': aurora_msl_min,
            'era5_min': era5_msl_min,
            'aurora_center': (aurora_center_lat, aurora_center_lon),
            'era5_center': (era5_center_lat, era5_center_lon),
            'center_diff_km': center_diff_km
        },
        'wind': {
            'aurora': aurora_wind_data,
            'era5': era5_wind_data,
            'difference': aurora_wind_data - era5_wind_data,
            'aurora_max': aurora_wind_max,
            'era5_max': era5_wind_max
        },
        'z700': {
            'aurora': aurora_z700_data,
            'era5': era5_z700_data,
            'difference': aurora_z700_data - era5_z700_data
        },
        'lat': lat,
        'lon': lon,
        'landfall_position': (landfall_lat, landfall_lon),
        'time': time_val
    }


def extract_error_at_lead_time(errors_data, target_hours):
    """
    Extract track error at specific lead time.

    Parameters
    ----------
    errors_data : dict
        Dictionary with 'errors' and 'lead_times' arrays
    target_hours : int
        Target lead time in hours (e.g., 24, 48, 72)

    Returns
    -------
    float or None
        Error at target lead time, or None if not available
    """
    lead_times = np.array(errors_data['lead_times'])
    errors = np.array(errors_data['errors'])

    # Find closest lead time
    if len(lead_times) == 0:
        return None

    idx = np.argmin(np.abs(lead_times - target_hours))

    # Only return if within 3 hours of target (i.e., exactly matches 6-hour steps)
    if np.abs(lead_times[idx] - target_hours) <= 3:
        return errors[idx]
    else:
        return None


def summarize_stage1_results(results, landfall_comparisons=None):
    """
    Create comprehensive summary table for Stage 1 lead time assessment.

    Parameters
    ----------
    results : dict
        Results dictionary from Stage 1 analysis
        Keys: lead time in days (1, 3, 5, 7)
        Values: result dicts with 'errors_data', 'summary', etc.
    landfall_comparisons : dict, optional
        Landfall field comparison results
        Keys: lead time labels (e.g., '1-day lead')
        Values: comparison dicts from compare_fields_at_landfall()

    Returns
    -------
    dict
        Summary metrics organized by lead time with keys:
        - 'track_error_24h': Track error at 24h lead (km)
        - 'track_error_48h': Track error at 48h lead (km)
        - 'track_error_72h': Track error at 72h lead (km)
        - 'mean_track_error': Mean error across all lead times (km)
        - 'msl_min_error': MSL minimum error at landfall (hPa)
        - 'wind_max_error': Wind maximum error at landfall (m/s)
        - 'center_position_error': TC center position error at landfall (km)
    """
    summary = {}

    for lead_days in sorted(results.keys()):
        result = results[lead_days]
        errors_data = result['errors_data']
        perf_summary = result['summary']

        metrics = {}

        # Track errors at specific lead times
        metrics['track_error_24h'] = extract_error_at_lead_time(errors_data, 24)
        metrics['track_error_48h'] = extract_error_at_lead_time(errors_data, 48)
        metrics['track_error_72h'] = extract_error_at_lead_time(errors_data, 72)
        metrics['mean_track_error'] = perf_summary.get('mean_error') if perf_summary else None

        # Landfall field comparison metrics (if available)
        if landfall_comparisons:
            label = f'{lead_days}-day lead'
            if label in landfall_comparisons:
                comp = landfall_comparisons[label]

                # MSL minimum error (convert Pa to hPa)
                if 'msl' in comp:
                    aurora_msl = comp['msl']['aurora_min']
                    era5_msl = comp['msl']['era5_min']
                    metrics['msl_min_error'] = (aurora_msl - era5_msl) / 100.0  # Pa to hPa

                    # Center position error
                    metrics['center_position_error'] = comp['msl'].get('center_diff_km')

                # Wind maximum error
                if 'wind' in comp:
                    aurora_wind = comp['wind']['aurora_max']
                    era5_wind = comp['wind']['era5_max']
                    metrics['wind_max_error'] = aurora_wind - era5_wind
            else:
                metrics['msl_min_error'] = None
                metrics['wind_max_error'] = None
                metrics['center_position_error'] = None
        else:
            metrics['msl_min_error'] = None
            metrics['wind_max_error'] = None
            metrics['center_position_error'] = None

        summary[lead_days] = metrics

    return summary


def export_results_to_csv(tc_name, stage, results, landfall_comparisons=None,
                          csv_path=None, stage_type='stage1'):
    """
    Export TC prediction results to CSV for paper table generation.

    Parameters
    ----------
    tc_name : str
        Name of the tropical cyclone (e.g., 'Sandy 2012', 'Ian 2022')
    stage : int
        Stage number (1 for lead time assessment, 2 for initialization time)
    results : dict
        Results dictionary from stage analysis
        For Stage 1: Keys are lead days (1, 3, 5, 7)
        For Stage 2: Keys are init hours ('00', '06', '12', '18')
    landfall_comparisons : dict, optional
        Landfall field comparison results
    csv_path : Path or str, optional
        Path to CSV file. If None, uses 'TC_result_metrics.csv' in current directory
    stage_type : str, optional
        'stage1' for lead time assessment, 'stage2' for initialization time

    Returns
    -------
    None
        Writes or appends to CSV file

    CSV Format
    ----------
    Columns: TC_Name, Stage, Lead_Day_or_Init_Time, Track_Error_24h_km,
             Track_Error_48h_km, Track_Error_72h_km, MSL_Error_hPa,
             Wind_Error_ms, Position_Error_Landfall_km

    Example
    -------
    >>> # Stage 1
    >>> export_results_to_csv('Sandy 2012', 1, results, landfall_comparisons,
    ...                       stage_type='stage1')
    >>> # Stage 2
    >>> export_results_to_csv('Ian 2022', 2, results, landfall_comparisons,
    ...                       stage_type='stage2')
    """
    import csv
    from pathlib import Path

    if csv_path is None:
        csv_path = Path.cwd() / 'TC_result_metrics.csv'
    else:
        csv_path = Path(csv_path)

    # Check if file exists to determine if we need to write header
    file_exists = csv_path.exists()

    # Prepare data rows
    rows = []

    if stage_type == 'stage1':
        # Stage 1: Results organized by lead days
        for lead_days in sorted(results.keys()):
            result = results[lead_days]
            errors_data = result['errors_data']
            perf_summary = result['summary']

            # Extract track errors
            track_24h = extract_error_at_lead_time(errors_data, 24)
            track_48h = extract_error_at_lead_time(errors_data, 48)
            track_72h = extract_error_at_lead_time(errors_data, 72)

            # Extract landfall field comparison metrics
            msl_err = None
            wind_err = None
            pos_err = None

            if landfall_comparisons:
                label = f'{lead_days}-day lead'
                if label in landfall_comparisons:
                    comp = landfall_comparisons[label]
                    if 'msl' in comp:
                        msl_err = (comp['msl']['aurora_min'] - comp['msl']['era5_min']) / 100.0
                        pos_err = comp['msl'].get('center_diff_km')
                    if 'wind' in comp:
                        wind_err = comp['wind']['aurora_max'] - comp['wind']['era5_max']

            row = {
                'TC_Name': tc_name,
                'Stage': stage,
                'Lead_Day_or_Init_Time': f'{lead_days}-day',
                'Track_Error_24h_km': f'{track_24h:.1f}' if track_24h is not None else 'N/A',
                'Track_Error_48h_km': f'{track_48h:.1f}' if track_48h is not None else 'N/A',
                'Track_Error_72h_km': f'{track_72h:.1f}' if track_72h is not None else 'N/A',
                'MSL_Error_hPa': f'{msl_err:.1f}' if msl_err is not None else 'N/A',
                'Wind_Error_ms': f'{wind_err:.1f}' if wind_err is not None else 'N/A',
                'Position_Error_Landfall_km': f'{pos_err:.1f}' if pos_err is not None else 'N/A'
            }
            rows.append(row)

    elif stage_type == 'stage2':
        # Stage 2: Results organized by initialization times
        for hour in sorted(results.keys()):
            result = results[hour]
            perf_summary = result['summary']

            # Extract track errors from summary
            track_24h = perf_summary.get('error_24h')
            track_48h = perf_summary.get('error_48h')
            track_72h = perf_summary.get('error_72h')

            # Extract landfall field comparison metrics
            msl_err = None
            wind_err = None
            pos_err = None

            field_comp = result.get('landfall_field_comparison')
            if field_comp:
                if 'msl' in field_comp:
                    msl_err = (field_comp['msl']['aurora_min'] - field_comp['msl']['era5_min']) / 100.0
                    pos_err = field_comp['msl'].get('center_diff_km')
                if 'wind' in field_comp:
                    wind_err = field_comp['wind']['aurora_max'] - field_comp['wind']['era5_max']

            row = {
                'TC_Name': tc_name,
                'Stage': stage,
                'Lead_Day_or_Init_Time': f'{hour}:00 UTC',
                'Track_Error_24h_km': f'{track_24h:.1f}' if track_24h is not None else 'N/A',
                'Track_Error_48h_km': f'{track_48h:.1f}' if track_48h is not None else 'N/A',
                'Track_Error_72h_km': f'{track_72h:.1f}' if track_72h is not None else 'N/A',
                'MSL_Error_hPa': f'{msl_err:.1f}' if msl_err is not None else 'N/A',
                'Wind_Error_ms': f'{wind_err:.1f}' if wind_err is not None else 'N/A',
                'Position_Error_Landfall_km': f'{pos_err:.1f}' if pos_err is not None else 'N/A'
            }
            rows.append(row)

    # Write to CSV
    fieldnames = ['TC_Name', 'Stage', 'Lead_Day_or_Init_Time', 'Track_Error_24h_km',
                  'Track_Error_48h_km', 'Track_Error_72h_km', 'MSL_Error_hPa',
                  'Wind_Error_ms', 'Position_Error_Landfall_km']

    with open(csv_path, 'a' if file_exists else 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header if new file
        if not file_exists:
            writer.writeheader()

        # Write data rows
        writer.writerows(rows)

    print(f"✓ Exported {len(rows)} rows to {csv_path}")
    if file_exists:
        print(f"  (appended to existing file)")
    else:
        print(f"  (created new file)")

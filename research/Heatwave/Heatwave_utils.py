"""
Heatwave specific utilities.

This module contains functions specific to heatwave event analysis:
- Regional subset extraction
- Spatial statistics (mean, min, max over region)
- Temporal detection (onset, peak, recovery)
- Heatwave-specific metrics (RMSE, spatial extent, IoU, duration)
- Heatwave-specific visualizations

Key differences from Freeze_utils.py:
- INVERTED thresholds: > instead of < for detection
- Peak detection uses argmax (hottest) instead of argmin (coldest)
- Color schemes: Reds/oranges instead of blues
- Thresholds: 30°C, 35°C, 40°C instead of 0°C, -5°C, -10°C
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import BoundaryNorm
import json


def extract_regional_subset(ds, variable, region, level=None):
    """
    Extract regional subset from dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the variable
    variable : str
        Variable name (e.g., 't2m', 'msl', 't', 'z')
    region : dict
        Region definition with keys: lat_min, lat_max, lon_min, lon_max
    level : int or None
        Pressure level for atmospheric variables (e.g., 850, 500)

    Returns
    -------
    xarray.DataArray
        Regional subset of the variable
    """
    # Handle longitude wrapping (negative to 0-360)
    lon_min = region['lon_min'] if region['lon_min'] >= 0 else region['lon_min'] + 360
    lon_max = region['lon_max'] if region['lon_max'] >= 0 else region['lon_max'] + 360

    # Select variable with or without pressure level
    if level is not None:
        var = ds[variable].sel(pressure_level=level)
    else:
        var = ds[variable]

    # Check if region crosses prime meridian
    if lon_min > lon_max:
        # Extract two regions and concatenate
        import xarray as xr
        subset1 = var.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(lon_min, 360)
        )
        subset2 = var.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(0, lon_max)
        )
        subset = xr.concat([subset1, subset2], dim='longitude')
    else:
        # Simple case
        subset = var.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(lon_min, lon_max)
        )

    return subset


def compute_regional_statistics(field_timeseries, region=None):
    """
    Compute regional statistics over time.

    Parameters
    ----------
    field_timeseries : xarray.DataArray or list of numpy.ndarray
        Time series of spatial fields
    region : dict or None
        If provided, will extract subset first

    Returns
    -------
    dict
        Dictionary with keys:
        - 'mean': regional mean at each timestep
        - 'min': regional minimum at each timestep
        - 'max': regional maximum at each timestep
        - 'std': regional std dev at each timestep
    """
    import xarray as xr

    if isinstance(field_timeseries, list):
        # List of numpy arrays
        means = [float(np.mean(f)) for f in field_timeseries]
        mins = [float(np.min(f)) for f in field_timeseries]
        maxs = [float(np.max(f)) for f in field_timeseries]
        stds = [float(np.std(f)) for f in field_timeseries]
    else:
        # xarray DataArray
        means = field_timeseries.mean(dim=['latitude', 'longitude']).values
        mins = field_timeseries.min(dim=['latitude', 'longitude']).values
        maxs = field_timeseries.max(dim=['latitude', 'longitude']).values
        stds = field_timeseries.std(dim=['latitude', 'longitude']).values

    return {
        'mean': np.array(means),
        'min': np.array(mins),
        'max': np.array(maxs),
        'std': np.array(stds)
    }


def detect_onset_timing_heat(t2m_mean, times, threshold=30.0):
    """
    Detect onset timing (first time regional mean EXCEEDS threshold).

    INVERTED from freeze: uses > instead of <

    Parameters
    ----------
    t2m_mean : array-like
        Regional mean temperature time series (°C)
    times : array-like
        Time coordinates (datetime64 or datetime objects)
    threshold : float
        Temperature threshold in °C (default: 30.0)

    Returns
    -------
    datetime or None
        Onset time, or None if threshold never exceeded
    """
    above_threshold = np.where(np.array(t2m_mean) > threshold)[0]

    if len(above_threshold) > 0:
        onset_idx = above_threshold[0]
        return times[onset_idx]
    else:
        return None


def detect_peak_timing_heat(t2m_mean, times):
    """
    Detect peak heat timing (MAXIMUM regional mean temperature).

    INVERTED from freeze: uses argmax instead of argmin

    Parameters
    ----------
    t2m_mean : array-like
        Regional mean temperature time series (°C)
    times : array-like
        Time coordinates

    Returns
    -------
    tuple
        (peak_time, peak_temperature)
    """
    peak_idx = np.argmax(t2m_mean)
    return times[peak_idx], float(t2m_mean[peak_idx])


def detect_recovery_timing_heat(t2m_mean, times, threshold=30.0):
    """
    Detect recovery timing (last time regional mean ABOVE threshold).

    INVERTED from freeze: uses > instead of <

    Parameters
    ----------
    t2m_mean : array-like
        Regional mean temperature time series (°C)
    times : array-like
        Time coordinates
    threshold : float
        Temperature threshold in °C (default: 30.0)

    Returns
    -------
    datetime or None
        Recovery time (first timestep after last above-threshold), or None
    """
    above_threshold = np.where(np.array(t2m_mean) > threshold)[0]

    if len(above_threshold) > 0:
        last_idx = above_threshold[-1]
        # Recovery is the next timestep after last above-threshold
        if last_idx + 1 < len(times):
            return times[last_idx + 1]
        else:
            return None  # Recovery not captured in data
    else:
        return None


def compute_spatial_extent_heat(field, thresholds):
    """
    Compute spatial extent (fraction of region) ABOVE temperature thresholds.

    INVERTED from freeze: uses > instead of <

    Parameters
    ----------
    field : numpy.ndarray
        2D temperature field (°C)
    thresholds : list of float
        Temperature thresholds (e.g., [30, 35, 40])

    Returns
    -------
    dict
        Mapping from threshold to fraction of region above that threshold
    """
    total_points = field.size
    extents = {}

    for thresh in thresholds:
        fraction = float(np.sum(field > thresh) / total_points)
        extents[thresh] = fraction

    return extents


def compute_iou_heat(forecast_field, truth_field, threshold):
    """
    Compute Intersection over Union for areas ABOVE threshold.

    INVERTED from freeze: uses > instead of <

    Parameters
    ----------
    forecast_field : numpy.ndarray
        Forecast temperature field (°C)
    truth_field : numpy.ndarray
        Truth temperature field (°C)
    threshold : float
        Temperature threshold (e.g., 30°C)

    Returns
    -------
    float
        IoU score (0 to 1)
    """
    forecast_mask = forecast_field > threshold
    truth_mask = truth_field > threshold

    intersection = np.sum(forecast_mask & truth_mask)
    union = np.sum(forecast_mask | truth_mask)

    if union == 0:
        return 1.0 if intersection == 0 else 0.0

    return float(intersection / union)


def compute_heatwave_rmse(forecast_fields, truth_fields, phase_indices):
    """
    Compute RMSE at onset, peak, and recovery phases.

    Same as freeze (RMSE calculation is symmetric)

    Parameters
    ----------
    forecast_fields : list of numpy.ndarray
        Forecast temperature fields (°C) at each timestep
    truth_fields : xarray.DataArray or list
        Truth temperature fields (°C)
    phase_indices : dict
        Mapping from phase name to timestep index
        e.g., {'onset': 10, 'peak': 15, 'recovery': 20}

    Returns
    -------
    dict
        RMSE at each phase
    """
    rmse_results = {}

    for phase, idx in phase_indices.items():
        if idx < len(forecast_fields):
            forecast = forecast_fields[idx]

            # Handle xarray or list
            if hasattr(truth_fields, 'isel'):
                truth = truth_fields.isel(valid_time=idx).values
            else:
                truth = truth_fields[idx]

            # Compute RMSE
            rmse = np.sqrt(np.mean((forecast - truth)**2))
            rmse_results[phase] = float(rmse)
        else:
            rmse_results[phase] = None

    return rmse_results


def compute_pattern_correlation(forecast_field, truth_field):
    """
    Compute spatial pattern correlation.

    Same as freeze (correlation is symmetric)

    Parameters
    ----------
    forecast_field : numpy.ndarray
        Forecast field
    truth_field : numpy.ndarray
        Truth field

    Returns
    -------
    float
        Correlation coefficient
    """
    # Flatten fields
    f_flat = forecast_field.flatten()
    t_flat = truth_field.flatten()

    # Remove NaNs
    mask = ~(np.isnan(f_flat) | np.isnan(t_flat))
    f_clean = f_flat[mask]
    t_clean = t_flat[mask]

    if len(f_clean) < 2:
        return np.nan

    # Compute correlation
    corr = np.corrcoef(f_clean, t_clean)[0, 1]
    return float(corr)


def compute_heatwave_metrics(forecast_fields, truth_ds, forecast_times,
                              region, onset_date, peak_date, recovery_date,
                              thresholds=[30, 35, 40]):
    """
    Compute comprehensive heatwave event metrics.

    INVERTED from freeze: uses > thresholds, argmax for peak

    Parameters
    ----------
    forecast_fields : list of numpy.ndarray
        Forecast T2m fields (°C) at each timestep - GLOBAL fields (720x1440)
    truth_ds : xarray.Dataset
        ERA5 truth dataset
    forecast_times : list
        Forecast timesteps (datetime objects)
    region : dict
        Regional domain definition
    onset_date : str
        Expected onset date (YYYY-MM-DD)
    peak_date : str
        Expected peak date (YYYY-MM-DD)
    recovery_date : str
        Expected recovery date (YYYY-MM-DD)
    thresholds : list
        Temperature thresholds for spatial extent (default: [30, 35, 40])

    Returns
    -------
    dict
        Comprehensive metrics dictionary
    """
    # Extract regional subset from GLOBAL forecast fields
    import xarray as xr

    # Create DataArray from forecast fields for easy subsetting
    # Aurora 0.25° grid: 720 lats (90 to -89.75), 1440 lons (0 to 359.75)
    global_lats = np.linspace(90, -90, 720, endpoint=False)
    global_lons = np.linspace(0, 360, 1440, endpoint=False)

    # Convert forecast fields to regional subset
    forecast_fields_regional = []
    for forecast in forecast_fields:
        # Create temporary DataArray
        forecast_da = xr.DataArray(
            forecast,
            dims=['latitude', 'longitude'],
            coords={'latitude': global_lats, 'longitude': global_lons}
        )

        # Extract regional subset
        lon_min = region['lon_min'] if region['lon_min'] >= 0 else region['lon_min'] + 360
        lon_max = region['lon_max'] if region['lon_max'] >= 0 else region['lon_max'] + 360

        if lon_min > lon_max:
            # Crosses prime meridian
            subset1 = forecast_da.sel(
                latitude=slice(region['lat_max'], region['lat_min']),
                longitude=slice(lon_min, 360)
            )
            subset2 = forecast_da.sel(
                latitude=slice(region['lat_max'], region['lat_min']),
                longitude=slice(0, lon_max)
            )
            subset = xr.concat([subset1, subset2], dim='longitude')
        else:
            subset = forecast_da.sel(
                latitude=slice(region['lat_max'], region['lat_min']),
                longitude=slice(lon_min, lon_max)
            )

        forecast_fields_regional.append(subset.values)

    # Extract truth subset
    truth_t2m = extract_regional_subset(truth_ds, 't2m', region) - 273.15  # K to °C

    # Compute forecast statistics (using regional subset now)
    forecast_stats = compute_regional_statistics(forecast_fields_regional)
    truth_stats = compute_regional_statistics(truth_t2m)

    # Detect timing in forecast (INVERTED LOGIC)
    forecast_onset = detect_onset_timing_heat(forecast_stats['mean'], forecast_times, threshold=30.0)
    forecast_peak_time, forecast_peak_temp = detect_peak_timing_heat(forecast_stats['mean'], forecast_times)
    forecast_recovery = detect_recovery_timing_heat(forecast_stats['mean'], forecast_times, threshold=30.0)

    # Detect timing in truth (INVERTED LOGIC)
    truth_times = truth_t2m.valid_time.values
    truth_onset = detect_onset_timing_heat(truth_stats['mean'], truth_times, threshold=30.0)
    truth_peak_time, truth_peak_temp = detect_peak_timing_heat(truth_stats['mean'], truth_times)
    truth_recovery = detect_recovery_timing_heat(truth_stats['mean'], truth_times, threshold=30.0)

    # Compute timing errors (in hours)
    def time_diff_hours(t1, t2):
        if t1 is None or t2 is None:
            return None
        dt1 = pd.Timestamp(t1)
        dt2 = pd.Timestamp(t2)
        return (dt1 - dt2).total_seconds() / 3600

    onset_error = time_diff_hours(forecast_onset, truth_onset)
    peak_error = time_diff_hours(forecast_peak_time, truth_peak_time)
    recovery_error = time_diff_hours(forecast_recovery, truth_recovery)

    # Find phase indices in forecast
    phase_indices = {}
    for phase_name, target_date in [('onset', onset_date), ('peak', peak_date), ('recovery', recovery_date)]:
        target_dt = pd.Timestamp(target_date)
        # Find closest timestep
        diffs = [abs((pd.Timestamp(t) - target_dt).total_seconds()) for t in forecast_times]
        phase_indices[phase_name] = int(np.argmin(diffs))

    # Compute RMSE at each phase (using regional subset)
    rmse_results = compute_heatwave_rmse(forecast_fields_regional, truth_t2m, phase_indices)

    # Compute spatial extent and IoU at peak (using regional subset, INVERTED LOGIC)
    peak_idx = phase_indices['peak']
    if peak_idx < len(forecast_fields_regional):
        forecast_extents = compute_spatial_extent_heat(forecast_fields_regional[peak_idx], thresholds)
        truth_peak = truth_t2m.isel(valid_time=peak_idx).values
        truth_extents = compute_spatial_extent_heat(truth_peak, thresholds)

        iou_scores = {}
        for thresh in thresholds:
            iou_scores[thresh] = compute_iou_heat(forecast_fields_regional[peak_idx], truth_peak, thresh)

        pattern_corr = compute_pattern_correlation(forecast_fields_regional[peak_idx], truth_peak)
    else:
        forecast_extents = None
        truth_extents = None
        iou_scores = None
        pattern_corr = None

    # Duration (number of timesteps ABOVE 30°C, INVERTED)
    forecast_duration = np.sum(forecast_stats['mean'] > 30) * 6  # hours
    truth_duration = np.sum(truth_stats['mean'] > 30) * 6  # hours
    duration_error = forecast_duration - truth_duration

    # Intensity bias at peak
    intensity_bias = forecast_peak_temp - truth_peak_temp

    return {
        'timing': {
            'onset_error_hours': onset_error,
            'peak_error_hours': peak_error,
            'recovery_error_hours': recovery_error,
            'forecast_onset': str(forecast_onset) if forecast_onset else None,
            'truth_onset': str(truth_onset) if truth_onset else None,
            'forecast_peak': str(forecast_peak_time),
            'truth_peak': str(truth_peak_time),
        },
        'rmse': rmse_results,
        'spatial_extent': {
            'forecast': forecast_extents,
            'truth': truth_extents,
            'iou_scores': iou_scores
        },
        'duration': {
            'forecast_hours': float(forecast_duration),
            'truth_hours': float(truth_duration),
            'error_hours': float(duration_error)
        },
        'intensity': {
            'forecast_peak_temp': float(forecast_peak_temp),
            'truth_peak_temp': float(truth_peak_temp),
            'bias': float(intensity_bias)
        },
        'pattern_correlation_at_peak': float(pattern_corr) if pattern_corr else None
    }


def save_heatwave_results(results, output_path):
    """
    Save heatwave stage 1 results to JSON file.

    Parameters
    ----------
    results : dict
        Results dictionary from stage 1 analysis
    output_path : Path or str
        Output file path (.json)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSON-serializable format
    json_results = {}
    for lead_days, result in results.items():
        json_results[str(lead_days)] = {
            'config': result['config'],
            'metrics': result['metrics']
        }

    with open(output_path, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"✓ Results saved to: {output_path}")


def plot_heatwave_temporal_evolution(results, output_dir, event_name="Heatwave Event"):
    """
    Plot temperature evolution for all lead times.

    MODIFIED from freeze: Red/orange colors for heat

    Parameters
    ----------
    results : dict
        Results from stage 1 (keyed by lead_days)
    output_dir : Path
        Output directory for figures
    event_name : str
        Event name for title
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # HOT COLORS instead of cool
    colors = {1: 'darkred', 7: 'orangered', 14: 'orange', 21: 'gold'}

    # Plot 1: Regional mean temperature
    ax = axes[0]
    for lead_days in sorted(results.keys()):
        result = results[lead_days]
        times = result['forecast_times']
        stats = result['forecast_stats']

        color = colors.get(lead_days, 'black')
        ax.plot(times, stats['mean'], color=color, linewidth=2,
                label=f'{lead_days}-day lead', alpha=0.8)

    # Plot truth
    if 'truth_stats' in results[list(results.keys())[0]]:
        truth_stats = results[list(results.keys())[0]]['truth_stats']
        truth_times = results[list(results.keys())[0]]['truth_times']
        ax.plot(truth_times, truth_stats['mean'], 'k--', linewidth=2.5, label='ERA5 Truth')

    # Heat threshold line (instead of freeze line)
    ax.axhline(30, color='red', linestyle='--', linewidth=1, alpha=0.5, label='30°C threshold')
    ax.set_ylabel('Regional Mean T2m (°C)', fontsize=12)
    ax.set_title(f'{event_name}: Temperature Evolution by Lead Time', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    # Plot 2: Absolute error over time
    ax = axes[1]
    for lead_days in sorted(results.keys()):
        result = results[lead_days]
        if 'error_evolution' in result:
            times = result['forecast_times']
            errors = result['error_evolution']
            color = colors.get(lead_days, 'black')
            ax.plot(times, errors, color=color, linewidth=2,
                    label=f'{lead_days}-day lead', alpha=0.8)

    ax.set_ylabel('RMSE (°C)', fontsize=12)
    ax.set_xlabel('Valid Time', fontsize=12)
    ax.set_title('Forecast Error Evolution', fontsize=12, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    plt.tight_layout()
    output_file = output_dir / "heatwave_temporal_evolution.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file.name}")
    plt.close()


def plot_spatial_comparison_heat(forecast_field, truth_field, region, valid_time,
                                  variable_name, units, lead_days, output_path,
                                  vmin=None, vmax=None, cmap='YlOrRd'):
    """
    Plot spatial comparison: Forecast, ERA5, and Difference side-by-side.

    MODIFIED from freeze: Hot colormap (YlOrRd instead of RdBu_r for temperature)

    Parameters
    ----------
    forecast_field : numpy.ndarray
        Forecast field (2D)
    truth_field : numpy.ndarray
        ERA5 truth field (2D)
    region : dict
        Region definition with lat/lon bounds
    valid_time : datetime or str
        Valid time for this field
    variable_name : str
        Variable name (e.g., '2m Temperature', '850 hPa Temperature')
    units : str
        Units (e.g., '°C', 'hPa', 'm')
    lead_days : int
        Lead time in days
    output_path : Path or str
        Output file path
    vmin, vmax : float or None
        Color scale limits (if None, auto-determined)
    cmap : str
        Colormap name (default: 'YlOrRd' for heat)
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from matplotlib.colors import TwoSlopeNorm

    fig = plt.figure(figsize=(18, 5))

    # Create lon/lat grids (assume regular spacing)
    lon_min = region['lon_min'] if region['lon_min'] >= 0 else region['lon_min'] + 360
    lon_max = region['lon_max'] if region['lon_max'] >= 0 else region['lon_max'] + 360

    nlat, nlon = forecast_field.shape
    lats = np.linspace(region['lat_max'], region['lat_min'], nlat)
    lons = np.linspace(lon_min, lon_max, nlon)

    # Adjust lons back to -180 to 180 for plotting
    lons_plot = np.where(lons > 180, lons - 360, lons)

    # Compute difference
    difference = forecast_field - truth_field

    # Determine color scales
    if vmin is None or vmax is None:
        combined = np.concatenate([forecast_field.flatten(), truth_field.flatten()])
        vmin = np.nanpercentile(combined, 2)
        vmax = np.nanpercentile(combined, 98)

    # Difference scale (symmetric around 0)
    diff_max = np.nanpercentile(np.abs(difference), 95)
    diff_max = max(diff_max, 0.5)  # Minimum range

    # Panel 1: Aurora Forecast
    ax1 = plt.subplot(1, 3, 1, projection=ccrs.PlateCarree())
    ax1.coastlines(linewidth=0.5)
    ax1.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')
    ax1.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax1.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    im1 = ax1.pcolormesh(lons_plot, lats, forecast_field,
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree(), zorder=2)
    if variable_name == '2m Temperature':
        # Heat contours (red tones)
        ax1.contour(lons_plot, lats, forecast_field, levels=[30, 35, 40],
                   colors=['black', 'red', 'darkred'], linewidths=[2.5, 2.0, 1.5],
                   transform=ccrs.PlateCarree())
    ax1.set_title(f'Aurora Forecast ({lead_days}-day lead)', fontsize=12, fontweight='bold')
    plt.colorbar(im1, ax=ax1, orientation='horizontal', pad=0.05, label=f'{variable_name} ({units})')

    # Panel 2: ERA5 Truth
    ax2 = plt.subplot(1, 3, 2, projection=ccrs.PlateCarree())
    ax2.coastlines(linewidth=0.5)
    ax2.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')
    ax2.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax2.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    im2 = ax2.pcolormesh(lons_plot, lats, truth_field,
                         cmap=cmap, vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree(), zorder=2)
    if variable_name == '2m Temperature':
        ax2.contour(lons_plot, lats, truth_field, levels=[30, 35, 40],
                   colors=['black', 'red', 'darkred'], linewidths=[2.5, 2.0, 1.5],
                   transform=ccrs.PlateCarree())
    ax2.set_title('ERA5 Truth', fontsize=12, fontweight='bold')
    plt.colorbar(im2, ax=ax2, orientation='horizontal', pad=0.05, label=f'{variable_name} ({units})')

    # Panel 3: Difference (Aurora - ERA5)
    ax3 = plt.subplot(1, 3, 3, projection=ccrs.PlateCarree())
    ax3.coastlines(linewidth=0.5)
    ax3.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')
    ax3.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)
    ax3.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    # Use diverging colormap centered at 0
    norm = TwoSlopeNorm(vmin=-diff_max, vcenter=0, vmax=diff_max)
    im3 = ax3.pcolormesh(lons_plot, lats, difference,
                         cmap='RdBu_r', norm=norm,
                         transform=ccrs.PlateCarree(), zorder=2)
    ax3.set_title('Difference (Aurora - ERA5)', fontsize=12, fontweight='bold')
    plt.colorbar(im3, ax=ax3, orientation='horizontal', pad=0.05,
                label=f'Difference ({units})', extend='both')

    # Super title
    time_str = pd.Timestamp(valid_time).strftime('%Y-%m-%d %H:%M UTC')
    plt.suptitle(f'{variable_name} - Valid: {time_str}',
                fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_heatwave_extent_comparison(forecast_field, truth_field, region, valid_time,
                                     lead_days, output_path, thresholds=[30, 35, 40]):
    """
    Plot heatwave extent with multiple temperature contours.

    MODIFIED from freeze: Red color scheme, heat thresholds

    Parameters
    ----------
    forecast_field : numpy.ndarray
        Forecast T2m (°C)
    truth_field : numpy.ndarray
        ERA5 T2m (°C)
    region : dict
        Region bounds
    valid_time : datetime
        Valid time
    lead_days : int
        Lead time
    output_path : Path
        Output file
    thresholds : list
        Temperature thresholds to contour (default: [30, 35, 40])
    """
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    fig = plt.figure(figsize=(18, 5))

    # Create coordinate grids
    lon_min = region['lon_min'] if region['lon_min'] >= 0 else region['lon_min'] + 360
    lon_max = region['lon_max'] if region['lon_max'] >= 0 else region['lon_max'] + 360

    nlat, nlon = forecast_field.shape
    lats = np.linspace(region['lat_max'], region['lat_min'], nlat)
    lons = np.linspace(lon_min, lon_max, nlon)
    lons_plot = np.where(lons > 180, lons - 360, lons)

    difference = forecast_field - truth_field

    # Temperature colormap (HOT instead of COLD)
    vmin, vmax = 15, 45

    # Panel 1: Aurora Forecast with heat contours
    ax1 = plt.subplot(1, 3, 1, projection=ccrs.PlateCarree())
    ax1.coastlines(linewidth=0.8, edgecolor='black')
    ax1.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':', edgecolor='black')
    ax1.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.2)
    ax1.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    im1 = ax1.pcolormesh(lons_plot, lats, forecast_field,
                         cmap='YlOrRd', vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree(), zorder=2)

    # Heat contours (RED tones instead of BLUE)
    colors = {30: 'black', 35: 'red', 40: 'darkred'}
    linewidths = {30: 2.5, 35: 2.0, 40: 1.5}
    for thresh in thresholds:
        ax1.contour(lons_plot, lats, forecast_field, levels=[thresh],
                   colors=colors[thresh], linewidths=linewidths[thresh],
                   transform=ccrs.PlateCarree())

    ax1.set_title(f'Aurora Forecast ({lead_days}-day lead)', fontsize=12, fontweight='bold')
    cbar1 = plt.colorbar(im1, ax=ax1, orientation='horizontal', pad=0.05, extend='both')
    cbar1.set_label('2m Temperature (°C)', fontsize=10)

    # Panel 2: ERA5 Truth with heat contours
    ax2 = plt.subplot(1, 3, 2, projection=ccrs.PlateCarree())
    ax2.coastlines(linewidth=0.8, edgecolor='black')
    ax2.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':', edgecolor='black')
    ax2.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.2)
    ax2.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    im2 = ax2.pcolormesh(lons_plot, lats, truth_field,
                         cmap='YlOrRd', vmin=vmin, vmax=vmax,
                         transform=ccrs.PlateCarree(), zorder=2)

    for thresh in thresholds:
        ax2.contour(lons_plot, lats, truth_field, levels=[thresh],
                   colors=colors[thresh], linewidths=linewidths[thresh],
                   transform=ccrs.PlateCarree())

    ax2.set_title('ERA5 Truth', fontsize=12, fontweight='bold')
    cbar2 = plt.colorbar(im2, ax=ax2, orientation='horizontal', pad=0.05, extend='both')
    cbar2.set_label('2m Temperature (°C)', fontsize=10)

    # Panel 3: Difference with heat extent overlap
    ax3 = plt.subplot(1, 3, 3, projection=ccrs.PlateCarree())
    ax3.coastlines(linewidth=0.8, edgecolor='black')
    ax3.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':', edgecolor='black')
    ax3.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.2)
    ax3.set_extent([region['lon_min'], region['lon_max'],
                    region['lat_min'], region['lat_max']], crs=ccrs.PlateCarree())

    from matplotlib.colors import TwoSlopeNorm
    diff_max = 10  # ±10°C range
    norm = TwoSlopeNorm(vmin=-diff_max, vcenter=0, vmax=diff_max)
    im3 = ax3.pcolormesh(lons_plot, lats, difference,
                         cmap='RdBu_r', norm=norm,
                         transform=ccrs.PlateCarree(), zorder=2)

    # Show 30°C contours from both (dashed=Aurora, solid=ERA5)
    ax3.contour(lons_plot, lats, forecast_field, levels=[30],
               colors='red', linewidths=2, linestyles='--',
               transform=ccrs.PlateCarree(), label='Aurora 30°C')
    ax3.contour(lons_plot, lats, truth_field, levels=[30],
               colors='blue', linewidths=2, linestyles='-',
               transform=ccrs.PlateCarree(), label='ERA5 30°C')

    ax3.set_title('Difference & Heat Extent Comparison', fontsize=12, fontweight='bold')
    cbar3 = plt.colorbar(im3, ax=ax3, orientation='horizontal', pad=0.05)
    cbar3.set_label('Temperature Difference (°C)', fontsize=10)
    ax3.legend(loc='upper right', fontsize=8)

    # Super title
    time_str = pd.Timestamp(valid_time).strftime('%Y-%m-%d %H:%M UTC')
    plt.suptitle(f'Heatwave Extent Analysis - Valid: {time_str}',
                fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_lead_time_skill_heat(results, output_dir, event_name="Heatwave Event"):
    """
    Plot skill degradation with lead time.

    Same structure as freeze, adapted labels

    Parameters
    ----------
    results : dict
        Results from stage 1
    output_dir : Path
        Output directory
    event_name : str
        Event name
    """
    output_dir = Path(output_dir)

    lead_times = sorted(results.keys())

    # Extract metrics
    onset_errors = [abs(results[ld]['metrics']['timing']['onset_error_hours'])
                   if results[ld]['metrics']['timing']['onset_error_hours'] is not None else None
                   for ld in lead_times]
    peak_errors = [abs(results[ld]['metrics']['timing']['peak_error_hours'])
                  if results[ld]['metrics']['timing']['peak_error_hours'] is not None else None
                  for ld in lead_times]
    peak_rmse = [results[ld]['metrics']['rmse']['peak'] for ld in lead_times]
    duration_errors = [abs(results[ld]['metrics']['duration']['error_hours']) for ld in lead_times]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Onset timing error (RED for heat)
    ax = axes[0, 0]
    valid_onset = [(ld, err) for ld, err in zip(lead_times, onset_errors) if err is not None]
    if valid_onset:
        ld_valid, err_valid = zip(*valid_onset)
        ax.plot(ld_valid, err_valid, 'o-', linewidth=2, markersize=8, color='darkred')
    ax.set_xlabel('Lead Time (days)')
    ax.set_ylabel('Onset Timing Error (hours)')
    ax.set_title('Onset Detection Skill', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 2: Peak timing error
    ax = axes[0, 1]
    valid_peak = [(ld, err) for ld, err in zip(lead_times, peak_errors) if err is not None]
    if valid_peak:
        ld_valid, err_valid = zip(*valid_peak)
        ax.plot(ld_valid, err_valid, 'o-', linewidth=2, markersize=8, color='orangered')
    ax.set_xlabel('Lead Time (days)')
    ax.set_ylabel('Peak Timing Error (hours)')
    ax.set_title('Peak Detection Skill', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 3: Peak RMSE
    ax = axes[1, 0]
    valid_rmse = [(ld, r) for ld, r in zip(lead_times, peak_rmse) if r is not None]
    if valid_rmse:
        ld_valid, rmse_valid = zip(*valid_rmse)
        ax.plot(ld_valid, rmse_valid, 'o-', linewidth=2, markersize=8, color='orange')
    ax.set_xlabel('Lead Time (days)')
    ax.set_ylabel('RMSE at Peak (°C)')
    ax.set_title('Spatial Accuracy at Peak', fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Plot 4: Duration error
    ax = axes[1, 1]
    ax.plot(lead_times, duration_errors, 'o-', linewidth=2, markersize=8, color='gold')
    ax.set_xlabel('Lead Time (days)')
    ax.set_ylabel('Duration Error (hours)')
    ax.set_title('Event Duration Skill', fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.suptitle(f'{event_name}: Skill Degradation with Lead Time',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = output_dir / "heatwave_lead_time_skill.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file.name}")
    plt.close()

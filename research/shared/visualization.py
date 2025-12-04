"""
Visualization utilities for forecast verification plots.

This module contains functions for creating standardized publication-quality
figures following the project visualization standards.
"""

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D


# Visualization standards (consistent across all figures)
COLORS = {
    'forecast': '#4A90E2',      # Blue
    'forecast_alt': '#9B59B6',  # Purple
    'observation': '#E74C3C',    # Red/Orange
    'truth': '#E67E22',          # Orange
    'error_positive': '#E74C3C', # Red
    'error_negative': '#3498DB', # Blue
}

MAP_STYLE = {
    'land': cfeature.LAND.with_scale('50m'),
    'ocean': cfeature.OCEAN.with_scale('50m'),
    'coastline': cfeature.COASTLINE.with_scale('50m'),
    'borders': cfeature.BORDERS.with_scale('50m'),
    'land_color': '#F5F5F5',
    'ocean_color': '#E8F4F8',
}


def setup_map(ax, extent=None, projection=None):
    """
    Set up map with standard styling.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to configure (must have projection)
    extent : list or None, optional
        Map extent [lon_min, lon_max, lat_min, lat_max]
    projection : cartopy.crs projection or None
        If None, uses PlateCarree

    Returns
    -------
    ax : matplotlib.axes.Axes
        Configured axes
    """
    if extent is not None:
        ax.set_extent(extent, crs=ccrs.PlateCarree())

    # Add map features
    ax.add_feature(MAP_STYLE['land'], facecolor=MAP_STYLE['land_color'], zorder=0)
    ax.add_feature(MAP_STYLE['ocean'], facecolor=MAP_STYLE['ocean_color'], zorder=0)
    ax.add_feature(MAP_STYLE['coastline'], edgecolor='black', linewidth=0.5, zorder=1)
    ax.add_feature(MAP_STYLE['borders'], edgecolor='gray', linewidth=0.3, linestyle=':', zorder=1)

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    return ax


def plot_track_comparison(forecast_tracks, obs_track, title, save_path,
                          extent=None, track_labels=None, show_uncertainty=False,
                          obs_track_historical=None):
    """
    Plot track comparison between forecast(s) and observations.

    Parameters
    ----------
    forecast_tracks : dict or list
        If dict: {label: {'lat': [...], 'lon': [...], 'time': [...]}, ...}
        If list: [{'lat': [...], 'lon': [...], 'time': [...]}, ...]
    obs_track : dict
        Observed track: {'lat': [...], 'lon': [...], 'time': [...]}
    title : str
        Plot title
    save_path : str or Path
        Path to save figure
    extent : list or None, optional
        Map extent [lon_min, lon_max, lat_min, lat_max]
    track_labels : list or None, optional
        Labels for forecast tracks if forecast_tracks is a list
    show_uncertainty : bool, optional
        Show uncertainty ellipse (requires multiple forecast tracks)
    obs_track_historical : dict or None, optional
        Historical observed track segment to show as dashed line
        (e.g., track before forecast initialization period)
        Format: {'lat': [...], 'lon': [...], 'time': [...]}

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object

    Example
    -------
    >>> # Single forecast track
    >>> forecast = {'lat': [25, 26, 27], 'lon': [-80, -81, -82], 'time': [...]}
    >>> obs = {'lat': [25.1, 26.2, 27.1], 'lon': [-80.1, -81.2, -82.1], 'time': [...]}
    >>> fig = plot_track_comparison(forecast, obs, "Sandy Track", "sandy_track.png")
    >>>
    >>> # Multiple initialization times
    >>> forecasts = {
    ...     '06 UTC': {'lat': [...], 'lon': [...], 'time': [...]},
    ...     '12 UTC': {'lat': [...], 'lon': [...], 'time': [...]}
    ... }
    >>> fig = plot_track_comparison(forecasts, obs, "Sandy Track", "sandy_multi.png")
    """
    fig = plt.figure(figsize=(12, 8), dpi=300)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax = setup_map(ax, extent=extent)

    # Handle different input formats
    if isinstance(forecast_tracks, dict) and 'lat' in forecast_tracks:
        # Single track passed as dict with lat/lon
        forecast_tracks = {'Forecast': forecast_tracks}
    elif isinstance(forecast_tracks, list):
        # List of tracks
        if track_labels is None:
            track_labels = [f'Forecast {i+1}' for i in range(len(forecast_tracks))]
        forecast_tracks = dict(zip(track_labels, forecast_tracks))

    # Plot forecast tracks
    colors = [COLORS['forecast'], COLORS['forecast_alt'], '#2ECC71', '#F39C12', '#8E44AD']
    for i, (label, track) in enumerate(forecast_tracks.items()):
        color = colors[i % len(colors)]
        ax.plot(track['lon'], track['lat'],
               marker='o', markersize=4, linewidth=2,
               color=color, label=label,
               transform=ccrs.PlateCarree(), zorder=3)

        # Mark start point
        ax.plot(track['lon'][0], track['lat'][0],
               marker='s', markersize=8, color=color,
               markeredgecolor='black', markeredgewidth=1,
               transform=ccrs.PlateCarree(), zorder=4)

    # Plot historical observed track (if provided) as dashed line
    if obs_track_historical is not None:
        ax.plot(obs_track_historical['lon'], obs_track_historical['lat'],
               marker='*', markersize=6, linewidth=2,
               color=COLORS['observation'], linestyle='--', alpha=0.7,
               transform=ccrs.PlateCarree(), zorder=4)

    # Plot observed track (forecast period)
    ax.plot(obs_track['lon'], obs_track['lat'],
           marker='*', markersize=8, linewidth=2.5,
           color=COLORS['observation'], label='Observed',
           transform=ccrs.PlateCarree(), zorder=5)

    # Mark observed start point (of forecast period)
    ax.plot(obs_track['lon'][0], obs_track['lat'][0],
           marker='*', markersize=12, color=COLORS['observation'],
           markeredgecolor='black', markeredgewidth=1,
           transform=ccrs.PlateCarree(), zorder=6)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")

    return fig


def plot_error_evolution(errors_dict, lead_times, ylabel, title, save_path,
                        show_init_spread=False):
    """
    Plot error evolution vs lead time.

    Parameters
    ----------
    errors_dict : dict
        Dictionary mapping labels to error arrays
        E.g., {'06 UTC': [err_24h, err_48h, ...], '12 UTC': [...]}
        NOTE: Arrays can have different lengths (will be interpolated to common lead_times)
    lead_times : array-like
        Lead times in hours for reference (use longest available)
    ylabel : str
        Y-axis label (e.g., "Track Error (km)")
    title : str
        Plot title
    save_path : str or Path
        Path to save figure
    show_init_spread : bool, optional
        Show shaded region for initialization spread

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object
    """
    import numpy as np

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    colors = [COLORS['forecast'], COLORS['forecast_alt'], '#2ECC71', '#F39C12']

    # Handle different length arrays by using each series' own lead times
    for i, (label, errors) in enumerate(errors_dict.items()):
        color = colors[i % len(colors)]

        # Use first N lead times matching error array length
        series_lead_times = lead_times[:len(errors)] if len(errors) <= len(lead_times) else lead_times

        ax.plot(series_lead_times, errors,
               marker='o', markersize=6, linewidth=2,
               color=color, label=label)

    # Show initialization spread if requested
    if show_init_spread and len(errors_dict) > 1:
        all_errors = np.array(list(errors_dict.values()))
        mean_errors = np.mean(all_errors, axis=0)
        std_errors = np.std(all_errors, axis=0)

        ax.fill_between(lead_times,
                        mean_errors - std_errors,
                        mean_errors + std_errors,
                        alpha=0.2, color='gray',
                        label='Init spread (±1σ)')

    ax.set_xlabel('Lead Time (hours)', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Convert lead time to days on secondary axis
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(ax.get_xticks())
    ax2.set_xticklabels([f'{int(h/24)}d' for h in ax.get_xticks()])
    ax2.set_xlabel('Lead Time (days)', fontsize=12)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")

    return fig


def plot_error_by_valid_time(forecast_tracks_dict, errors_dict, target_time=None,
                              ylabel="Track Error (km)", title="", save_path=None,
                              valid_times_dict=None, xaxis_hours=None):
    """
    Plot error evolution vs forecast valid time (not lead time from init).

    Shows all forecasts on same timeline, converging at target event time.
    This makes it clear that different initialization lead times are predicting
    the SAME event, and longer leads have larger errors for the same target.

    Parameters
    ----------
    forecast_tracks_dict : dict
        Dictionary mapping labels to forecast track dicts with 'time' key
        E.g., {'1-day lead': {'time': [...], 'lat': [...], 'lon': [...]}, ...}
    errors_dict : dict
        Dictionary mapping same labels to error arrays
        E.g., {'1-day lead': [err1, err2, ...], ...}
    target_time : datetime, optional
        Target event time to mark with vertical line (e.g., landfall)
    ylabel : str
        Y-axis label
    title : str
        Plot title
    save_path : str or Path
        Path to save figure
    valid_times_dict : dict, optional
        Dictionary mapping labels to lists of valid times for each error point
        If provided, uses these times instead of slicing forecast_track['time']
    xaxis_hours : list of int, optional
        Hours to show on x-axis (e.g., [0, 12] or [6, 18])
        Default: [6, 18]

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object
    """
    import numpy as np
    import matplotlib.dates as mdates
    from datetime import datetime

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    colors = [COLORS['forecast'], COLORS['forecast_alt'], '#2ECC71', '#F39C12']

    # Plot each forecast's error evolution vs its valid times
    for i, (label, errors) in enumerate(errors_dict.items()):
        if label not in forecast_tracks_dict:
            continue

        # Use valid_times if provided, otherwise use forecast track times
        if valid_times_dict is not None and label in valid_times_dict:
            plot_times = valid_times_dict[label]
        else:
            forecast_track = forecast_tracks_dict[label]
            times = forecast_track['time']
            # Match errors length with times length
            plot_times = times[:len(errors)]

        color = colors[i % len(colors)]
        ax.plot(plot_times, errors,
               marker='o', markersize=6, linewidth=2,
               color=color, label=label)

    # Mark target time if provided
    if target_time is not None:
        ax.axvline(target_time, color='red', linestyle='--', linewidth=2,
                  alpha=0.7, label='Target (Landfall)')

    # Format x-axis for dates
    # Default to [6, 18] if not specified (matches most TC init/target times)
    if xaxis_hours is None:
        xaxis_hours = [6, 18]

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %HUTC'))
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=xaxis_hours))

    # Add margins to prevent label overlap with axis boundaries
    ax.margins(x=0.02)

    fig.autofmt_xdate(rotation=45, ha='right')

    ax.set_xlabel('Forecast Valid Time', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {save_path}")

    return fig


def plot_spatial_field(data, lat, lon, title, save_path,
                       vmin=None, vmax=None, cmap='viridis',
                       colorbar_label='', extent=None, projection=None):
    """
    Plot spatial field on map.

    Parameters
    ----------
    data : numpy.ndarray
        2D array of data to plot (lat, lon)
    lat : numpy.ndarray
        Latitude values
    lon : numpy.ndarray
        Longitude values
    title : str
        Plot title
    save_path : str or Path
        Path to save figure
    vmin, vmax : float or None, optional
        Color scale limits
    cmap : str, optional
        Colormap name (default: 'viridis')
    colorbar_label : str, optional
        Colorbar label
    extent : list or None, optional
        Map extent [lon_min, lon_max, lat_min, lat_max]
    projection : cartopy.crs or None, optional
        Map projection (default: PlateCarree)

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object
    """
    if projection is None:
        projection = ccrs.PlateCarree()

    fig = plt.figure(figsize=(12, 8), dpi=300)
    ax = plt.axes(projection=projection)
    ax = setup_map(ax, extent=extent)

    # Plot data
    mesh = ax.pcolormesh(lon, lat, data,
                        transform=ccrs.PlateCarree(),
                        cmap=cmap, vmin=vmin, vmax=vmax,
                        zorder=2)

    # Add colorbar
    cbar = plt.colorbar(mesh, ax=ax, orientation='horizontal',
                       pad=0.05, shrink=0.8)
    cbar.set_label(colorbar_label, fontsize=11)

    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")

    return fig


def plot_field_comparison(forecast, truth, lat, lon, variable_name,
                         title, save_path, vmin=None, vmax=None,
                         cmap='RdYlBu_r', extent=None):
    """
    Plot forecast, truth, and difference side by side.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field (2D: lat, lon)
    truth : numpy.ndarray
        Truth field (2D: lat, lon)
    lat : numpy.ndarray
        Latitude values
    lon : numpy.ndarray
        Longitude values
    variable_name : str
        Variable name for labels
    title : str
        Main title
    save_path : str or Path
        Path to save figure
    vmin, vmax : float or None, optional
        Color scale limits for forecast and truth
    cmap : str, optional
        Colormap (default: 'RdYlBu_r')
    extent : list or None, optional
        Map extent

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object
    """
    fig = plt.figure(figsize=(18, 5), dpi=300)

    # Forecast
    ax1 = plt.subplot(1, 3, 1, projection=ccrs.PlateCarree())
    ax1 = setup_map(ax1, extent=extent)
    mesh1 = ax1.pcolormesh(lon, lat, forecast, transform=ccrs.PlateCarree(),
                          cmap=cmap, vmin=vmin, vmax=vmax, zorder=2)
    ax1.set_title(f'Forecast {variable_name}', fontsize=12, fontweight='bold')
    plt.colorbar(mesh1, ax=ax1, orientation='horizontal', pad=0.05, shrink=0.8)

    # Truth
    ax2 = plt.subplot(1, 3, 2, projection=ccrs.PlateCarree())
    ax2 = setup_map(ax2, extent=extent)
    mesh2 = ax2.pcolormesh(lon, lat, truth, transform=ccrs.PlateCarree(),
                          cmap=cmap, vmin=vmin, vmax=vmax, zorder=2)
    ax2.set_title(f'ERA5 {variable_name}', fontsize=12, fontweight='bold')
    plt.colorbar(mesh2, ax=ax2, orientation='horizontal', pad=0.05, shrink=0.8)

    # Difference
    ax3 = plt.subplot(1, 3, 3, projection=ccrs.PlateCarree())
    ax3 = setup_map(ax3, extent=extent)
    diff = forecast - truth
    diff_max = np.max(np.abs(diff))
    mesh3 = ax3.pcolormesh(lon, lat, diff, transform=ccrs.PlateCarree(),
                          cmap='RdBu_r', vmin=-diff_max, vmax=diff_max, zorder=2)
    ax3.set_title(f'Difference (Forecast - ERA5)', fontsize=12, fontweight='bold')
    plt.colorbar(mesh3, ax=ax3, orientation='horizontal', pad=0.05, shrink=0.8)

    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")

    return fig


def plot_multi_init_field_comparison(forecast_dict, truth, lat, lon, variable_name,
                                     title, save_path, vmin=None, vmax=None,
                                     cmap='RdYlBu_r', extent=None):
    """
    Plot multiple initialization forecasts with truth and mean difference in 2x3 grid.

    Layout:
    Row 1: [00 UTC] [06 UTC] [12 UTC]
    Row 2: [18 UTC] [ERA5]   [Mean Difference]

    Parameters
    ----------
    forecast_dict : dict
        Dictionary mapping init times to forecast fields
        E.g., {'00': field_00utc, '06': field_06utc, '12': field_12utc, '18': field_18utc}
    truth : numpy.ndarray
        Truth field (2D: lat, lon)
    lat : numpy.ndarray
        Latitude values
    lon : numpy.ndarray
        Longitude values
    variable_name : str
        Variable name for labels
    title : str
        Main title
    save_path : str or Path
        Path to save figure
    vmin, vmax : float or None, optional
        Color scale limits for forecasts and truth
    cmap : str, optional
        Colormap (default: 'RdYlBu_r')
    extent : list or None, optional
        Map extent [lon_min, lon_max, lat_min, lat_max]

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object
    """
    fig = plt.figure(figsize=(18, 12), dpi=300)

    # Row 1: 00, 06, 12 UTC forecasts
    init_times = ['00', '06', '12', '18']

    for i, init_hour in enumerate(init_times[:3]):  # First row: 00, 06, 12
        ax = plt.subplot(2, 3, i+1, projection=ccrs.PlateCarree())
        ax = setup_map(ax, extent=extent)

        forecast = forecast_dict[init_hour]
        mesh = ax.pcolormesh(lon, lat, forecast, transform=ccrs.PlateCarree(),
                           cmap=cmap, vmin=vmin, vmax=vmax, zorder=2)
        ax.set_title(f'{init_hour} UTC', fontsize=12, fontweight='bold')
        plt.colorbar(mesh, ax=ax, orientation='horizontal', pad=0.05, shrink=0.8)

    # Row 2, Col 1: 18 UTC forecast
    ax4 = plt.subplot(2, 3, 4, projection=ccrs.PlateCarree())
    ax4 = setup_map(ax4, extent=extent)
    forecast_18 = forecast_dict['18']
    mesh4 = ax4.pcolormesh(lon, lat, forecast_18, transform=ccrs.PlateCarree(),
                          cmap=cmap, vmin=vmin, vmax=vmax, zorder=2)
    ax4.set_title('18 UTC', fontsize=12, fontweight='bold')
    plt.colorbar(mesh4, ax=ax4, orientation='horizontal', pad=0.05, shrink=0.8)

    # Row 2, Col 2: ERA5 truth
    ax5 = plt.subplot(2, 3, 5, projection=ccrs.PlateCarree())
    ax5 = setup_map(ax5, extent=extent)
    mesh5 = ax5.pcolormesh(lon, lat, truth, transform=ccrs.PlateCarree(),
                          cmap=cmap, vmin=vmin, vmax=vmax, zorder=2)
    ax5.set_title(f'ERA5 {variable_name}', fontsize=12, fontweight='bold')
    plt.colorbar(mesh5, ax=ax5, orientation='horizontal', pad=0.05, shrink=0.8)

    # Row 2, Col 3: Mean difference
    ax6 = plt.subplot(2, 3, 6, projection=ccrs.PlateCarree())
    ax6 = setup_map(ax6, extent=extent)

    # Compute mean forecast across all init times
    all_forecasts = np.stack([forecast_dict[h] for h in init_times])
    mean_forecast = np.mean(all_forecasts, axis=0)
    diff = mean_forecast - truth
    diff_max = np.max(np.abs(diff))

    mesh6 = ax6.pcolormesh(lon, lat, diff, transform=ccrs.PlateCarree(),
                          cmap='RdBu_r', vmin=-diff_max, vmax=diff_max, zorder=2)
    ax6.set_title('Mean Difference (Forecast - ERA5)', fontsize=12, fontweight='bold')
    plt.colorbar(mesh6, ax=ax6, orientation='horizontal', pad=0.05, shrink=0.8)

    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")

    return fig

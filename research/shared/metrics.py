"""
Metrics computation utilities for forecast verification.

This module contains functions for computing standard forecast verification
metrics used across all event types.
"""

import numpy as np


def compute_rmse(forecast, truth, mask=None):
    """
    Compute Root Mean Square Error.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field (any shape)
    truth : numpy.ndarray
        Truth/verification field (same shape as forecast)
    mask : numpy.ndarray or None, optional
        Boolean mask (True = include, False = exclude)
        Same shape as forecast/truth

    Returns
    -------
    float
        RMSE value

    Example
    -------
    >>> forecast_temp = np.array([[280, 285], [290, 295]])
    >>> truth_temp = np.array([[281, 284], [291, 294]])
    >>> rmse = compute_rmse(forecast_temp, truth_temp)
    """
    if mask is not None:
        forecast = forecast[mask]
        truth = truth[mask]

    squared_error = (forecast - truth) ** 2
    rmse = np.sqrt(np.mean(squared_error))

    return rmse


def compute_bias(forecast, truth, mask=None):
    """
    Compute mean bias (forecast - truth).

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field
    truth : numpy.ndarray
        Truth field
    mask : numpy.ndarray or None, optional
        Boolean mask

    Returns
    -------
    float
        Mean bias (positive = forecast too high, negative = forecast too low)
    """
    if mask is not None:
        forecast = forecast[mask]
        truth = truth[mask]

    bias = np.mean(forecast - truth)

    return bias


def compute_acc(forecast, truth, climatology, mask=None):
    """
    Compute Anomaly Correlation Coefficient.

    ACC measures pattern correlation of anomalies from climatology.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field
    truth : numpy.ndarray
        Truth field
    climatology : numpy.ndarray
        Climatological mean field (same shape)
    mask : numpy.ndarray or None, optional
        Boolean mask

    Returns
    -------
    float
        ACC value (range: -1 to 1, where 1 = perfect correlation)

    Notes
    -----
    ACC = correlation(forecast - climo, truth - climo)
    """
    if mask is not None:
        forecast = forecast[mask]
        truth = truth[mask]
        climatology = climatology[mask]

    # Compute anomalies
    forecast_anom = forecast - climatology
    truth_anom = truth - climatology

    # Compute correlation
    numerator = np.sum(forecast_anom * truth_anom)
    denominator = np.sqrt(np.sum(forecast_anom**2) * np.sum(truth_anom**2))

    if denominator == 0:
        return np.nan

    acc = numerator / denominator

    return acc


def compute_spatial_correlation(forecast, truth, mask=None):
    """
    Compute spatial pattern correlation.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field
    truth : numpy.ndarray
        Truth field
    mask : numpy.ndarray or None, optional
        Boolean mask

    Returns
    -------
    float
        Spatial correlation coefficient (range: -1 to 1)
    """
    if mask is not None:
        forecast = forecast[mask]
        truth = truth[mask]

    # Flatten arrays
    forecast_flat = forecast.flatten()
    truth_flat = truth.flatten()

    # Compute correlation
    correlation = np.corrcoef(forecast_flat, truth_flat)[0, 1]

    return correlation


def compute_mae(forecast, truth, mask=None):
    """
    Compute Mean Absolute Error.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field
    truth : numpy.ndarray
        Truth field
    mask : numpy.ndarray or None, optional
        Boolean mask

    Returns
    -------
    float
        MAE value
    """
    if mask is not None:
        forecast = forecast[mask]
        truth = truth[mask]

    mae = np.mean(np.abs(forecast - truth))

    return mae


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great circle distance using Haversine formula.

    Parameters
    ----------
    lat1, lon1 : float or array-like
        Latitude and longitude of first point(s) in degrees
    lat2, lon2 : float or array-like
        Latitude and longitude of second point(s) in degrees

    Returns
    -------
    float or numpy.ndarray
        Distance in kilometers

    Example
    -------
    >>> # Single point distance
    >>> dist = calculate_distance(40.7, -74.0, 34.0, -118.2)  # NYC to LA
    >>> print(f"Distance: {dist:.1f} km")
    >>>
    >>> # Track distance over time
    >>> lats_forecast = np.array([25, 26, 27])
    >>> lons_forecast = np.array([-80, -81, -82])
    >>> lats_obs = np.array([25.1, 26.2, 27.1])
    >>> lons_obs = np.array([-80.1, -81.2, -82.1])
    >>> distances = calculate_distance(lats_forecast, lons_forecast, lats_obs, lons_obs)
    """
    # Earth radius in km
    R = 6371.0

    # Convert to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    distance = R * c

    return distance


def compute_percentile_metrics(forecast, truth, percentiles=[50, 75, 90, 95, 99]):
    """
    Compute metrics at different percentiles of the distribution.

    Useful for evaluating extreme values.

    Parameters
    ----------
    forecast : numpy.ndarray
        Forecast field
    truth : numpy.ndarray
        Truth field
    percentiles : list of float, optional
        Percentiles to compute (default: [50, 75, 90, 95, 99])

    Returns
    -------
    dict
        Dictionary with keys:
        - 'percentiles': list of percentile values
        - 'forecast_values': forecast values at each percentile
        - 'truth_values': truth values at each percentile
        - 'bias': bias at each percentile
        - 'relative_bias': relative bias at each percentile (%)

    Example
    -------
    >>> metrics = compute_percentile_metrics(forecast_precip, truth_precip)
    >>> print(f"95th percentile bias: {metrics['bias'][3]:.2f} mm/day")
    """
    results = {
        'percentiles': percentiles,
        'forecast_values': [],
        'truth_values': [],
        'bias': [],
        'relative_bias': []
    }

    for p in percentiles:
        f_val = np.percentile(forecast, p)
        t_val = np.percentile(truth, p)
        bias = f_val - t_val
        rel_bias = (bias / t_val * 100) if t_val != 0 else np.nan

        results['forecast_values'].append(f_val)
        results['truth_values'].append(t_val)
        results['bias'].append(bias)
        results['relative_bias'].append(rel_bias)

    return results

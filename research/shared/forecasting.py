"""
Forecasting utilities for Aurora model runs.

This module contains functions for running Aurora forecasts with proper
rollout handling and memory management.
"""

import torch
from aurora import rollout


def run_forecast(model, batch, tracker, steps, name="forecast", device="cuda", verbose=True):
    """
    Run Aurora forecast with tracking.

    Parameters
    ----------
    model : aurora.Aurora
        Aurora model instance (already loaded and on device)
    batch : aurora.Batch
        Initial conditions batch
    tracker : aurora.Tracker or None
        Tracker instance for TC tracking, or None if not tracking
    steps : int
        Number of forecast steps (each step = 6 hours)
    name : str, optional
        Name for logging (default: "forecast")
    device : str, optional
        Device to use ('cuda' or 'cpu', default: 'cuda')
    verbose : bool, optional
        Print progress messages (default: True)

    Returns
    -------
    list of aurora.Batch
        List of predicted batches at each timestep

    Notes
    -----
    - Predictions are moved to CPU after each step to save GPU memory
    - If tracker fails at any step, tracking stops but forecast continues
    - GPU memory is cleared periodically (every 5 steps) when using CUDA
    """
    if verbose:
        print(f"   Running {name} for {steps} steps ({steps*6} hours)...")

    preds = []

    with torch.inference_mode():
        for i, pred in enumerate(rollout(model, batch, steps=steps)):
            # Move prediction to CPU to save GPU memory
            pred = pred.to("cpu")
            preds.append(pred)

            # Track cyclone if tracker provided
            if tracker is not None:
                try:
                    tracker.step(pred)
                except Exception as e:
                    if verbose:
                        print(f"   Warning: Tracker failed at step {i+1}: {e}")
                    # Continue without tracking remaining steps
                    tracker = None

            # Clear GPU memory periodically
            if device == "cuda" and i % 5 == 0:
                torch.cuda.empty_cache()

            if verbose and (i + 1) % 4 == 0:
                print(f"      Completed {i+1}/{steps} steps ({(i+1)*6} hours)")

    if verbose:
        print(f"   Forecast complete: {len(preds)} timesteps")

    return preds


def run_multi_init_forecast(model, static_vars_ds, surf_vars_ds, atmos_vars_ds,
                            init_hours, steps, tracker_class=None, device="cuda", verbose=True):
    """
    Run multiple forecasts from different initialization times.

    Parameters
    ----------
    model : aurora.Aurora
        Aurora model instance
    static_vars_ds : xarray.Dataset
        Static variables dataset
    surf_vars_ds : xarray.Dataset
        Surface variables dataset
    atmos_vars_ds : xarray.Dataset
        Atmospheric variables dataset
    init_hours : list of int
        Initialization hours (e.g., [0, 6, 12, 18])
    steps : int
        Number of forecast steps for each initialization
    tracker_class : class or None, optional
        Tracker class to instantiate for each forecast (e.g., aurora.Tracker)
        Set to None if not tracking (default: None)
    device : str, optional
        Device to use (default: 'cuda')
    verbose : bool, optional
        Print progress (default: True)

    Returns
    -------
    dict
        Dictionary mapping init hour to (predictions, tracker):
        {
            0: (preds_list, tracker_instance),
            6: (preds_list, tracker_instance),
            ...
        }

    Example
    -------
    >>> from aurora import Aurora, Tracker
    >>> model = Aurora(use_lora=False)
    >>> model.load_checkpoint("aurora", "microsoft/aurora")
    >>> model = model.to("cuda").eval()
    >>>
    >>> results = run_multi_init_forecast(
    ...     model, static_ds, surf_ds, atmos_ds,
    ...     init_hours=[6, 12],
    ...     steps=28,  # 7 days
    ...     tracker_class=Tracker
    ... )
    >>>
    >>> # Access results
    >>> preds_06, tracker_06 = results[6]
    >>> preds_12, tracker_12 = results[12]
    """
    from .data_loading import get_time_indices_from_hour, create_aurora_batch

    if verbose:
        print(f"\nRunning multi-initialization forecast:")
        print(f"  Initialization times: {init_hours} UTC")
        print(f"  Forecast length: {steps} steps ({steps*6} hours / {steps*6/24:.1f} days)")

    # Get time indices for each initialization hour
    time_indices = get_time_indices_from_hour(surf_vars_ds, init_hours)

    results = {}

    for hour in init_hours:
        if hour not in time_indices:
            print(f"  Warning: Hour {hour} not found in dataset, skipping")
            continue

        if verbose:
            print(f"\n  === Initialization: {hour:02d}:00 UTC ===")

        # Create batch for this initialization
        batch = create_aurora_batch(
            static_vars_ds, surf_vars_ds, atmos_vars_ds,
            time_start_idx=time_indices[hour]
        )

        # Create tracker if requested
        tracker = tracker_class() if tracker_class is not None else None

        # Run forecast
        preds = run_forecast(
            model, batch, tracker, steps,
            name=f"{hour:02d}UTC",
            device=device,
            verbose=verbose
        )

        results[hour] = (preds, tracker)

    if verbose:
        print(f"\nMulti-initialization forecast complete: {len(results)} forecasts")

    return results


def extract_field_from_predictions(preds, variable, level_idx=None):
    """
    Extract a specific variable from list of prediction batches.

    Parameters
    ----------
    preds : list of aurora.Batch
        List of prediction batches from run_forecast
    variable : str
        Variable name, one of:
        - Surface: '2t', '10u', '10v', 'msl'
        - Atmospheric: 't', 'u', 'v', 'q', 'z' (requires level_idx)
    level_idx : int or None, optional
        Pressure level index for atmospheric variables (0-12)
        Required for atmospheric variables, ignored for surface

    Returns
    -------
    list of numpy.ndarray
        List of 2D arrays (lat, lon) for each timestep

    Example
    -------
    >>> preds = run_forecast(model, batch, tracker, steps=8)
    >>> # Extract surface temperature at all timesteps
    >>> temps = extract_field_from_predictions(preds, '2t')
    >>> # Extract 700 hPa geopotential (level_idx=6 for 700 hPa)
    >>> z700 = extract_field_from_predictions(preds, 'z', level_idx=6)
    """
    fields = []

    for pred in preds:
        # Check if surface or atmospheric variable
        if variable in ['2t', '10u', '10v', 'msl']:
            # Surface variable
            field = pred.surf_vars[variable][0, -1].numpy()  # [batch, time, lat, lon]
        else:
            # Atmospheric variable
            if level_idx is None:
                raise ValueError(f"level_idx required for atmospheric variable '{variable}'")
            field = pred.atmos_vars[variable][0, -1, level_idx].numpy()  # [batch, time, level, lat, lon]

        fields.append(field)

    return fields

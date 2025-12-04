"""
Utilities for saving and loading Aurora predictions.

This avoids having to re-run expensive forecasts when:
- Fixing visualization bugs
- Trying different plot styles
- Computing additional metrics
- Regenerating figures
"""

import pickle
import json
from pathlib import Path
import numpy as np
import torch
from datetime import datetime


def batch_to_dict(batch):
    """
    Convert Aurora Batch object to dictionary for saving.

    Parameters
    ----------
    batch : aurora.Batch
        Aurora batch object

    Returns
    -------
    dict
        Dictionary with arrays and metadata
    """
    return {
        'surf_vars': {k: v.cpu().numpy() for k, v in batch.surf_vars.items()},
        'static_vars': {k: v.cpu().numpy() for k, v in batch.static_vars.items()},
        'atmos_vars': {k: v.cpu().numpy() for k, v in batch.atmos_vars.items()},
        'metadata': {
            'lat': batch.metadata.lat.cpu().numpy(),
            'lon': batch.metadata.lon.cpu().numpy(),
            'time': [t.isoformat() for t in batch.metadata.time],
            'atmos_levels': list(batch.metadata.atmos_levels) if isinstance(batch.metadata.atmos_levels, tuple) else batch.metadata.atmos_levels.tolist()
        }
    }


def batches_to_dicts(batches):
    """
    Convert list of Aurora Batch objects to list of dictionaries.

    Parameters
    ----------
    batches : list of aurora.Batch
        List of batch objects

    Returns
    -------
    list of dict
        List of dictionaries
    """
    if batches is None:
        return None
    return [batch_to_dict(b) for b in batches]


def save_forecast_results(results, output_path, metadata=None, save_predictions=True):
    """
    Save forecast results to disk.

    Parameters
    ----------
    results : dict
        Results dictionary with forecast tracks, predictions, errors, etc.
        If 'predictions' key exists and contains Aurora Batch objects,
        they will be converted to dictionaries for saving.
    output_path : str or Path
        Path to save results (will create .pkl file)
    metadata : dict, optional
        Additional metadata to save (event name, config, etc.)
    save_predictions : bool, optional
        Whether to save full prediction fields (default: True)
        Set to False to save only tracks/metrics (smaller file size)

    Returns
    -------
    Path
        Path to saved file

    Example
    -------
    >>> results = {
    ...     'forecast_track': {'time': [...], 'lat': [...], 'lon': [...]},
    ...     'predictions': [batch1, batch2, ...],  # Aurora Batch objects
    ...     'errors_data': {'lead_times': [...], 'errors': [...]},
    ...     'summary': {...}
    ... }
    >>> save_forecast_results(results, 'sandy_12utc_results.pkl')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert Aurora Batch objects to dictionaries if present
    results_to_save = results.copy()
    if save_predictions and 'predictions' in results_to_save:
        results_to_save['predictions'] = batches_to_dicts(results_to_save['predictions'])

    # Add timestamp
    save_data = {
        'results': results_to_save,
        'metadata': metadata or {},
        'saved_at': datetime.now().isoformat(),
        'has_predictions': save_predictions and 'predictions' in results
    }

    # Save as pickle
    with open(output_path, 'wb') as f:
        pickle.dump(save_data, f)

    print(f"✓ Saved results: {output_path}")

    # Also save a JSON summary (human-readable)
    json_path = output_path.with_suffix('.json')
    json_summary = {
        'saved_at': save_data['saved_at'],
        'metadata': metadata or {},
        'num_forecast_positions': len(results.get('forecast_track', {}).get('time', [])),
        'num_errors': len(results.get('errors_data', {}).get('errors', [])),
    }

    if 'summary' in results and results['summary']:
        json_summary['performance'] = {
            'mean_error_km': results['summary'].get('mean_error'),
            'error_24h_km': results['summary'].get('error_24h'),
            'error_48h_km': results['summary'].get('error_48h'),
            'error_72h_km': results['summary'].get('error_72h'),
        }

    with open(json_path, 'w') as f:
        json.dump(json_summary, f, indent=2)

    print(f"✓ Saved summary: {json_path}")

    return output_path


def load_forecast_results(input_path):
    """
    Load saved forecast results.

    Parameters
    ----------
    input_path : str or Path
        Path to saved .pkl file

    Returns
    -------
    dict
        Loaded results dictionary

    Example
    -------
    >>> results = load_forecast_results('sandy_12utc_results.pkl')
    >>> forecast_track = results['forecast_track']
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    with open(input_path, 'rb') as f:
        save_data = pickle.load(f)

    print(f"✓ Loaded results from {input_path}")
    print(f"  Saved at: {save_data['saved_at']}")

    return save_data['results']


def save_multi_init_results(all_results, output_path, metadata=None, save_predictions=True):
    """
    Save results from multiple initialization times.

    Parameters
    ----------
    all_results : dict
        Dictionary mapping init times to their results
        E.g., {1: {...}, 3: {...}, 5: {...}} for lead times
        or {'00': {...}, '06': {...}, '12': {...}} for init times
    output_path : str or Path
        Path to save results
    metadata : dict, optional
        Event metadata
    save_predictions : bool, optional
        Whether to save full prediction fields (default: True)

    Example
    -------
    >>> all_results = {
    ...     1: {'forecast_track': ..., 'predictions': [...], ...},
    ...     3: {'forecast_track': ..., 'predictions': [...], ...},
    ...     5: {'forecast_track': ..., 'predictions': [...], ...},
    ... }
    >>> save_multi_init_results(all_results, 'sandy_stage1_results.pkl')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert Aurora Batch objects to dictionaries for each result
    all_results_to_save = {}
    for key, results in all_results.items():
        results_copy = results.copy()
        if save_predictions and 'predictions' in results_copy:
            results_copy['predictions'] = batches_to_dicts(results_copy['predictions'])
        all_results_to_save[key] = results_copy

    save_data = {
        'all_results': all_results_to_save,
        'metadata': metadata or {},
        'saved_at': datetime.now().isoformat(),
        'init_times': list(all_results.keys()),
        'has_predictions': save_predictions
    }

    # Save pickle
    with open(output_path, 'wb') as f:
        pickle.dump(save_data, f)

    print(f"✓ Saved multi-init results: {output_path}")

    # JSON summary
    json_path = output_path.with_suffix('.json')
    json_summary = {
        'saved_at': save_data['saved_at'],
        'metadata': metadata or {},
        'init_times': save_data['init_times'],
        'performance_by_init': {}
    }

    for init_time, results in all_results.items():
        if 'summary' in results and results['summary']:
            json_summary['performance_by_init'][f'{init_time}UTC'] = {
                'mean_error_km': results['summary'].get('mean_error'),
                'error_24h_km': results['summary'].get('error_24h'),
                'error_48h_km': results['summary'].get('error_48h'),
                'error_72h_km': results['summary'].get('error_72h'),
            }

    with open(json_path, 'w') as f:
        json.dump(json_summary, f, indent=2)

    print(f"✓ Saved summary: {json_path}")

    return output_path


def load_multi_init_results(input_path):
    """
    Load saved multi-initialization results.

    Parameters
    ----------
    input_path : str or Path
        Path to saved .pkl file

    Returns
    -------
    dict
        Loaded results with keys:
        - 'all_results': dict mapping init times to results
        - 'metadata': event metadata
        - 'init_times': list of init times

    Example
    -------
    >>> data = load_multi_init_results('sandy_multi_init_results.pkl')
    >>> results_12utc = data['all_results']['12']
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    with open(input_path, 'rb') as f:
        save_data = pickle.load(f)

    print(f"✓ Loaded multi-init results from {input_path}")
    print(f"  Saved at: {save_data['saved_at']}")
    print(f"  Init times: {', '.join(save_data['init_times'])} UTC")

    return save_data

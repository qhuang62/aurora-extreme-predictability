# Aurora Extreme Weather Predictability Research Plan

**Last Updated**: November 10, 2025
**Status**: Active Research Project
**Target**: Paper submission within 4 weeks

---

## Project Overview

### Research Objectives

This paper provides the **first comprehensive evaluation of Aurora's predictability across multiple extreme weather types**, establishing Aurora's strengths, limitations, and predictability regimes as a foundation for future perturbation studies.

**What This Paper IS:**
- First systematic assessment of Aurora for extreme weather prediction
- Process-oriented case study approach with physical interpretation
- Identification of event-dependent predictability patterns
- Foundation for perturbation experiments (next paper)

**What This Paper IS NOT:**
- NOT a comprehensive benchmark of all ML weather models (like WeatherBench2)
- NOT a statistical survey of hundreds of events
- NOT an Aurora vs Pangu/GraphCast head-to-head comparison

### Key Research Questions

1. **Can Aurora predict diverse extreme events with useful skill?**
2. **How does predictability vary across event types with different spatiotemporal scales?**
3. **What are the practical predictability horizons for operational early warning?**
4. **Does Aurora maintain physical consistency in extreme conditions?**
5. **Where does Aurora succeed vs fail, and why?**

---

## Study Design

### Event Selection Strategy

**Selection Criteria:**
- **Out-of-sample focus**: Primarily 2020-2023 events (Aurora trained on ERA5 1979-2020)
- **High impact**: Billion-dollar disasters or >100 fatalities
- **Geographic diversity**: Multiple climate zones and ocean basins
- **Data availability**: ERA5 coverage + observational validation datasets

### Selected Events

| **Event Type** | **Out-of-Sample (2021-2023)** | **In-Sample (≤2020)** |
|----------------|-------------------------------|-------------------------|
| **TC** | Hurricane Ian 2022<br>Typhoon Hinnamnor 2022 | ✅ Sandy 2012 (COMPLETE)<br>Cyclone Amphan 2020 (boundary case) |
| **Freeze** | Texas 2021<br>UK 2022 | Beast from East 2018 |
| **AR** | California 2022-23 sequence | — |
| **Precip** | Spain Oct 2024<br>Kentucky Jul 2023<br>China Houzihe Jun 2025 | Western Europe Jul 2021 |

**Sample Size Rationale:**
- TC: 4-6 cases (2 Atlantic, 2 Western Pacific, 1-2 North Indian Ocean)
- Freeze: 3 cases (different blocking regimes and hemispheres)
- AR: 1 comprehensive case study (multi-event sequence)
- Precipitation: 3-4 high-impact cases (different climate zones)

**Total: ~12-15 events** - sufficient for process understanding while maintaining depth of analysis within AGU 12-page limit.

### Training Contamination Handling

**CRITICAL ISSUE**: Aurora trained on ERA5 1979-2020 → events ≤2020 were "seen" during training

**Solution:**
1. **Primary analysis**: Focus on 2021-2023 out-of-sample events for scientific validity
2. **Boundary case**: Amphan (May 2020) is at training cutoff - tests temporal boundary performance
3. **In-sample context**: Include select pre-2020 events (Sandy 2012, Beast from East 2018) clearly labeled as in-sample
4. **Transparency**: Explicitly state training period in methods section
5. **Discussion**: Address implications of training contamination in limitations

**TC Sample Status Clarification:**
- **In-sample**: Sandy 2012, Amphan 2020 (at boundary)
- **Out-of-sample**: Ian 2022, Hinnamnor 2022
- Balanced 2 vs 2 design allows in-sample vs out-of-sample comparison

**Current TC Status:**
- ✅ **Sandy 2012 COMPLETE** (in-sample, full two-stage analysis done, 20 figures generated)
  - Stage 1: 4 lead times tested (1, 3, 5, 7 days)
  - Stage 2: 4 init times tested (00, 06, 12, 18 UTC)
  - Results documented in `TC/2012_Sandy/SANDY_RESULTS.md`
- ✅ Nanmadol 2022 (out-of-sample, scientifically valid)
- 🔨 Ian 2022 (next priority)
- 🔨 Hinnamnor 2022 (next priority)

---

## Experimental Framework

### Standard Protocol (Apply to ALL Events)

#### Step 1: Initialization Sensitivity
- **Test**: 00, 06, 12, 18 UTC initializations
- **Objective**: Identify optimal initialization time for each event type
- **Metric**: Quantify initialization-dependent uncertainty (ensemble spread)

#### Step 2: Lead Time Analysis
- **Forecast lengths**: 1-day, 3-day, 5-day, 7-day
- **Analysis**: Plot skill degradation curves
- **Output**: Identify practical predictability horizon for each event type

#### Step 3: Physical Consistency Checks
- **Energy**: Check if total column energy conserved
- **Moisture**: Verify precipitable water conservation
- **Dynamics**: Geostrophic balance, thermal wind relationship
- **Extremes**: Does Aurora maintain realistic extreme values or dampen them?

#### Step 4: Verification
- **Primary**: Against ERA5 reanalysis (standard approach)
- **Secondary**: Against observations where available
  - TC: IBTrACS best track data
  - Freeze: Station temperature data (GHCN-Daily, E-OBS)
  - AR: AR catalogs (Guan & Waliser, ARTMIP)
  - Precipitation: IMERG GPM, CPC Unified Gauge-Based

---

## Metrics & Evaluation

### Unified Metrics Across Event Types

| **Event** | **RMSE** | **ACC** | **Spatial** | **Physical** |
|-----------|----------|---------|-------------|--------------|
| **TC** | Track error (km) | Landfall timing | Position uncertainty | MSL pressure min |
| **Freeze** | T2m anomaly (°C) | Onset timing | Cold pool extent | Jet stream pattern |
| **AR** | IVT (kg/m/s) | AR arrival time | AR width/length | Moisture flux |
| **Precip** | Precip rate (mm/day) | Peak timing | Spatial correlation | Moisture convergence |

### Event-Specific Metrics

**Tropical Cyclones:**
- Track error (km) at 24h, 48h, 72h, 120h, 168h lead times
- Landfall location error (km)
- Landfall timing error (hours)
- Minimum sea-level pressure (hPa) - intensity proxy
- Position uncertainty ellipse area (km²)

**Freeze/Cold Snaps:**
- 2-meter temperature RMSE (°C) over affected region
- Temperature anomaly correlation with ERA5
- Cold pool spatial extent (km² below threshold)
- Jet stream position RMSE (latitude)
- Onset timing accuracy (hours before critical temperature)

**Atmospheric Rivers:**
- IVT magnitude RMSE (kg/m/s)
- AR detection success rate (hits, misses, false alarms)
- AR arrival timing error (hours)
- AR geometry (length, width) accuracy
- Precipitation accumulation correlation

**Precipitation Extremes:**
- Precipitation rate RMSE (mm/day)
- Spatial pattern correlation
- Peak timing accuracy (hours)
- Intensity bias (systematic over/underestimation)
- Scale-dependent performance (grid box vs regional aggregate)

### Tropical Cyclone Metrics: Track Error vs Landfall Position Error

**Important Clarification**: TC analysis uses two complementary metrics that measure different aspects of forecast skill:

#### 1. Track Error (Time-Synchronized)

**Definition**: Position error between Aurora's tracker and IBTrACS observations at each forecast timestep.

**Calculation**:
```
For each timestep t in forecast:
  track_error(t) = distance(Aurora_tracker(t), IBTrACS(t))

Mean track error = average(all track_error values)
Final track error = track_error(last timestep)
24h/48h/72h errors = track_error at specific lead times
```

**What it measures**:
- Day-to-day tracking skill throughout the forecast
- Consistency of position prediction over time
- Time-synchronized: compares same times in Aurora and IBTrACS

**Usage**: Shown in track error evolution plots (error vs valid time)

#### 2. Landfall Position Error (Location-Focused)

**Definition**: Distance between TC center locations in Aurora's MSL field vs ERA5's MSL field at landfall.

**Calculation**:
```
1. Find Aurora timestep spatially closest to landfall location
2. Extract Aurora's MSL field at that timestep
3. Extract ERA5's MSL field at landfall marker time
4. Find MSL minimum in Aurora field → Aurora TC center
5. Find MSL minimum in ERA5 field → ERA5 TC center
6. landfall_position_error = distance(Aurora_center, ERA5_center)
```

**What it measures**:
- Final location accuracy at critical landfall time
- Uses MSL field minimum (not tracker position)
- **May compare different times**: Aurora's forecast endpoint vs ERA5's landfall marker
- Operationally relevant: "Where will the TC hit?"

**Usage**: Reported in CSV results and field comparison plots

#### Why These Metrics Can Differ Significantly

**Example: Hurricane Ian 3-day lead**
- **Track error**: 35.3 km mean, 101.2 km final
  - Aurora tracker at Sep 28 12:00 is 101 km from IBTrACS at 12:00
- **Landfall position error**: 0.0 km
  - Aurora MSL minimum at Sep 28 12:00 at exact same location as ERA5 MSL minimum at Sep 28 18:00
  - Aurora predicted TC would reach that location 6h early, but location was perfect!

**Key Insight**: These metrics are **complementary, not contradictory**:
- Good track error + good position error = Excellent forecast (smooth, accurate track)
- Good track error + poor position error = Consistent but wrong direction
- Poor track error + good position error = Wobbly track that ends in right place (**Ian case**)
- Poor track error + poor position error = Poor forecast overall

#### Operational Significance

**Track Error**:
- Important for confidence in early warnings
- Shows forecast reliability day-to-day
- Indicates systematic biases in motion prediction

**Landfall Position Error**:
- Critical for evacuation planning
- Direct answer to "where will it make landfall?"
- Less sensitive to timing errors (early vs late arrival)
- More operationally relevant for emergency management

**Bottom Line**: For TC forecasting, **landfall position error is more operationally important** than mean track error. A forecast that wobbles during the ocean phase but accurately predicts landfall location is more valuable than a smooth track that misses the landfall point.

---

## Visualization Plan

### Publication Figures (7 main figures)

**Figure 1: Event Overview Map**
- World map showing all 12-15 events analyzed
- Color-coded by event type (TC, Freeze, AR, Precip)
- Symbols indicate in-sample vs out-of-sample
- Timeline inset showing temporal coverage

**Figure 2: Tropical Cyclone Predictability**
- Panel A: Track comparison (3-4 TCs, Aurora vs observations)
- Panel B: Track error vs lead time (all TC cases)
- Panel C: Landfall timing accuracy
- Panel D: Initialization sensitivity (spread across init times)

**Figure 3: Freeze Event Analysis**
- Panel A: Temperature anomaly forecast vs ERA5 (Texas 2021 example)
- Panel B: Jet stream pattern evolution (500 hPa geopotential)
- Panel C: Cold pool extent comparison (spatial overlap)
- Panel D: Onset timing skill (all freeze events)

**Figure 4: Atmospheric River Predictability**
- Panel A: IVT field comparison (California 2022-23 example)
- Panel B: AR position tracking over time (forecast vs catalog)
- Panel C: Precipitation verification (accumulated precip)
- Panel D: Moisture flux convergence (physical consistency check)

**Figure 5: Precipitation Extremes**
- Panel A: Spatial pattern correlation (3-4 events, maps)
- Panel B: Intensity bias analysis (scatter plot, Q-Q plot)
- Panel C: Timing skill scores (peak precip timing errors)
- Panel D: Scale-dependent performance (point vs area-averaged)

**Figure 6: Cross-Event Comparison**
- Panel A: Skill score radar chart (all event types, multiple metrics)
- Panel B: Lead time degradation curves (all events overlaid)
- Panel C: Initialization sensitivity heatmap (event × init time)
- Panel D: Predictability horizon summary (bar chart by event type)

**Figure 7: Physical Consistency Analysis**
- Panel A: Energy budget conservation (scatter plot, Aurora vs ERA5)
- Panel B: Moisture conservation (precipitable water time series)
- Panel C: Extreme value distribution (PDFs, Aurora vs ERA5)
- Panel D: Geostrophic balance verification (thermal wind relationship)

### Visualization Standards

**Color Schemes** (consistent across all figures):
- **Forecasts**: Blues/purples
- **Observations/Truth**: Reds/oranges
- **Errors/Differences**: Viridis or RdYlBu diverging

**Map Projections**:
- **Global context**: PlateCarree
- **Regional mid-latitudes**: Lambert Conformal Conic
- **Tropical regions**: Mercator

**File Formats**:
- PNG at 300 DPI for all figures
- High-resolution for publication submission

**Figure Size Standards**:
- Single column: 3.5 inches wide
- Double column: 7 inches wide
- Maximum height: 9 inches
- Multi-panel layouts: consistent panel sizes

---

## Code Infrastructure

### Directory Structure

```
research/
├── RESEARCH_PLAN.md              # This file (master plan)
├── TC/                           # ✅ Tropical Cyclones (in progress)
│   ├── 2012_Sandy/              # ✅ COMPLETE (in-sample, two-stage analysis done)
│   │   ├── sandy_stage1_lead_day.py
│   │   ├── sandy_stage2_init_time.py
│   │   ├── SANDY_RESULTS.md     # ✅ Complete results & findings
│   │   └── prediction_output/   # 20 publication-quality figures
│   ├── 2022_Nanmadol/           # ✅ Complete (out-of-sample)
│   ├── 2022_Ian/                # 🔨 Next priority
│   ├── 2022_Hinnamnor/          # 🔨 Next priority
│   ├── 2020_Amphan/             # 🔨 To create
│   ├── TC_utils.py              # ✅ Shared tracking/analysis code
│   └── ProgressRecord.md        # ✅ Existing documentation
├── Freeze/                       # 🔨 New category
│   ├── 2021_Texas/
│   ├── 2022_UK/
│   ├── 2018_BeastFromEast/      # Optional
│   └── freeze_utils.py
├── AR/                           # 🔨 New category
│   ├── 2022_California/
│   └── ar_utils.py
├── Precipitation/                # 🔨 New category
│   ├── 2024_Spain/
│   ├── 2023_Kentucky/
│   ├── 2025_China_Houzihe/
│   ├── 2021_WestEurope/
│   └── precip_utils.py
└── shared/                       # 🔨 Common utilities
    ├── aurora_wrapper.py        # Unified Aurora interface
    ├── metrics.py               # Common metrics (RMSE, ACC, etc.)
    ├── visualization.py         # Standard plotting functions
    ├── verification.py          # ERA5/obs loading and comparison
    └── download_era5.py         # Bulk data acquisition script
```

### Shared Utilities Design

**`shared/aurora_wrapper.py`** - Standardized Aurora interface:
```python
class AuroraPredictor:
    """Unified interface for Aurora predictions across all event types"""

    def __init__(self, model_type='pretrained', use_lora=False, device='cuda'):
        # Load Aurora model with specified configuration

    def predict(self, init_batch, lead_time_hours, output_freq_hours=6):
        # Standard rollout with specified lead time

    def predict_multi_init(self, era5_date, init_times=[0, 6, 12, 18],
                           lead_time_hours=168):
        # Multiple initialization times for uncertainty quantification

    def predict_ensemble(self, init_batch, n_members, perturbation_config):
        # Ensemble forecasting (for perturbation experiments)
```

**`shared/metrics.py`** - Unified metrics computation:
```python
def compute_rmse(forecast, truth, variable, region=None, mask=None)
def compute_acc(forecast, truth, climatology, variable)
def compute_bias(forecast, truth, variable)
def compute_spatial_correlation(forecast, truth, variable)
def compute_pattern_correlation(forecast, truth)
def compute_track_error(forecast_track, obs_track)  # TC-specific
def compute_timing_error(forecast_series, truth_series, threshold)
```

**`shared/visualization.py`** - Publication-quality plotting:
```python
def plot_forecast_comparison(forecast, truth, variable, time, region,
                             title, save_path)
def plot_error_evolution(errors_dict, lead_times, event_types,
                         metric_name, save_path)
def plot_spatial_field(data, variable, time, region, projection,
                       colorbar_label, save_path)
def plot_track_comparison(forecast_tracks, obs_track, basin_map, save_path)
def create_multi_panel_figure(panels_config, figure_title, save_path)
```

**`shared/verification.py`** - Data loading and comparison:
```python
def load_era5_verification(date_range, variables, region)
def load_ibtracs_track(storm_name, year, basin)
def load_ar_catalog(date_range, region, algorithm='guan_waliser')
def load_station_data(station_ids, date_range, variable)
def load_precipitation_obs(date_range, region, source='IMERG')
def compare_to_era5(forecast, era5_truth, metrics_list)
def compare_to_observations(forecast, obs_data, event_type)
```

**`shared/download_era5.py`** - Automated data acquisition:
```python
def download_event_era5(event_config):
    """
    Download ERA5 data for one extreme event

    Parameters:
    - event_config: dict with keys:
        - 'name': string identifier
        - 'init_date': 'YYYY-MM-DD'
        - 'end_date': 'YYYY-MM-DD'
        - 'region': [lat_max, lon_min, lat_min, lon_max] or None for global
        - 'variables': list of variable names
    """
    pass

def download_all_events(events_list_file):
    """Batch download all events from configuration file"""
    pass
```

### Event-Specific Utilities

**TC**: `TC/TC_utils.py`
- `detect_cyclone_center()` - MSL pressure minimum + Z700 geopotential
- `track_cyclone()` - Multi-timestep tracking
- `compute_track_metrics()` - Error, timing, landfall analysis
- `compare_to_ibtracs()` - Observational validation

**Freeze**: `Freeze/freeze_utils.py`
- `detect_cold_pool()` - Temperature threshold + spatial extent
- `analyze_blocking_pattern()` - Z500 anomaly detection
- `compute_jet_position()` - Maximum wind speed latitude
- `compute_onset_timing()` - When temperature drops below threshold

**AR**: `AR/ar_utils.py`
- `compute_ivt()` - Integrated vapor transport from q, u, v
- `detect_ar()` - IVT threshold + geometry criteria
- `track_ar()` - AR position over time
- `compare_to_catalog()` - Validation against Guan/Waliser or ARTMIP

**Precipitation**: `Precipitation/precip_utils.py`
- `compute_spatial_correlation()` - Pattern correlation
- `compute_intensity_bias()` - Systematic over/underestimation
- `detect_peak_timing()` - Maximum precipitation timing
- `compute_scale_metrics()` - Grid-scale vs area-averaged performance

---

## Paper Structure

### Outline (Target: 12 pages AGU format)

**Abstract** (250 words)
- Context: Extreme weather prediction challenges
- Gap: AI model performance for extremes unclear
- Approach: Aurora evaluated on 12-15 events across 4 types
- Results: Event-dependent predictability, horizons identified
- Implications: Promising for operational use with limitations

**1. Introduction** (~2 pages)
- 1.1 Extreme weather prediction challenges and societal importance
- 1.2 Traditional NWP limitations (computational cost, localized extremes)
- 1.3 Emergence of AI weather models (GraphCast, Pangu, Aurora)
- 1.4 Knowledge gap: Extreme event predictability not systematically evaluated
- 1.5 Study objectives and event selection rationale
- 1.6 Paper structure overview

**2. Methods** (~2.5 pages)
- 2.1 Aurora Model Configuration
  - Model version: Aurora 0.25° Pretrained
  - Training period: ERA5 1979-2020
  - Input variables and resolution
  - Initialization procedure
  - Forecast configuration (lead times, output frequency)

- 2.2 Verification Datasets
  - ERA5 reanalysis (primary ground truth)
  - Observational datasets by event type
  - Out-of-sample event selection strategy
  - Training contamination handling

- 2.3 Performance Metrics
  - **Table 1**: Metrics by event type (RMSE, ACC, Spatial, Physical)
  - Initialization sensitivity analysis approach
  - Lead time degradation quantification

- 2.4 Case Study Design
  - Event selection criteria (impact, out-of-sample, data availability)
  - **Table 2**: Selected events (date, location, impact, sample status)
  - Objective detection algorithms for each event type

**3. Results** (~4 pages)
- 3.1 Tropical Cyclones
  - Track prediction skill across basins
  - **Figure 2**: Track comparisons, errors, timing, initialization
  - Lead time effects and predictability horizons
  - Landfall prediction accuracy

- 3.2 Freeze/Cold Snaps
  - Temperature anomaly prediction skill
  - **Figure 3**: Temperature, jet stream, cold pool, timing
  - Synoptic pattern reproduction
  - Onset timing and blocking pattern capture

- 3.3 Atmospheric Rivers
  - IVT and moisture flux prediction
  - **Figure 4**: IVT fields, AR tracking, precipitation, moisture flux
  - AR detection and tracking performance
  - Precipitation verification

- 3.4 Precipitation Extremes
  - Spatial pattern skill and intensity bias
  - **Figure 5**: Patterns, bias, timing, scale-dependence
  - Timing performance and scale effects
  - Challenges with localized convective events

**4. Discussion** (~2.5 pages)
- 4.1 Comparative Predictability Across Event Types
  - **Figure 6**: Cross-event skill comparison
  - Why TC/Freeze more predictable than Precip
  - Spatial scale effects on predictability
  - Dynamics (quasi-geostrophic vs moist convection)
  - Initialization sensitivity patterns

- 4.2 Lead Time vs Accuracy Trade-offs
  - Skill degradation patterns by event type
  - Practical predictability horizons:
    - TC: 5-7 days useful
    - Freeze: 5-7 days useful
    - AR: 3-5 days useful
    - Precipitation: 1-3 days useful
  - Implications for early warning systems

- 4.3 Physical Consistency
  - **Figure 7**: Energy/moisture budgets, extremes, balance
  - Energy and moisture conservation analysis
  - Extreme value representation (dampening or realistic?)
  - Dynamical balance verification
  - Comparison to NWP physical constraints

- 4.4 Aurora Performance Context
  - Literature comparison (Aurora TC paper, GraphCast, Pangu)
  - Computational efficiency (inference time vs traditional NWP)
  - Trade-offs: Speed vs physical interpretability

- 4.5 Limitations
  - **Training contamination** for pre-2020 events (addressed via out-of-sample focus)
  - Small sample size per event type (case study approach)
  - Single model evaluation (not multi-model comparison)
  - ERA5 as imperfect ground truth (also a model product)
  - Static field representation limitations

- 4.6 Implications and Future Directions
  - Aurora shows promise with event-dependent skill
  - Suitable for large-scale extreme events (TC, Freeze, AR)
  - Challenges remain for small-scale convective precipitation
  - Need for ensemble forecasting and uncertainty quantification
  - **Bridge to next paper**: Perturbation experiments to enhance predictions

**5. Conclusions** (~0.5 pages)
- Aurora successfully predicts diverse extreme events with varying skill
- Event-dependent predictability: TC/Freeze (5-7 day horizon) > AR (3-5 days) > Precip (1-3 days)
- Physical consistency generally maintained with some systematic biases
- Promising for operational early warning systems for large-scale events
- Perturbation experiments needed to improve predictions (next paper)

**References** (~1-2 pages)
**Supplementary Material** (individual event details, additional figures)

---

## Timeline & Milestones

### 4-Week Sprint to Submission

**Week 1: Infrastructure & TC Completion** (Days 1-7)
- [ ] Day 1-2: Create shared utilities (`aurora_wrapper`, `metrics`, `visualization`, `verification`)
- [ ] Day 3-4: Complete 2 additional TC cases (Ian 2022, Hinnamnor 2022)
- [ ] Day 5-7: Freeze infrastructure + Texas 2021 analysis
- **Deliverable**: TC results section draft, Freeze utilities ready, Introduction written

**Week 2: Freeze & AR Analysis** (Days 8-14)
- [ ] Day 8-10: Complete UK 2022 Freeze, Beast from East 2018
- [ ] Day 11-14: AR infrastructure + California 2022-23 complete analysis
- **Deliverable**: Freeze and AR results sections draft, Methods section complete

**Week 3: Precipitation & Cross-Event Analysis** (Days 15-21)
- [ ] Day 15-17: Precipitation infrastructure + 3-4 case analyses
- [ ] Day 18-19: Physical consistency checks (energy, moisture, dynamics)
- [ ] Day 20-21: Cross-event comparison analysis
- **Deliverable**: All results sections complete, Discussion draft started

**Week 4: Finalization & Submission Prep** (Days 22-28)
- [ ] Day 22-23: Generate all publication figures (Figures 1-7)
- [ ] Day 24-25: Complete Discussion section, polish Introduction/Methods
- [ ] Day 26-27: Write Abstract and Conclusions, format references
- [ ] Day 28: Internal review, final checks, submission preparation

### Critical Path Items (Start Immediately)

1. **ERA5 Data Downloads** - Can take 24-48 hours per event, run overnight
2. **Shared Utilities Creation** - Blocks all event-specific analysis
3. **Freeze/AR/Precip Detection Algorithms** - Need working code before analysis
4. **Observational Data Acquisition** - AR catalogs, station data, precipitation obs

---

## Data Requirements

### ERA5 Variables (All Events)

**Surface-level** (required):
- `2t`: 2-meter temperature
- `10u`: 10-meter u-component of wind
- `10v`: 10-meter v-component of wind
- `msl`: Mean sea-level pressure

**Static** (required):
- `lsm`: Land-sea mask
- `slt`: Soil type
- `z`: Geopotential (topography)

**Atmospheric** (13 pressure levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `t`: Temperature
- `u`: U-component of wind
- `v`: V-component of wind
- `q`: Specific humidity
- `z`: Geopotential

**Additional for verification**:
- `tp`: Total precipitation (for precip events)
- `tcwv`: Total column water vapor (for AR events)

### Event-Specific Data Needs

**TC Events** (~6 cases × 10 days each):
- ERA5: 7 days initialization window + 10 days verification
- IBTrACS: Best track data for all events
- Storage: ~5 GB per event = 30 GB total

**Freeze Events** (~3 cases × 14 days each):
- ERA5: 7 days initialization window + 14 days verification
- Station data: GHCN-Daily or E-OBS for affected regions
- Storage: ~6 GB per event = 18 GB total

**AR Events** (~1 case, 30 days sequence):
- ERA5: Dec 20, 2022 - Jan 20, 2023 (continuous)
- AR catalog: Guan & Waliser or ARTMIP for California
- Storage: ~15 GB total

**Precipitation Events** (~4 cases × 7 days each):
- ERA5: 3 days initialization window + 7 days verification
- IMERG GPM: High-resolution precipitation for verification
- Storage: ~4 GB per event = 16 GB total

**Total Storage Estimate**: ~80 GB for all ERA5 data

### Data Organization Structure

All data organized by event type in dedicated directories:

```
research/
├── TC/data/
│   ├── era5_sandy_2012/           # Oct 22-31, 2012 (in-sample)
│   ├── era5_ian_2022/             # Sep 23 - Oct 3, 2022
│   ├── era5_hinnamnor_2022/       # Aug 28 - Sep 8, 2022
│   └── era5_amphan_2020/          # May 15-25, 2020
│
├── Freeze/data/
│   ├── era5_texas_2021/           # Feb 9-22, 2021
│   ├── era5_uk_2022/              # Dec 3-20, 2022
│   └── era5_beasteast_2018/       # Feb 20 - Mar 7, 2018 (optional)
│
├── AR/data/
│   └── era5_california_2022_2023/ # Dec 21, 2022 - Jan 20, 2023
│
└── Precipitation/data/
    ├── era5_spain_2024/           # Oct 26 - Nov 1, 2024
    ├── era5_kentucky_2023/        # Jul 16-22, 2023
    ├── era5_china_2025/           # Jun 22-28, 2025
    └── era5_westeurope_2021/      # Jul 10-18, 2021
```

**Naming Convention**: `era5_{event}_{year}/`

### Required ERA5 Variables

**Surface-level** (single-levels):
- `2t`: 2m temperature
- `10u`, `10v`: 10m wind components
- `msl`: Mean sea level pressure

**Atmospheric** (pressure-levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `t`: Temperature
- `u`, `v`: Wind components
- `q`: Specific humidity
- `z`: Geopotential

**Static** (provided with Aurora checkpoints):
- `z`: Geopotential (topography)
- `lsm`: Land-sea mask
- `slt`: Soil type

**Temporal Resolution**: 6-hourly (00, 06, 12, 18 UTC)

### Quick Reference: Data Requirements by Event

| Event Type | Init Times | Lead Times | Data Period | Storage/Event |
|------------|-----------|------------|-------------|---------------|
| **TC** | 00/06/12/18 UTC | 1,3,5,7 days | ~11 days | ~5 GB |
| **Freeze** | 00/06/12/18 UTC | 1,3,5,7 days | ~14 days | ~6 GB |
| **AR** | 00/06/12/18 UTC | 1,3,5,7 days | ~31 days | ~15 GB |
| **Precip** | 00/06/12/18 UTC | 1,3,5,7 days | ~7 days | ~4 GB |

### Observational Datasets

**Tropical Cyclones**:
- Source: IBTrACS (https://www.ncei.noaa.gov/products/international-best-track-archive)
- Variables: Position, intensity, timing
- Format: NetCDF or CSV

**Freeze/Cold Snaps**:
- Source: GHCN-Daily (https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily)
- Source: E-OBS for Europe (https://www.ecad.eu/download/ensembles/download.php)
- Variables: Daily min/max temperature
- Format: NetCDF or CSV

**Atmospheric Rivers**:
- Source: Guan & Waliser Catalog (https://catalog.pangeo.io/browse/master/atmosphere/ar_catalog/)
- Source: ARTMIP (https://www.cgd.ucar.edu/projects/artmip/)
- Variables: AR detection, IVT, geometry
- Format: NetCDF

**Precipitation**:
- Source: IMERG GPM (https://gpm.nasa.gov/data/imerg) - primary, 2000-present
- Source: CPC Unified Gauge-Based (https://psl.noaa.gov/data/gridded/data.cpc.globalprecip.html)
- Variables: Precipitation rate (mm/day)
- Resolution: 0.1° (IMERG) or 0.5° (CPC)
- Format: NetCDF or HDF5

---

## Key Research Hypotheses

### To Test Through Analysis

**H1: Spatial Scale Hypothesis**
- **Prediction**: Predictability decreases with decreasing spatial scale
- **Test**: Compare skill scores: TC (1000 km) > AR (200-400 km) > Precip (10-100 km)
- **Metric**: Correlation between event characteristic scale and ACC/RMSE

**H2: Dynamics Hypothesis**
- **Prediction**: Quasi-geostrophic events more predictable than moist convective
- **Test**: Compare Freeze (baroclinic) vs Precipitation (convective) skill
- **Metric**: ACC for dynamical variables (Z500) vs thermodynamic (precip)

**H3: Initialization Sensitivity Hypothesis**
- **Prediction**: Sensitivity varies by event type (nonlinear dynamics = higher sensitivity)
- **Test**: Compare spread across 00/06/12/18 UTC initialization times
- **Metric**: Ensemble spread (standard deviation across init times)

**H4: Lead Time Degradation Hypothesis**
- **Prediction**: Skill decays exponentially with lead time, rate varies by event type
- **Test**: Fit exponential decay to skill vs lead time curves
- **Metric**: e-folding time scale for each event type

**H5: Physical Realism Hypothesis**
- **Prediction**: Aurora maintains energy/moisture conservation but may dampen extremes
- **Test**: Budget closure analysis, extreme value statistics
- **Metric**: Correlation of budgets, percentile comparison of extremes

**H6: Training Contamination Impact**
- **Prediction**: In-sample events show artificially high skill vs out-of-sample
- **Test**: Compare skill for pre-2020 vs 2020-2023 events of same type
- **Metric**: Skill difference (in-sample minus out-of-sample)

---

## Success Criteria

### Scientific Success
- ✅ Quantify Aurora's predictability for 4 diverse extreme event types
- ✅ Identify practical predictability horizons for operational use
- ✅ Characterize physical consistency and biases
- ✅ Determine when/where/why Aurora succeeds or fails

### Practical Success
- ✅ Provide guidance for operational deployment of AI weather models
- ✅ Identify which extreme events are most suitable for Aurora forecasting
- ✅ Quantify uncertainty and reliability for different lead times

### Strategic Success
- ✅ Establish foundation for perturbation experiments (next paper)
- ✅ Position research at forefront of AI weather for extreme events
- ✅ Generate publishable results within 4-week timeline
- ✅ Create reusable infrastructure for future studies

---

## Risk Mitigation

### Risk 1: Code Infrastructure Development Takes Too Long
- **Mitigation**: Replicate existing TC structure for new event types
- **Fallback**: Focus on TC + Freeze (2 types) in depth rather than 4 types superficially
- **Timeline Buffer**: Build Week 1 entirely for infrastructure

### Risk 2: Aurora Performs Poorly on Some Events
- **Mitigation**: Negative results are publishable findings!
- **Reframe**: "Aurora struggles with localized convective precipitation" = valuable result
- **Scientific Value**: Identifying limitations is as important as successes

### Risk 3: Insufficient Observational Data for Verification
- **Mitigation**: ERA5-only verification is acceptable (standard in ML weather papers)
- **Enhancement**: Use observations where available as supplementary validation
- **Precedent**: Most AI weather papers primarily use reanalysis verification

### Risk 4: Cannot Complete All Event Types in Time
- **Fallback Priority Order**:
  1. TC (already 40% done)
  2. Freeze (large-scale, high impact)
  3. AR (unique challenge, good contrast to TC)
  4. Precipitation (if time permits)
- **Minimum Viable Product**: 2 event types well-analyzed > 4 types rushed

### Risk 5: Figures Take Too Long to Make Publication-Quality
- **Mitigation**: Create templates in Week 1, reuse for all events
- **Strategy**: 80% quality for initial submission, polish in revision
- **Tools**: Use `shared/visualization.py` with consistent styling

### Risk 6: Paper Rejected for Small Sample Size
- **Mitigation**: Frame as "comprehensive process-oriented case study approach"
- **Strength**: Depth of analysis compensates for breadth
- **Precedent**: Many AI weather papers use case studies (cite Aurora TC paper, GraphCast storm paper)
- **Scientific Value**: Process understanding > statistical significance with limited samples

---

## References & Resources

### Key Papers to Cite

**AI Weather Models:**
- Aurora: Bodnar et al. (2024) - Foundation model for atmospheric prediction
- GraphCast: Lam et al. (2023) - Graph neural network weather model
- Pangu-Weather: Bi et al. (2023) - 3D transformer for global forecasting
- FourCastNet: Pathak et al. (2022) - Fourier neural operator

**Extreme Event Prediction:**
- Aurora TC study: Bodnar et al. (2024) - Typhoon Nanmadol case study
- GraphCast storm paper: Recent extreme event analysis
- WeatherBench2: Rasp et al. (2024) - Evaluation framework

**Traditional NWP Baseline:**
- ECMWF IFS: Operational NWP model
- NOAA GFS: Global forecast system
- Track prediction benchmarks: Historical operational skill

**Observational Datasets:**
- IBTrACS: Knapp et al. (2010)
- AR Catalogs: Guan & Waliser (2015), ARTMIP (2019)
- ERA5: Hersbach et al. (2020)
- IMERG: Huffman et al. (2019)

### Useful Links

- Aurora GitHub: https://github.com/microsoft/aurora
- Aurora HuggingFace: https://huggingface.co/microsoft/aurora
- WeatherBench2: https://sites.research.google/gr/weatherbench/
- IBTrACS: https://www.ncei.noaa.gov/products/international-best-track-archive
- ERA5 CDS: https://cds.climate.copernicus.eu/
- AR Catalog: https://catalog.pangeo.io/browse/master/atmosphere/ar_catalog/

---

## Notes & Updates

### Meeting Notes (2025-11-10)

**Key Decisions:**
- Focus on Aurora (not multi-model comparison)
- Include Pangu only if time permits, not required
- 3 cases per extreme type (different climate zones)
- Use billion-dollar disaster database for event selection
- Paper positioning: Aurora evaluation (not WeatherBench2-style benchmark)

**Priority:**
- Out-of-sample validation critical for scientific validity
- Depth over breadth (fewer events, better analysis)
- Foundation for perturbation paper (main strategic goal)

### Current Status (2025-11-11)

**Completed:**
- ✅ TC infrastructure (TC_utils.py, shared utilities)
- ✅ **Hurricane Sandy 2012 COMPLETE** (full two-stage analysis, 20 figures)
  - Stage 1: Lead time assessment (1, 3, 5, 7 days)
  - Stage 2: Initialization sensitivity (00, 06, 12, 18 UTC)
  - Key findings: 21.5 km landfall error (1-day), low init sensitivity (18.9 km std dev)
  - Systematic bias: Underpredicts intensity and wind speed
- ✅ Typhoon Nanmadol 2022 (out-of-sample)
- ✅ Track prediction methodology validated
- ✅ Field comparison methodology (MSL, wind at landfall)

**In Progress:**
- 🔨 Documentation updates (RESEARCH_PLAN.md)

**Next Steps:**
- Complete Hurricane Ian 2022 (out-of-sample, Atlantic)
- Complete Typhoon Hinnamnor 2022 (out-of-sample, Western Pacific)
- Cross-event TC comparison
- Build Freeze/AR/Precip infrastructure

---

## Contact & Collaboration

**Primary Researcher**: [Your Name]
**Advisor**: Manu
**Collaborators**: Yeongbin (perturbation methods), Moyan (cloud seeding physics)
**Institution**: Arizona State University
**Computing**: ASU Sol (CUDA GPU resources)

---

**Document Version**: 1.0
**Created**: 2025-11-10
**Last Modified**: 2025-11-10
**Status**: Active - Week 1 of 4-week sprint

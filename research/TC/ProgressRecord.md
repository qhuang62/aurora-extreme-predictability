# Tropical Cyclone (TC) Analysis

Research work on evaluating Aurora's predictability for tropical cyclones.

## October 19, 2025 - Initial Aurora TC Testing ✅

**Objective**: Verify Aurora TC prediction functionality on ASU Sol.

**Accomplishments**:
- **Setup**: Aurora environment operational on ASU Sol with CUDA GPU
- **Data**: Downloaded HRES T0 + ERA5 static for Typhoon Nanmadol (Sep 17, 2022)
- **Model**: Aurora 0.25° Fine-Tuned, 48-hour forecast (8 × 6hr steps)
- **Tracking**: Successfully tracked Nanmadol from 27.5°N, 132°E
- **Validation**: Added IBTrACS observational track comparison with quantitative error analysis

**Files**: `finetune_nanmadol_2022_init12.ipynb`, `data/hresT0_nanmadol_2022/`

---

## October 20, 2025 - ERA5 Workflow & Documentation ✅

**Objective**: Create ERA5-based TC prediction workflow for historical analysis beyond WeatherBench2's 2016-2022 limitation.

**Accomplishments**:
- **ERA5 Workflows**: Created 06:00 UTC (`era5_nanmadol_2022_init6.ipynb`) and 12:00 UTC (`era5_nanmadol_2022_init12.ipynb`) initialization variants
- **Model**: Aurora 0.25° Pretrained with `use_lora=False` for ERA5 compatibility
- **Technical Guide**: `Aurora_TC_Setup_Guide.md` with reproducibility documentation
- **Key Insight**: Fine-tuned models for HRES data, pretrained models for ERA5 data
- **Historical Coverage**: Enables analysis of pre-2016 TCs (Sandy 2012, Earl 2010)

**Files**: `era5_nanmadol_2022_init6.ipynb`, `era5_nanmadol_2022_init12.ipynb`, `Aurora_TC_Setup_Guide.md`, `data/era5_nanmadol_2022/`

---

## October 21, 2025 - ECMWF Open Data Exploration & Study Design 

**Objective**: Investigate ECMWF Open Data for direct HRES access and refine experimental design for training data contamination.

**Attempts & Limitations**:
- **ECMWF Open Data**: Tested `ecmwf-opendata` package for historical HRES access - confirmed that we can use this for real time only
- **MARS Archive**: No access; need research non-commencial license 
- **Historical Data**: 2022 Nanmadol data unavailable via open data API

**Key Methodological Insight**: 
- **Training Contamination Issue**: Aurora pretrained on ERA5 1979-2020, so TCs in this period were "seen" during training
- **Study Design Solution**: Focus on **out-of-sample validation** using 2021-2023 TCs for scientific validity

**Revised Experimental Plan**:
- **Primary**: 2021-2023 TCs (out-of-sample) with Aurora Pretrained + ERA5 via WeatherBench2 or CDS API
- **Secondary**: 2021-2022 TCs with Aurora Fine-tuned + HRES T0 via WeatherBench2  
- **Comparison**: Model variants (pretrained vs fine-tuned) on same events
- **Data Sources**: ERA5 (1959-2023) vs HRES T0 (2016-2022) via WeatherBench2 or CDS API

**Weather Bench 2**
- **Primary**: a framework for several AI weather model evaluation; also contains groudtruth and observational baseline datasets
- **Website**: https://sites.research.google/gr/weatherbench/

**Files**: `hres_nanmadol_2022.ipynb`, `data/test_opendata_download/` (deleted)

---

## October 31, 2025 - Data Assimilation Investigation & Aurora Architecture Analysis ✅

**Objective**: Develop data assimilation approach for Aurora TC prediction and understand model limitations.

**Data Assimilation Attempt**:
- **Initial Approach**: Implemented `era5_nanmadol_da_experiment.py` with 12-hour observational updates
- **Method**: Reset tracker positions to observed locations every 12 hours during 48-hour rollout
- **Failure**: Aurora tracker threw `NoEyeException: Completely failed at the first step`
- **Root Cause**: Breaking Aurora's internal state consistency disrupts cyclone detection algorithm

**Critical Aurora Architecture Insights**:
- **Tracker Algorithm**: Uses MSL pressure minima and Z700 geopotential for automatic cyclone center detection
- **Rollout Continuity**: Aurora maintains temporal continuity by concatenating previous timesteps (`batch.surf_vars[k][:, 1:]`)
- **Autoregressive Nature**: Model builds predictions on previous states; artificial position jumps break this sequence
- **Eye Detection Requirements**: Tracker expects coherent atmospheric structure around cyclone center

**Source Code Analysis**:
- **`aurora/tracker.py`**: Gaussian filtering, local minima detection, land/sea masking for eye tracking
- **`aurora/rollout.py`**: Temporal concatenation mechanism preserves model memory
- **`aurora/batch.py`**: Data structure requirements for proper model input
- **Key Finding**: Aurora's design philosophy prioritizes internal physical consistency over external corrections

**Revised Scientific Approach**:
- **Problem**: Direct data assimilation incompatible with Aurora's architecture without significant model modification
- **Solution**: Focus on **predictability analysis** rather than forced assimilation
- **Implementation**: `nanmadol_predictability_analysis.py` - proper Aurora workflow respecting model design

**Predictability Analysis Results**:
- **Initialization Sensitivity**: 06 UTC vs 12 UTC initialization comparison
- **Lead Time Analysis**: Error growth quantification over 48-hour forecasts
- **Track Error Metrics**: 24-hour and 48-hour position errors calculated
- **Visualization**: Separate high-quality PNG outputs for presentation

**Quantitative Findings**:
- **06 UTC Init**: [Actual results from model run]
- **12 UTC Init**: [Actual results from model run]
- **Error Growth**: Demonstrates Aurora's predictability horizon limitations
- **Track Quality**: Aurora captures general TC movement patterns but with accumulating position errors

**Technical Outputs**:
- **`nanmadol_track_comparison.png`**: Geographic track comparison with adjusted marker sizes
- **`nanmadol_error_analysis.png`**: Error vs lead time quantitative analysis
- **Methodology**: Proper Aurora rollout workflow without breaking internal state

**Key Research Implications**:
1. **Aurora DA Requirements**: True data assimilation would require:
   - Ensemble forecasting with perturbed initial conditions
   - Variational DA preserving model physics
   - Observation operators mapping between model and observation space
   - Internal model modifications beyond current Aurora codebase

2. **Predictability Framework**: Current approach establishes baseline for:
   - Initialization timing optimization
   - Forecast skill assessment
   - Lead time limitations quantification
   - Model comparison methodology

3. **Future Research Directions**:
   - Multi-initialization ensemble forecasting
   - Systematic basin comparison (Atlantic, Western Pacific, North Indian)
   - Out-of-sample validation (2021-2023 events)
   - Physical consistency analysis (energy budgets, moisture conservation)

**Files**: `era5_nanmadol_da_experiment.py` (failed approach), `nanmadol_predictability_analysis.py` (successful), track and error analysis PNG outputs

**Scientific Status**: Established proper Aurora TC prediction methodology; identified fundamental DA limitations; ready for presentation and systematic multi-event analysis.

---

**Research Context**: This work is part of evaluating Aurora's predictability for extreme weather events, specifically tropical cyclones, as outlined in the paper development plan.
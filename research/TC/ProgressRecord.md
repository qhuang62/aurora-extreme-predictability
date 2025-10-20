# Tropical Cyclone (TC) Analysis

This folder contains research work on evaluating Aurora's predictability for tropical cyclones.

## Today's Work - October 19, 2025

### Successfully Tested Aurora TC Tracking on ASU Sol Supercomputer

**Objective**: Verify Aurora model functionality for tropical cyclone prediction on local infrastructure.

**What We Accomplished**:

1. **Setup Aurora Environment**
   - Successfully imported Aurora from upstream-aurora path structure
   - Verified all dependencies working on ASU Sol's Jupyter notebook session
   - Confirmed CUDA GPU access for model inference

2. **Data Download and Processing**
   - **HRES T0 Data**: Downloaded from WeatherBench2 for September 17, 2022
     - Surface variables: 10m wind components (u,v), 2m temperature, mean sea level pressure
     - Atmospheric variables: temperature, wind components (u,v), specific humidity, geopotential
     - Temporal coverage: Full day with 6-hour intervals
   - **ERA5 Static Variables**: Downloaded from Copernicus CDS
     - Geopotential, land-sea mask, soil type
   - **Data Storage**: Saved locally in `research/TC/data/nanmadol_2022/`

3. **Model Execution**
   - **Model**: Aurora 0.25° Fine-Tuned (`aurora-0.25-finetuned.ckpt`)
   - **Checkpoint**: Successfully loaded from Microsoft HuggingFace repository
   - **Initial Conditions**: September 17, 2022, 12:00 UTC
   - **Forecast Period**: 8 steps × 6 hours = 48 hours of predictions
   - **Hardware**: Ran locally on CUDA GPU

4. **Tropical Cyclone Tracking**
   - **Target**: Typhoon Nanmadol (2022)
   - **Initial Position**: 27.5°N, 132°E (from IBTrACS database)
   - **Tracking Algorithm**: Aurora's built-in tropical cyclone tracker
   - **Results**: Successfully predicted typhoon track over 48-hour period

5. **Output and Visualization**
   - Generated 8 time-step predictions showing typhoon movement
   - Visualized track overlaid on mean sea level pressure fields
   - Demonstrated northeastward movement pattern consistent with expected behavior
   - Track data saved for future analysis

6. **Track Comparison with Observations** 
   - **Observational Data**: Added IBTrACS data for Typhoon Nanmadol (Sep 16-19, 2022)
   - **Comparison Period**: 48-hour forecast from Sep 17 12:00 to Sep 19 12:00 UTC
   - **Visualization**: Created clean track comparison plot with:
     - Black solid line for observed track
     - Blue dashed line for Aurora predictions
     - Map showing Japanese coastline and major cities (Tokyo, Osaka, Nagoya, Kagoshima)
     - Gold triangle marking initialization point
   - **Quantitative Analysis**: Added final position error calculation
   - **Result**: Aurora successfully predicted general typhoon movement direction

**Key Technical Notes**:
- Used original Aurora example code from their GitHub repository
- Successfully adapted for research folder structure 
- All imports and data paths properly configured
- Model ran efficiently on ASU Sol infrastructure

**Status**: ✅ **SUCCESSFUL** - Aurora model is fully operational for TC research

**Limitations**:
- No comparison with observational track data yet
- No quantitative accuracy metrics calculated
- Single case study only

**Next Steps**:
1. Download IBTrACS observational data for Typhoon Nanmadol
2. Calculate track error metrics (distance, timing, landfall accuracy)
3. Test additional tropical cyclone cases (Hurricane Sandy 2012, Earl 2010)
4. Implement systematic evaluation framework

**Files Generated**:
- `nanmadol_2022.ipynb` - Jupyter notebook with full analysis
- `data/nanmadol_2022/` - Downloaded HRES T0 and ERA5 data
- Track predictions (in memory, ready for export)

---

**Research Context**: This work is part of evaluating Aurora's predictability for extreme weather events, specifically tropical cyclones, as outlined in the paper development plan.
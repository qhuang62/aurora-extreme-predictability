# **Evaluating the Predictability of Weather Extremes with Aurora: Insights from Tropical Cyclones, Freezes, and Atmospheric Rivers**

# 1\. Introduction

1. ## Challenge \- extreme events are hardest to predict yet most critical

2. ## Why predict extreme weather 

   1. Hurricanes, freezes, atmospheric rivers (ARs), and heavy precipitation events are increasing in impact as exposure and vulnerability grow globally  
   2. Accurate and timely forecasts are essential for preparedness, adaptation, and mitigation

3. ## Current prediction methods & their limitations

   1. NWP (Numerical Weather Prediction) \- traditional models such as ECMWF, GFS, and WRF simulate the atmosphere using DA (data assimilation) and physical equations  
   2. Pros (physically interpretable) & Cons (reduced predictability at longer lead times; high computational costs, difficulty capturing localized extremes?)

4. ## Aurora as an emerging ai forecasting approach \- can it address some of these gaps?

   1. Aurora is a foundation model for global weather prediction trained directly on ERA5 reanalysis data   
   2. Without explicit physics equations, learning spatiotemporal relationships directly from data  
   3. Faster inference and higher spatial resolution; early studies show comparable/superior prediction skills on xx xx xx  
   4. So this raises the key question: *Can Aurora enhance predictability for extreme events, especially those with nonlinear dynamics or multi-scale coupling?*

5. ## Objectives of this paper

   1. Evaluate how well Aurora predicts specific classes of extreme events \- hurricanes, freezes, ARs, and precipitation extremes \- why these 4 event types? (they span different spatiotemporal scales, mechanisms, predictability regimes)  
   2. Compare forecast performance, lead-time skill, and physical consistency  
   3. Identify event-dependent predictability and Aurora’s potential/limitations for future early warning systems

# 2\. Methods & Data

1. ## Aurora setup

   1. Input variables, initialization dates, lead times tested, model resolution and forecast outputs

2. ## Verification datasets 

   1. ERA5 reanalysis \+ observational datasets (TC and AR catalog) 

3. ## Performance metrics

   1. RMSE, ACC?  
   2. …etc

4. ## Case study design

   1. Objective event definition \- how do we objectively identify each extreme? (e.g., TC tracking algorithm, AR detection method like Guan/Waliser, freeze thresholds, precipitation percentiles  
   2. Representative events selected for each category

# 3\. Case Studies 

1. TC (Sandy 2012, Earl 2010, etc)  
   1. Mechanism: warm SSTs, moist convection, Coriolis force, latent heat feedback  
   2. Lead time, sensitivity to initialization (no intensity or rainfall location right?)  
   3. Compare to observed track  
   4. Updated tracking algorithm  
   5. Metrics: track error (km), landfall timing, position uncertainty  
2. Freeze/cold snaps (2021 Texas Freeze)  
   1. Mechanism: arctic air mass intrusion due to high-latitude blocking and jet stream meandering  
   2. Prediction of cold surge, jet stream pattern, and surface temperature anomalies  
   3. How far in advance Aurora captured the cold pool and blocking high  
   4. Metrics: temperature anomaly RMSE, onset timing, spatial extent

3. ## AR (Winter 2022 West Coast)

   1. Mechanism: ARs as traveling waves themselves \- long narrow corridors of water vapor transport \- tropical moisture export  
   2. AR detection, IVT prediction, precipitation impacts  
   3. Metrics: IVT RMSE, AR position/timing, precipitation skill scores

4. ## Precipitation

   1. Event list:   
      - [ ] Sudan floods \- Oct 9, 2025 & Aug 1, 2020  
      - [ ] Pakistan/India \- Jun 27-28, 2025; Aug 27, 2022; Aug 1, 2010  
      - [ ] Northeastern US (Ida) \- Sep 1-2, 2021  
      - [ ] Western Kentucky \- Jul 18-19, 2023  
      - [ ] Texas \- Jul 4-7, 2025  
      - [ ] Houzihe Grand Bridge, China \- Jun 24, 2025  
      - [ ] Western Europe \- Jul 12-15, 2021  
      - [ ] Spain \- Oct 29, 2024

# 4\. Results & Discussions

1. Comparative predictability across event types \- which events does Aurora predict best/worst and why (spatial scale, dynamics, initialization sensitivity)?  
2. Lead time vs. accuracy tradeoffs (how does skill degrade with forecast horizon?)  
3. Physical consistency (energy budgets, moisture conservation; does aurora maintain realistic dynamics?)  
4. Aurora vs. traditional NWP (find existing studies and compare \- literature based)  
5. Our limitations (small sample size, era5 data, single model eval…etc)  
6. Implications and future works
# Starting a New TC Case Study - Required Reading

This guide lists all files/scripts that Claude Code should read when starting a new tropical cyclone case study in a fresh session.

## Purpose

When opening a new Claude Code session to analyze a different TC event, read these files in order to understand:
1. Project context and Aurora model details
2. Research methodology and experimental design
3. Completed example (Sandy 2012) as reference
4. Existing utilities and scripts to adapt

---

## Essential Context Files (Read First)

### 1. Project Overview
**File**: `/scratch/qhuang62/aurora-extreme-predictability/CLAUDE.md`
- Project structure and organization
- Aurora model versions and capabilities
- Required input variables and data format
- General development notes

### 2. Master Research Plan
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/RESEARCH_PLAN.md`
- Overall paper objectives and methodology
- TC case study selection criteria
- Two-stage experimental design:
  - Stage 1: Lead time assessment (1, 3, 5, 7 days)
  - Stage 2: Initialization sensitivity (00, 06, 12, 18 UTC)
- Evaluation metrics and success criteria
- Timeline and priorities

### 3. Completed Example - Sandy 2012 Results
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/SANDY_RESULTS.md`
- Complete Stage 1 and Stage 2 results
- Key findings and systematic biases
- All visualizations produced (20 figures)
- Field comparison methodology
- Summary statistics format
- Implications for paper

### 4. Detailed Workflow Documentation
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/SANDY_DATA_WORKFLOW.md`
- Step-by-step data download process
- ERA5 data requirements and CDS API usage
- Combined vs separate file strategy
- IBTrACS observational data handling
- Script execution order
- Verification data requirements

---

## Template Scripts to Adapt

### 5. Stage 1 Script Template
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/sandy_stage1_lead_day.py`
**Purpose**: Lead time assessment (1, 3, 5, 7 day forecasts)

**Key sections to adapt**:
- `CONFIG` dictionary:
  - `event_name`: New TC name
  - `init_date`: When to start forecasts
  - `landfall_date`: Target landfall time
  - `init_time_idx`: Index in combined ERA5 file
  - `init_lat`, `init_lon`: Initial TC position from IBTrACS
  - `lead_days`: [1, 3, 5, 7] (can adjust based on event)

- Data paths and file names
- Observational track time range
- Regional extents for visualization

**Outputs**:
- Track comparison plots (4 lead times)
- Error analysis plot
- Landfall field comparisons (MSL, wind) for each lead time
- Summary statistics JSON

### 6. Stage 2 Script Template
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/sandy_stage2_init_time.py`
**Purpose**: Initialization time sensitivity (00, 06, 12, 18 UTC inits)

**Key sections to adapt**:
- `CONFIG` dictionary:
  - `lead_days`: Usually 3 days (based on Stage 1 results)
  - `init_date`: Initialization date for all times
  - `landfall_date`: Target landfall time
  - `init_times`: List of dicts with hour, time_idx, lat, lon, steps
    - Each init time has different position and forecast steps
    - All reach same landfall target

- Separate ERA5 file for landfall verification
- Historical track segment for context
- Regional extents

**Outputs**:
- Combined track comparison plot (all 4 init times)
- Individual error analysis plots (4 init times)
- Landfall field comparisons (8 plots: 4 MSL + 4 wind)
- Summary statistics with initialization sensitivity

---

## Shared Utilities (Reference)

### 7. TC Analysis Utilities
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/TC_utils.py`

**Key functions**:
- `load_ibtracs_data()`: Load observational TC track
- `track_cyclone()`: Track TC center in forecast fields
- `compare_fields_at_landfall()`: Extract and compare MSL/wind fields
- Regional extraction and field analysis

### 8. Visualization Utilities
**File**: `/scratch/qhuang62/aurora-extreme-predictability/research/shared/visualization.py`

**Key functions**:
- `plot_track_comparison()`: Track plots with basemap
- `plot_forecast_errors()`: Error evolution over time
- `plot_field_comparison()`: Side-by-side field plots with difference
- `plot_multi_init_field_comparison()`: Combined multi-init visualization
- Date formatting and styling utilities

---

## Workflow for New TC Case

After reading all files above, follow these steps:

### 1. Create New Event Folder
```bash
mkdir -p /scratch/qhuang62/aurora-extreme-predictability/research/TC/YYYY_EventName/
cd /scratch/qhuang62/aurora-extreme-predictability/research/TC/YYYY_EventName/
```

### 2. Gather Event Information
Before creating scripts, collect:
- Event name and year
- Landfall date and location
- IBTrACS ID or coordinates
- Approximate initialization dates (1-7 days before landfall)
- Basin and region for visualization extents

### 3. Create New Scripts
Copy and adapt templates:
- `eventname_stage1_lead_day.py` (from `sandy_stage1_lead_day.py`)
- `eventname_stage2_init_time.py` (from `sandy_stage2_init_time.py`)

Update:
- All dates and coordinates
- File paths and event names
- Regional extents for mapping
- Observational track time ranges

### 4. Create Documentation
- `EVENTNAME_DATA_WORKFLOW.md`: Data download steps, file structure
- `EVENTNAME_RESULTS.md`: Results after analysis (create after running)

### 5. Download ERA5 Data
Follow workflow from `SANDY_DATA_WORKFLOW.md`:
- Combined file: initialization date to day before landfall
- Separate file: landfall date (for verification)
- Surface-level variables: 2t, 10u, 10v, msl
- Atmospheric variables: t, u, v, q, z at 13 pressure levels
- Time resolution: 6-hourly (00, 06, 12, 18 UTC)

### 6. Run Analysis
Execute in order:
1. Stage 1: Lead time assessment
2. Review Stage 1 results, select best lead time
3. Stage 2: Initialization sensitivity with selected lead time
4. Document results in `EVENTNAME_RESULTS.md`

### 7. Update Master Plan
Update `/scratch/qhuang62/aurora-extreme-predictability/research/RESEARCH_PLAN.md`:
- Mark new event as complete
- Add key findings
- Update current status and next priorities

---

## Important Notes

### Data Requirements
- **ERA5 resolution**: 0.25° (matches Aurora pretrained model)
- **Time range**: At least 7 days before landfall for full Stage 1
- **Verification data**: Must use actual landfall time data (not interpolated)
- **File format**: NetCDF with standard ERA5 variable names

### Model Configuration
- Use `AuroraPretrained` model (not fine-tuned versions)
- Load static variables: lsm, slt, z (from `static` folder)
- 6-hour forecast steps (Aurora's native resolution)
- CUDA acceleration if available

### Consistency Across Cases
- Same two-stage experimental design
- Same metrics: track error, MSL bias, wind bias, position error
- Same visualization style and output format
- Same statistical summary format

### Common Adaptations Needed
- **Basins**: Atlantic vs Pacific (affects longitude convention)
- **Extents**: Adjust map bounds based on TC track
- **Lead times**: Some events may need shorter/longer forecasts
- **Initialization**: Coordinate precision from IBTrACS (actual observations, not interpolated)

---

## Quick Reference Checklist

When starting a new TC case, ensure you have:

- [ ] Read all 8 files listed above
- [ ] Created new event folder
- [ ] Collected event dates and coordinates from IBTrACS
- [ ] Downloaded ERA5 data (combined + landfall verification)
- [ ] Adapted Stage 1 script with correct CONFIG
- [ ] Adapted Stage 2 script with correct CONFIG
- [ ] Created DATA_WORKFLOW.md documentation
- [ ] Verified regional extents for visualization
- [ ] Confirmed observational track time range
- [ ] Ready to execute Stage 1 analysis

---

## Questions to Address Before Starting

1. **What is the exact landfall date and time (UTC)?**
   - This determines target for all forecasts

2. **What are the IBTrACS coordinates at potential initialization times?**
   - Need actual 6-hourly positions (not interpolated)
   - For Stage 1: 1, 3, 5, 7 days before landfall
   - For Stage 2: 3 days before landfall at 00, 06, 12, 18 UTC

3. **What is the appropriate regional extent for visualization?**
   - Should encompass entire track from initialization to landfall
   - Typical: 20-30° latitude range, 20-40° longitude range

4. **What is the basin and expected track behavior?**
   - Atlantic: Typically NW to N/NE tracks
   - Western Pacific: More variable, often recurving
   - Affects interpretation and comparison with other cases

5. **Are there any unique characteristics of this event?**
   - Rapid intensification? Long-lived? Unusual track?
   - Note for interpretation and paper discussion

---

## Summary

This document provides the complete reading list and workflow for analyzing a new tropical cyclone case with Aurora. By following this guide, you can maintain consistency with the Sandy 2012 analysis while adapting to each event's unique characteristics.

**Key principle**: Read the context files first to understand the methodology, then adapt the template scripts to the new event's specific dates, coordinates, and characteristics.

# Beast from East 2018 - Quick Reference

## ⚠️ PRESSURE LEVEL BUG FIXED (Nov 20, 2024)

**Issue**: Aurora pressure levels in reverse order caused wrong extraction:
- T850: Was index 10 (150 hPa ❌) → Fixed to index 2 (850 hPa ✓)
- Z500: Was index 6 (400 hPa ❌) → Fixed to index 5 (500 hPa ✓)

**Action**: Old predictions deleted, all data regenerated with correct indices.

**Aurora levels**: (1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50 hPa)

---

## ✅ BEST PREDICTION: **7-DAY LEAD**

**Why?**
- Pattern correlation: 0.867 (excellent)
- Captures 66% of freeze extent
- Operationally relevant lead time
- Avoids 14-day climatology convergence

## ⭐ TOP 9 PLOTS FOR PRESENTATION

### Slide 1: Lead Time Comparison (4 plots)
```
beast_1day_peak_t2m.png
beast_7day_peak_t2m.png
beast_14day_peak_t2m.png
beast_21day_peak_t2m.png
```

### Slide 2: Physical Mechanisms @ 7-day (3 plots)
```
beast_7day_peak_t2m.png    - Cold air mass
beast_7day_peak_t850.png   - Mid-level cold advection
beast_7day_peak_z500.png   - Blocking pattern
```

### Slide 3: Event Evolution @ 1-day (3 plots)
```
beast_1day_onset_t2m.png
beast_1day_peak_t2m.png
beast_1day_recovery_t2m.png
```

## 📊 Key Numbers

| Metric | 1-day | 7-day | 14-day | 21-day |
|--------|-------|-------|--------|--------|
| RMSE (°C) | 7.03 | 7.40 | 2.78* | 4.01 |
| Pattern Corr | 0.911 | **0.867** | 0.820 | 0.677 |
| Freeze Extent | 68% | **66%** | 10%* | 22% |

*14-day has suspiciously low RMSE but severely underpredicts extent

## ➡️ NEXT: Stage 2 with 7-day lead

Update `beast_stage2_physical_mechanisms.py` to analyze:
1. Blocking patterns (Z500)
2. Cold air mass (T850)
3. Jet stream dynamics
4. Physical mechanism errors

## 🔧 Quick Commands

```bash
# Regenerate all visualizations
export LD_LIBRARY_PATH=/packages/apps/jupyter/2025-03-24/lib:$LD_LIBRARY_PATH
python regenerate_visualizations.py

# View metrics
cat prediction_output/beast_stage1_metrics.csv | column -t -s,
```

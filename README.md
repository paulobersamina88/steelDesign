# AISC Steel Checker ULTRA Phase 2 — DB Ready

This upgrade lets the Streamlit app read:
1. the AISC Shapes Database Excel file directly, or
2. a normalized office CSV

## What it adds
- auto-detects AISC database files
- reads the Database v15.0 worksheet
- maps section labels and type families
- converts imperial properties to metric internally
- uses the loaded section library for the checker and batch mode

## Accepted uploads
- AISC v15.0 Excel file
- CSV exported from AISC database
- normalized office CSV with columns like:
  shape, family, A_mm2, d_mm, bf_mm, tw_mm, tf_mm, Zx_mm3, Zy_mm3, Sx_mm3, Sy_mm3, rx_mm, ry_mm

## Important
This is still a preliminary office checker, not a full final-design engine.

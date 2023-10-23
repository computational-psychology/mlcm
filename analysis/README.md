# Scaling analysis

PYTHON
1. Merge participant data
2. Plot heatmaps from raw data
2. Reindex for MLCM

R (CSV in -> CSV out)
- CSV in: absolute path, agnostic to folderstructures/file locations
3. Fit additive model
4. Fit full model
5. Compare model fits -> is full significantly better than additive?
6. GOF for single model (full if necessary, otherwise additive)
    - iteratively remove residuals
7. Bootstrap samples for additive
    -> export to CSV
    - raw and normalized
8. Bootstrap samples for full
    -> export to CSV
    - raw and normalized
9. CI calculation
    - for each
10. Save model outputs
    - export scales, CIs to CSV, normalized and raw
    - and "log" for model comparison etc.

PYTHON
- load from CSVs
- plotting of scales w/ CIs, contexts, etc.
- predict matches (from scales, and from bootstrap samples)
    -> takes a long time, CSV in -> CSV out
    - plot matching predictions, separately afterwards
- fit Whittle contrast model
- ...

## Simulation
...
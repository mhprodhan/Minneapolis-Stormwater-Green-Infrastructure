# Model design notes and QA checklist

## What was verified

The three uploaded SWMM 5.2.4 input files were compared line by line.

| Comparison | Finding |
|---|---|
| Baseline vs. S1-only | Only addition of rain-garden control definition and one S1 LID deployment |
| S1-only vs. All-six | Exactly five additional LID deployment rows (S2 through S6) |
| Catchments, subareas, infiltration, nodes, pipes, x-sections, rainfall and run dates | Identical in all three files |
| Baseline rain garden assignment | None |
| S1-only rain garden assignment | 10 units in S1 |
| All-six rain garden assignment | 10 units in each of S1–S6 |

All scenario outcomes below are from SWMM 5.2.4 simulation summaries supplied by the project author; the engine was not rerun for this GitHub package.

## LID footprint audit

All-six uses `RG_01` with 10 units per subcatchment; 50% of impervious runoff is routed to each subcatchment's set of units. A unit's surface width is 0, initial saturation is 0%, and pervious-area runoff treated is 0%.

| Subcatchment | SWMM area (acres) | Unit area (ft²) | Total LID area (ft²) | Approximate area fraction |
|---|---:|---:|---:|---:|
| S1 | 8.956 | 1,950.6 | 19,506 | 5.0% |
| S2 | 14.879 | 3,240.6 | 32,406 | 5.0% |
| S3 | 19.773 | 4,306.6 | 43,066 | 5.0% |
| S4 | 12.639 | 2,752.8 | 27,528 | 5.0% |
| S5 | 11.760 | 2,561.3 | 25,613 | 5.0% |
| S6 | 14.600 | 3,179.9 | 31,799 | 5.0% |
| **Total** | **82.607** | — | **179,918** | **5.0%** |

The 60 units represent distributed *equivalent* rain-garden area, not an implemented site plan. Feasibility depends on site constraints, utilities, soil conductivity, groundwater, pollution risk, and proximity to buildings.

## Rainfall and continuity checks

The storm file has 96 incremental 15-minute volumes over 24 hours, totaling exactly 4.20 inches. SWMM reported 28.912 acre-ft of rainfall in all three runs, consistent with a modeled area of 82.607 acres.

| Quantity | Baseline | S1-only | All-six |
|---|---:|---:|---:|
| Initial LID storage (acre-ft) | 0.000 | 0.090 | 0.826 |
| Infiltration loss (acre-ft) | 8.626 | 9.108 | 12.884 |
| Surface runoff (acre-ft) | 20.111 | 19.369 | 13.507 |
| Final surface/LID storage (acre-ft) | 0.182 | 0.533 | 3.363 |
| Surface-runoff continuity error (%) | -0.024 | -0.028 | -0.054 |
| Flow-routing continuity error (%) | -0.001 | -0.001 | -0.001 |

There was no reported flooding loss; all links were reported stable, with flow-routing convergence at all time steps. **Initial LID storage is not an error:** `0%` initial saturation refers to the soil's water content relative to wilting point, not zero absolute soil water content.

The reduction in runoff comprises both additional infiltration and net retained surface/LID storage during this finite 30-hour run. Long-term fate of stored water has not been tested.

## Conveyance assumptions

| Link | Upstream | Downstream | Length (ft) | Diameter (ft) | Manning n |
|---|---|---|---:|---:|---:|
| C1 | J1 | J2 | 702.8 | 3 | 0.013 |
| C2 | J2 | J3 | 644.1 | 4 | 0.013 |
| C3 | J3 | O1 | 270.1 | 5 | 0.013 |

Assumed invert elevations are J1 732.91 ft, J2 731.73 ft, J3 727.79 ft and O1 712.34 ft. They were derived by assuming a uniform 3-meter burial depth beneath preliminary DEM ground elevations. These are **not surveyed sewer elevations**.

Consequently, the C3 slope is `(727.79 - 712.34) / 270.1 = 5.72%`. Its peak computed velocities (18.16 ft/s in baseline; 16.14 ft/s in all-six) warrant scour, abrasion and energy-dissipation review. Pipe diameters were hypothetical; `FREE` outfall neglects Mississippi River tailwater.

The manually assigned subcatchment widths are rough square-equivalent approximations of `sqrt(area)` in feet and should be replaced with representative overland-flow widths when high-quality drainage delineation becomes available.

## Reproducibility notes

- SWMM `.inp` files are placed in the repository root, because their rainfall references use the Windows relative path `Data\Minneapolis_NOAA14_10yr24h_Q1_50pct_15min.dat`.
- A visual map backdrop referenced as `Minneapolis_backdrop.png` was unavailable and is not included. Its absence does not change the routing model.
- The 4.20-inch, 10-year 24-hour depth and NOAA temporal curve were supplied during the tutorial. Confirm NOAA temporal region assignment for this site before formal design use.
- The included comparisons should be described as **modeled scenario responses** rather than field measurements or verified reductions.
- A later extension should compare event/antecedent conditions, river stage, soil tests, spatial rain-garden placement and municipal design criteria.

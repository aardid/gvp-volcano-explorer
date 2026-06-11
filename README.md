# gvp-volcano-explorer

Data, figures, and an interactive web app supporting **Kennedy et al.,
"Inconsistent perceptions of terminology: Erupting, Active, Dormant, and Extinct
volcanoes."**

Everything is rebuilt live from the Smithsonian **Global Volcanism Program —
Volcanoes of the World** WFS service, so the catalogue, figures, and app stay
fully reproducible and never disagree with one another. Reference year **2026**;
tier thresholds follow the manuscript's draft Table 2.

> **Private repo.** Contains the unpublished manuscript draft and internal
> review/analysis documents — do not make public without the authors' agreement.

## Data pipeline
- **`build_catalogue.py`** → downloads GVP layers to CSV (+ raw GeoJSON in `raw/`):
  Holocene volcanoes (1,215), Holocene eruptions (11,089; 9,918 confirmed),
  Pleistocene volcanoes (1,451), and LandScan population exposure.

## Figures
- **`build_lasteruption_figure.py`** → time-since-last-eruption figure (4 panels)
  + world repose map; writes `last_eruption_per_volcano.csv`.
- **`build_exposure_figures.py`** → population-exposure figures (`exposure_figs/`).
- **`build_ben_requests.py`** → review-requested analyses (`ben_figs/`):
  cut-off sensitivity (500-yr vs 100-yr split + "active but undated" column),
  repose vs mean recurrence interval, and repose-by-volcano-type box plots
  with Kruskal–Wallis / Spearman statistics.

## Interactive app (`webapp/`)
A self-contained browser tool (just open `webapp/index.html`) with three lenses:
**terminology & tiers** (draggable thresholds), **population exposure**, and an
**eruption timeline** (scrub/play the reference year to rebuild the active-volcano
picture through history). Rebuild its embedded data with
`python webapp/build_webdata.py`. See `webapp/README.md` for details.

## Environment
Windows / PowerShell, Python via Anaconda (`pandas`, `numpy`, `matplotlib`,
`geopandas`, `scipy`). Basemap = Natural Earth 110m (auto-cached in `raw/`).
See `CLAUDE.md` for conventions and data gotchas.

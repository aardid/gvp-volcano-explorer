# BK_paper_2026 — volcano terminology paper

Figures and data work supporting **Kennedy et al., "Inconsistent perceptions of
terminology: Erupting, Active, Dormant, and Extinct volcanoes."** This folder
holds the manuscript drafts plus a self-built GVP catalogue and the figure
scripts that consume it. We (contributing on the stats/figures side, with
Alberto Ardid) are addressing **Action item 4**: a graph of the world's active
volcanoes vs. time since last eruption, from the Smithsonian database.

## Manuscript / context docs (read-only references)
- `active volcano Inconsistent perceptions of terminology may 2026_DC.docx` — current manuscript draft.
- `volcano_project_report.docx`, `eruption_rate_report_FULL.docx`, `eruption_rate_meeting_brief.docx` — Alberto's review + eruption-rate analysis (the "constant-rate is the exception" work; 9,918 confirmed eruptions matches our pull).
- The paper's **draft Table 2** defines the tier thresholds used throughout the figures: erupting = **92 days** (~0.25 yr), high = **500 yr**, moderate = **12 kyr** (Holocene), dormant = Pleistocene (to **2.5 Myr**), extinct = >2.5 Myr.

## Data pipeline
Everything is rebuilt live from the **Smithsonian GVP Volcanoes of the World**
WFS service — no manual downloads, fully reproducible.

- `build_catalogue.py` → downloads layers to CSV (+ raw GeoJSON in `raw/`, provenance in `CATALOGUE_README.md`):
  - `gvp_holocene_volcanoes.csv` (1,215; has `Last_Eruption_Year`, `Primary_Volcano_Type`, lat/lon)
  - `gvp_holocene_eruptions.csv` (11,089; 9,918 confirmed; `StartDateYear` signed, negative = BCE)
  - `gvp_pleistocene_volcanoes.csv` (1,451; epoch-only, **no per-volcano ages**)
  - `gvp_population_exposure.csv` (from `E3WebApp_HoloceneVolcanoes`; `Within_5/10/30/100km` LandScan population, keyed by `VolcanoNumber`)
- WFS endpoint: `https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows`
- **Gotcha:** this GeoServer rejects `startIndex` paging (HTTP 400). Fetch all features in one request with a large `count` instead.

## Figure scripts
- `build_lasteruption_figure.py` → two figures + `last_eruption_per_volcano.csv`:
  - `fig_time_since_last_eruption.png/.svg` — 4 panels (a: distribution+thresholds, b: by volcano type, c: recording bias post-1500 CE, d: full population mapped to Table 2 tiers).
  - `fig_volcano_map.png/.svg` — world map coloured by repose time + 6 zoom panels (Aleutians, Kamchatka–Japan, Indonesia, Central America, Andes, East Africa Rift).
- `build_exposure_figures.py` → `exposure_figs/` (population-exposure alternatives):
  - `fig_exposure_vs_repose` (scatter: repose vs. pop within 30 km, long-repose/high-exposure outliers numbered — Tatun, Chichinautzin, Campi Flegrei…)
  - `fig_exposure_by_tier` (bar: total pop within 30 km per active tier; ~270M total)
  - `fig_exposure_map` (map, marker size = population, colour = repose)

## Conventions / facts to keep consistent
- **Reference year = 2026** (`REF_YEAR`); `years_since = 2026 - Last_Eruption_Year`.
- 1,215 Holocene volcanoes: **849 dated, 366 (30%) undated** (no last-eruption year → "active but untimed"; relevant to the poorly-studied-volcanoes point).
- Volcano types need normalising (singular/plural variants, e.g. `Stratovolcano` vs `Stratovolcano(es)`) — see `type_group()`, reused across scripts. Median repose by type: monogenetic ~1,070 yr, stratovolcano ~82 yr.
- Basemap = Natural Earth 110m, cached at `raw/ne_110m_admin_0_countries.geojson` (auto-downloads if missing).
- Map panels: use `aspect="equal"` with `adjustable="datalim"` for aligned zoom grids; the top overview needs a tall enough row to fill full width, colorbar as an inset so it doesn't steal width.

## Environment
- Windows, PowerShell (5.1). Python via Anaconda (`pandas`, `numpy`, `matplotlib`, `geopandas` available; **no cartopy** — use geopandas + Natural Earth).
- Not a git repo.
- DOCX has no plain-text export here; extract via PowerShell `System.IO.Compression` reading `word/document.xml`.

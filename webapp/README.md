# GVP Volcano Explorer (web app)

Interactive map companion to the terminology paper. Built from the local GVP
catalogue — same tier thresholds, `type_group()` and `REF_YEAR = 2026` as the
figure scripts, so the app and the paper figures never disagree.

## Run
Just **double-click `index.html`** (data is embedded as JS, so no local server
is needed). The Leaflet library and basemap tiles load from the web, so an
internet connection is required for the map background.

## Rebuild data
After re-running `../build_catalogue.py`, regenerate the embedded data:

```
python build_webdata.py
```

This writes `data/data_core.js` (volcanoes + per-volcano eruption history +
population) and `data/data_details.js` (summaries + photos).

## The three tabs
- **Terminology & tiers** — colour by draft Table 2 tier; drag the
  erupting / high / moderate thresholds and watch the active/dormant counts flip.
- **Population exposure** — marker area ∝ people within 5–100 km; sidebar lists
  the long-repose, high-exposure volcanoes (Tatun, Chichinautzin, Campi Flegrei…).
- **Eruption timeline** — scrub or **play** the reference year to rebuild the
  active-volcano picture through history (last eruption is recomputed from each
  volcano's confirmed eruption record up to that year).

The reference-year slider is shared across all map tabs, the live histogram /
exposure / timeline chart sits bottom-left, and tier counts update top-right.

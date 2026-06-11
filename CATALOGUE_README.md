# GVP catalogue — provenance

Downloaded: 2026-06-10 23:04 UTC
Source: Smithsonian Global Volcanism Program (GVP), Volcanoes of the World (VOTW).
Endpoint: https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows (WFS 2.0, GeoServer).

## Files
- `gvp_holocene_volcanoes.csv` — 1215 records (raw GeoJSON in `raw/`).
- `gvp_holocene_eruptions.csv` — 11089 records (raw GeoJSON in `raw/`).
- `gvp_pleistocene_volcanoes.csv` — 1451 records (raw GeoJSON in `raw/`).
- `gvp_population_exposure.csv` — 1215 records (raw GeoJSON in `raw/`).

## Citation
Global Volcanism Program (current version), Volcanoes of the World database,
Smithsonian Institution. https://volcano.si.edu  (compiled by E. Venzke).
Andrews, B.J. et al. (2025). The Volcanoes of the World database. Bull. Volcanol. 87, 34.

## Key fields
Holocene_Volcanoes: Volcano_Number, Volcano_Name, Primary_Volcano_Type,
  Last_Eruption_Year (signed int; negative = BCE; blank = undated/no dated eruption),
  Geologic_Epoch, Evidence_Category, Tectonic_Setting, Major_Rock_Type, lat/lon.
Holocene_Eruptions: Volcano_Number, Eruption_Number, Activity_Type,
  StartDateYear (signed int; negative = BCE), StartDateYearModifier/Uncertainty,
  StartDateMonth/Day, ExplosivityIndexMax (VEI), StartEvidenceMethod.
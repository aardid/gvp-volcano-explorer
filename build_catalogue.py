"""
build_catalogue.py
------------------
Download a reproducible eruption / volcano catalogue from the Smithsonian
Global Volcanism Program (GVP) "Volcanoes of the World" (VOTW) database and
save it as CSV files in this folder.

Source: GVP WFS web services (GeoServer), layers:
    GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes   (one row per volcano)
    GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions    (one row per eruption)
    GVP-VOTW:Smithsonian_VOTW_Pleistocene_Volcanoes (context: dormant/extinct)

Reference: Global Volcanism Program (current v5.x), Volcanoes of the World;
Andrews et al. (2025), Bull. Volcanol. 87, 34.

Run:  python build_catalogue.py
Outputs (written next to this script):
    raw/gvp_holocene_volcanoes.geojson      (raw download, provenance)
    raw/gvp_holocene_eruptions.geojson
    raw/gvp_pleistocene_volcanoes.geojson
    gvp_holocene_volcanoes.csv              (flat table)
    gvp_holocene_eruptions.csv
    gvp_pleistocene_volcanoes.csv
    CATALOGUE_README.md                     (provenance + record counts)
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

BASE = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
PAGE = 100000  # this GeoServer rejects startIndex paging; fetch all in one request

LAYERS = {
    "gvp_holocene_volcanoes": "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes",
    "gvp_holocene_eruptions": "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions",
    "gvp_pleistocene_volcanoes": "GVP-VOTW:Smithsonian_VOTW_Pleistocene_Volcanoes",
    # population within 5/10/30/100 km per Holocene volcano (LandScan-based)
    "gvp_population_exposure": "GVP-VOTW:E3WebApp_HoloceneVolcanoes",
}


def fetch_layer(typename):
    """Page through a WFS 2.0 layer and return a GeoJSON FeatureCollection."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": typename,
        "outputFormat": "application/json",
        "count": PAGE,
        "srsName": "EPSG:4326",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "BK-paper-2026/catalogue-build"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    matched = data.get("numberMatched")
    returned = data.get("numberReturned", len(data.get("features", [])))
    print(f"    matched {matched}, returned {returned}")
    if matched not in (None, "unknown") and returned < int(matched):
        raise RuntimeError(f"truncated: got {returned} of {matched}; raise PAGE")
    return {"type": "FeatureCollection", "numberMatched": matched,
            "features": data.get("features", [])}


def flatten(fc):
    """GeoJSON FeatureCollection -> DataFrame of properties (+ geometry coords)."""
    rows = []
    for f in fc["features"]:
        row = dict(f.get("properties", {}) or {})
        geom = f.get("geometry") or {}
        if geom.get("type") == "Point" and geom.get("coordinates"):
            row.setdefault("Longitude", geom["coordinates"][0])
            row.setdefault("Latitude", geom["coordinates"][1])
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {}
    for name, typename in LAYERS.items():
        print(f"[{name}] downloading {typename}")
        fc = fetch_layer(typename)
        with open(os.path.join(RAW, name + ".geojson"), "w", encoding="utf-8") as fh:
            json.dump(fc, fh)
        df = flatten(fc)
        out_csv = os.path.join(HERE, name + ".csv")
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        counts[name] = len(df)
        print(f"    -> {out_csv}  ({len(df)} rows, {df.shape[1]} cols)")

    # provenance note
    readme = [
        "# GVP catalogue — provenance",
        "",
        f"Downloaded: {stamp}",
        f"Source: Smithsonian Global Volcanism Program (GVP), Volcanoes of the World (VOTW).",
        f"Endpoint: {BASE} (WFS 2.0, GeoServer).",
        "",
        "## Files",
    ]
    for name, n in counts.items():
        readme.append(f"- `{name}.csv` — {n} records (raw GeoJSON in `raw/`).")
    readme += [
        "",
        "## Citation",
        "Global Volcanism Program (current version), Volcanoes of the World database,",
        "Smithsonian Institution. https://volcano.si.edu  (compiled by E. Venzke).",
        "Andrews, B.J. et al. (2025). The Volcanoes of the World database. Bull. Volcanol. 87, 34.",
        "",
        "## Key fields",
        "Holocene_Volcanoes: Volcano_Number, Volcano_Name, Primary_Volcano_Type,",
        "  Last_Eruption_Year (signed int; negative = BCE; blank = undated/no dated eruption),",
        "  Geologic_Epoch, Evidence_Category, Tectonic_Setting, Major_Rock_Type, lat/lon.",
        "Holocene_Eruptions: Volcano_Number, Eruption_Number, Activity_Type,",
        "  StartDateYear (signed int; negative = BCE), StartDateYearModifier/Uncertainty,",
        "  StartDateMonth/Day, ExplosivityIndexMax (VEI), StartEvidenceMethod.",
    ]
    with open(os.path.join(HERE, "CATALOGUE_README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(readme))
    print("\nDone. Catalogue written to", HERE)
    print("Counts:", counts)


if __name__ == "__main__":
    sys.exit(main())

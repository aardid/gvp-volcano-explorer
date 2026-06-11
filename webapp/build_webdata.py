"""
build_webdata.py
----------------
Pack the local GVP catalogue (built by ../build_catalogue.py) into compact JS
data files for the static volcano-explorer web app (index.html).

Outputs (webapp/data/):
    data_core.js     window.GVP_CORE  -- meta + volcanoes[] + eruptions{}
    data_details.js  window.GVP_DETAILS -- number -> {summary, photo, ...}

Everything is emitted as `window.<NAME> = {...}` assigned via <script> tags so
the app works by double-clicking index.html (no local server / fetch / CORS).

Keeps the SAME tier thresholds, type grouping and REF_YEAR as the figure
scripts so the app and the paper figures never disagree.
"""

import os
import json
import math
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

REF_YEAR = 2026  # keep in sync with the figure scripts

# ---------------------------------------------------------------- load
vol = pd.read_csv(os.path.join(ROOT, "gvp_holocene_volcanoes.csv"))
eru = pd.read_csv(os.path.join(ROOT, "gvp_holocene_eruptions.csv"))
pop = pd.read_csv(os.path.join(ROOT, "gvp_population_exposure.csv")).rename(
    columns={"VolcanoNumber": "Volcano_Number"})


# ----------------------------------------------- volcano-type grouping
def type_group(t):
    if not isinstance(t, str):
        return "Other"
    s = t.lower()
    if "caldera" in s:
        return "Caldera"
    if "shield" in s:
        return "Shield"
    if "stratovolcano" in s or "complex" in s or "compound" in s:
        return "Stratovolcano / complex"
    if any(k in s for k in ["field", "cone", "fissure", "maar", "dome",
                            "tuff", "crater", "lava"]):
        return "Monogenetic / field"
    return "Other"


def tectonic_group(t):
    if not isinstance(t, str):
        return "Other"
    s = t.lower()
    if "subduction" in s:
        return "Subduction zone"
    if "rift" in s:
        return "Rift zone"
    if "intraplate" in s or "hotspot" in s or "plume" in s:
        return "Intraplate"
    return "Other"


# ----------------------------------------------- join population
vol = vol.merge(
    pop[["Volcano_Number", "Within_5km", "Within_10km",
         "Within_30km", "Within_100km"]],
    on="Volcano_Number", how="left")


def num(x):
    """float or None (JSON-safe)."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return f


def i_or_none(x):
    f = num(x)
    return None if f is None else int(round(f))


# ----------------------------------------------- build per-volcano eruption history
conf = eru[eru["Activity_Type"] == "Confirmed Eruption"].copy()
hist = {}
for vn, grp in conf.groupby("Volcano_Number"):
    rows = []
    for _, r in grp.iterrows():
        yr = num(r["StartDateYear"])
        if yr is None:
            continue
        vei = num(r["ExplosivityIndexMax"])
        rows.append([int(yr), (None if vei is None else int(vei))])
    rows.sort(key=lambda a: a[0])
    if rows:
        hist[int(vn)] = rows

# ----------------------------------------------- core volcano records
volcanoes = []
for _, r in vol.iterrows():
    lat, lon = num(r["Latitude"]), num(r["Longitude"])
    if lat is None or lon is None:
        continue
    volcanoes.append({
        "n":    int(r["Volcano_Number"]),
        "name": r["Volcano_Name"],
        "cty":  r["Country"] if isinstance(r["Country"], str) else "",
        "reg":  r["Region"] if isinstance(r["Region"], str) else "",
        "type": r["Primary_Volcano_Type"] if isinstance(r["Primary_Volcano_Type"], str) else "Unknown",
        "tg":   type_group(r["Primary_Volcano_Type"]),
        "tec":  r["Tectonic_Setting"] if isinstance(r["Tectonic_Setting"], str) else "",
        "teg":  tectonic_group(r["Tectonic_Setting"]),
        "rock": r["Major_Rock_Type"] if isinstance(r["Major_Rock_Type"], str) else "",
        "lat":  round(lat, 4),
        "lon":  round(lon, 4),
        "elev": i_or_none(r["Elevation"]),
        "ley":  i_or_none(r["Last_Eruption_Year"]),   # None = undated
        "p5":   i_or_none(r["Within_5km"]),
        "p10":  i_or_none(r["Within_10km"]),
        "p30":  i_or_none(r["Within_30km"]),
        "p100": i_or_none(r["Within_100km"]),
        "ne":   len(hist.get(int(r["Volcano_Number"]), [])),  # n confirmed eruptions
    })

meta = {
    "ref_year": REF_YEAR,
    "n_volcanoes": len(volcanoes),
    "n_dated": sum(1 for v in volcanoes if v["ley"] is not None),
    "n_undated": sum(1 for v in volcanoes if v["ley"] is None),
    "n_eruptions": int(sum(len(v) for v in hist.values())),
    "source": "Smithsonian GVP — Volcanoes of the World (WFS)",
    # draft Table 2 default thresholds (years)
    "thresholds": {"erupting": 0.252, "high": 500, "moderate": 12000,
                   "dormant": 2.5e6},
}

core = {"meta": meta, "volcanoes": volcanoes, "eruptions": hist}

# ----------------------------------------------- details (heavy fields, lazy)
details = {}
for _, r in vol.iterrows():
    vn = int(r["Volcano_Number"])
    details[vn] = {
        "sum":    r["Geological_Summary"] if isinstance(r["Geological_Summary"], str) else "",
        "photo":  r["Primary_Photo_Link"] if isinstance(r["Primary_Photo_Link"], str) else "",
        "cap":    r["Primary_Photo_Caption"] if isinstance(r["Primary_Photo_Caption"], str) else "",
        "credit": r["Primary_Photo_Credit"] if isinstance(r["Primary_Photo_Credit"], str) else "",
        "sreg":   r["Subregion"] if isinstance(r["Subregion"], str) else "",
        "epoch":  r["Geologic_Epoch"] if isinstance(r["Geologic_Epoch"], str) else "",
    }


def dump(name, varname, obj):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.%s = " % varname)
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print("wrote", path, "(%.0f KB)" % (os.path.getsize(path) / 1024))


dump("data_core.js", "GVP_CORE", core)
dump("data_details.js", "GVP_DETAILS", details)

print("\nmeta:", json.dumps(meta, indent=2))

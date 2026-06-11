"""
build_lasteruption_figure.py
----------------------------
Build the "active volcanoes vs. time since last eruption" figure for
Kennedy et al. (terminology paper), from the local GVP catalogue produced by
build_catalogue.py.

Inputs (in this folder):
    gvp_holocene_volcanoes.csv
    gvp_holocene_eruptions.csv
Outputs:
    last_eruption_per_volcano.csv      derived per-volcano table
    fig_time_since_last_eruption.png   3-panel publication figure
    fig_time_since_last_eruption.svg

Reference date: 2026 (manuscript uses status "on 01/12/2025"; current = 2026).
Tier thresholds overlaid are from the manuscript's draft Table 2:
    erupting  = 92 days (~0.25 yr)
    high      = 500 yr
    moderate  = 12,000 yr (Holocene)
    (dormant  = 2.5 Myr / extinct > 2.5 Myr lie beyond the Holocene population)
"""

import os
import urllib.request
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
REF_YEAR = 2026

# ---------------------------------------------------------------- load
vol = pd.read_csv(os.path.join(HERE, "gvp_holocene_volcanoes.csv"))
eru = pd.read_csv(os.path.join(HERE, "gvp_holocene_eruptions.csv"))
pleist = pd.read_csv(os.path.join(HERE, "gvp_pleistocene_volcanoes.csv"))

# basemap (Natural Earth 110m countries); cache locally, fetch if missing
BASEMAP = os.path.join(HERE, "raw", "ne_110m_admin_0_countries.geojson")
if not os.path.exists(BASEMAP):
    url = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
           "master/geojson/ne_110m_admin_0_countries.geojson")
    print("downloading basemap ...")
    urllib.request.urlretrieve(url, BASEMAP)
world = gpd.read_file(BASEMAP)


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


vol["Type_group"] = vol["Primary_Volcano_Type"].apply(type_group)

# ----------------------------------------------- years since last eruption
vol["years_since"] = REF_YEAR - vol["Last_Eruption_Year"]
dated = vol[vol["Last_Eruption_Year"].notna()].copy()
n_undated = int(vol["Last_Eruption_Year"].isna().sum())
# floor so a 2026 eruption (years_since 0) plots in the recent-most bin
FLOOR = 0.04  # ~2 weeks in years
dated["years_since_plot"] = dated["years_since"].clip(lower=FLOOR)

# derived table for coauthors
out = vol[["Volcano_Number", "Volcano_Name", "Country", "Primary_Volcano_Type",
           "Type_group", "Tectonic_Setting", "Last_Eruption_Year",
           "years_since"]].copy()
out["dated"] = vol["Last_Eruption_Year"].notna()
out = out.sort_values("years_since")
out.to_csv(os.path.join(HERE, "last_eruption_per_volcano.csv"),
           index=False, encoding="utf-8-sig")

# ----------------------------------------------- shared log bins
BMIN, BMAX = 0.03, 15000.0
bins = np.logspace(np.log10(BMIN), np.log10(BMAX), 38)

# tier thresholds (yr) from draft Table 2
THRESH = [(0.252, "92 days\n(erupting)"),
          (500, "500 yr\n(high)"),
          (12000, "12 kyr\n(Holocene /\nmoderate)")]

TYPE_ORDER = ["Caldera", "Stratovolcano / complex", "Shield",
              "Monogenetic / field", "Other"]
TYPE_COLORS = {
    "Caldera": "#b2182b",
    "Stratovolcano / complex": "#ef8a62",
    "Shield": "#fddbc7",
    "Monogenetic / field": "#67a9cf",
    "Other": "#bdbdbd",
}

# ====================================================== figure 1 (a-d)
fig = plt.figure(figsize=(11, 12))
gs = gridspec.GridSpec(3, 2, height_ratios=[1.15, 1.0, 0.78],
                       hspace=0.38, wspace=0.24)

# ---- Panel A: overall distribution + tiers --------------------------
axA = fig.add_subplot(gs[0, :])
axA.hist(dated["years_since_plot"], bins=bins, color="#4d4d4d",
         edgecolor="white", linewidth=0.4)
axA.set_xscale("log")
for x, lab in THRESH:
    axA.axvline(x, color="#2166ac", ls="--", lw=1.3, alpha=0.9)
    axA.text(x, axA.get_ylim()[1] * 0.92, lab, rotation=0, ha="center",
             va="top", fontsize=8, color="#2166ac",
             bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.5))
axA.set_xlim(0.025, 30000)
axA.set_xlabel("Time since last known eruption (years, log scale)")
axA.set_ylabel("Number of volcanoes")
axA.set_title("a)  Distribution of the world's active (Holocene) volcanoes "
              "by time since last eruption", fontsize=11, loc="left")
axA.text(10, 0.93,
         f"n = {len(dated)} dated volcanoes\n"
         f"+{n_undated} Holocene volcanoes undated\n(no last-eruption year; not shown)",
         transform=axA.get_xaxis_transform(), ha="center", va="top", fontsize=8.5,
         bbox=dict(fc="#fff3cd", ec="#cccccc", pad=0.5))

# ---- Panel B: by volcano type (stacked) -----------------------------
axB = fig.add_subplot(gs[1, 0])
stack = [dated.loc[dated["Type_group"] == g, "years_since_plot"]
         for g in TYPE_ORDER]
axB.hist(stack, bins=bins, stacked=True,
         color=[TYPE_COLORS[g] for g in TYPE_ORDER],
         label=[f"{g} ({(dated['Type_group'] == g).sum()})" for g in TYPE_ORDER],
         edgecolor="white", linewidth=0.2)
axB.set_xscale("log")
for x, _ in THRESH:
    axB.axvline(x, color="#2166ac", ls="--", lw=0.9, alpha=0.7)
axB.set_xlim(0.025, 30000)
axB.set_xlabel("Time since last eruption (years, log scale)")
axB.set_ylabel("Number of volcanoes")
axB.set_title("b)  Same distribution, split by volcano type", fontsize=11, loc="left")
axB.legend(fontsize=7.5, loc="upper left", framealpha=0.9)

# ---- Panel C: recording completeness --------------------------------
axC = fig.add_subplot(gs[1, 1])
conf = eru[eru["Activity_Type"] == "Confirmed Eruption"].copy()
recent = conf[conf["StartDateYear"] >= -1000]
cbins = np.arange(-1000, REF_YEAR + 50, 50)
axC.hist(recent["StartDateYear"], bins=cbins, color="#762a83",
         edgecolor="white", linewidth=0.3)
axC.axvline(1500, color="#1a9850", ls="--", lw=1.4)
axC.text(1500, axC.get_ylim()[1] * 0.96, " global record\n broadly complete\n after ~1500 CE",
         ha="right", va="top", fontsize=8, color="#1a9850")
axC.set_yscale("log")
axC.set_xlabel("Year of eruption onset (CE)")
axC.set_ylabel("Confirmed eruptions per 50 yr (log)")
axC.set_title("c)  Eruption record is dominated by recent under-recording",
              fontsize=10.5, loc="left")

# ---- Panel D: full-population tier map, days -> >2.5 Myr ------------
axD = fig.add_subplot(gs[2, :])
ys = dated["years_since"]
n_erupt = int((ys <= 0.252).sum())
n_high = int(((ys > 0.252) & (ys <= 500)).sum())
n_mod = int(((ys > 500) & (ys <= 12000)).sum())
n_pleist = len(pleist)

# (x0, x1, count, color, tier label)
TIERS = [
    (0.04, 0.252, n_erupt, "#67000d", "Erupting"),
    (0.252, 500, n_high, "#ef3b2c", "High"),
    (500, 12000, n_mod, "#fdae61", "Moderate"),
    (12000, 2.5e6, n_pleist, "#4575b4", "Dormant\n(Pleistocene)"),
    (2.5e6, 1e7, 0, "#969696", "Extinct"),
]
ymax = max(n_high, n_mod, n_pleist) * 1.25
for x0, x1, n, c, lab in TIERS:
    if n > 0:
        axD.add_patch(Rectangle((x0, 0), x1 - x0, n, facecolor=c,
                                edgecolor="white", linewidth=0.6, alpha=0.95))
        xc = np.sqrt(x0 * x1)
        axD.text(xc, n + ymax * 0.02, str(n), ha="center", va="bottom",
                 fontsize=9, fontweight="bold")
    xc = np.sqrt(x0 * x1)
    axD.text(xc, -ymax * 0.10, lab, ha="center", va="top", fontsize=8.5,
             color="#333333")
# extinct annotation
axD.text(3.2e6, ymax * 0.16,
         "not systematically\ncatalogued by GVP", ha="left", va="bottom",
         fontsize=7.5, style="italic", color="#666666")
for x in (0.252, 500, 12000, 2.5e6):
    axD.axvline(x, color="#444444", ls=":", lw=0.8, alpha=0.6)
# active brace
axD.annotate("", xy=(0.04, ymax * 1.02), xytext=(12000, ymax * 1.02),
             arrowprops=dict(arrowstyle="-", color="#67000d", lw=1.3))
axD.text(np.sqrt(0.04 * 12000), ymax * 1.05, "ACTIVE  (Holocene)",
         ha="center", va="bottom", fontsize=9, color="#67000d",
         fontweight="bold")
axD.set_xscale("log")
axD.set_xlim(0.025, 1e7)
axD.set_ylim(-ymax * 0.30, ymax * 1.18)
axD.set_xlabel("Time since last eruption (years, log scale)")
axD.set_ylabel("Number of volcanoes")
axD.set_yticks([t for t in axD.get_yticks() if t >= 0])
axD.set_title("d)  Full volcano population mapped onto the draft Table 2 tiers "
              "(active → dormant → extinct)", fontsize=11, loc="left")
axD.text(0.012, 0.64,
         f"+{n_undated} undated Holocene volcanoes are\nactive but untimed "
         f"(somewhere in 0–12 kyr)",
         transform=axD.transAxes, ha="left", va="top", fontsize=8,
         bbox=dict(fc="#fff3cd", ec="#cccccc", pad=0.4))

fig.suptitle("World active-volcano population and time since last eruption "
             "— Smithsonian GVP / Volcanoes of the World",
             fontsize=12.5, y=0.99)
fig.text(0.5, 0.045,
         f"Data: GVP Volcanoes of the World (Holocene volcanoes n={len(vol)}, "
         f"confirmed eruptions n={len(conf)}, Pleistocene volcanoes n={len(pleist)}). "
         f"Reference year {REF_YEAR}. Tier thresholds from draft Table 2.",
         ha="center", fontsize=7.5, color="#555555")

png = os.path.join(HERE, "fig_time_since_last_eruption.png")
svg = os.path.join(HERE, "fig_time_since_last_eruption.svg")
fig.savefig(png, dpi=200, bbox_inches="tight")
fig.savefig(svg, bbox_inches="tight")
print("wrote", png)
print("wrote", svg)

# ====================================================== figure 2 (map)
undated_v = vol[vol["Last_Eruption_Year"].isna()]
CMAP, VMIN, VMAX = "plasma_r", np.log10(0.1), np.log10(12000)

# dense regions to zoom (name, lon0, lon1, lat0, lat1)
REGIONS = [
    ("Alaska–Aleutians", -180, -145, 50, 65),
    ("Kamchatka–Kurile–Japan", 122, 167, 28, 62),
    ("Indonesia–Philippines", 94, 128, -11, 20),
    ("Central America–Mexico", -106, -83, 8, 22),
    ("Andes", -78, -66, -46, 2),
    ("East Africa Rift", 28, 45, -6, 15),
]


def plot_volcanoes(ax, s_dated=26, s_undated=14):
    world.plot(ax=ax, color="#d4d6d9", edgecolor="#9aa0a6",
               linewidth=0.4, zorder=0)
    ax.scatter(undated_v["Longitude"], undated_v["Latitude"], s=s_undated,
               facecolor="none", edgecolor="#888888", linewidth=0.5, zorder=2)
    return ax.scatter(dated["Longitude"], dated["Latitude"],
                      c=np.log10(dated["years_since_plot"]), cmap=CMAP,
                      s=s_dated, edgecolor="white", linewidth=0.25,
                      vmin=VMIN, vmax=VMAX, zorder=3)


figM = plt.figure(figsize=(14, 15))
gsM = gridspec.GridSpec(3, 3, height_ratios=[2.0, 1.0, 1.0],
                        hspace=0.28, wspace=0.18)

# --- world overview (spans top row, full width) ---
axE = figM.add_subplot(gsM[0, :])
sc = plot_volcanoes(axE)
axE.scatter([], [], facecolor="none", edgecolor="#888888",
            label=f"undated ({len(undated_v)})")
axE.set_xlim(-180, 180)
axE.set_ylim(-78, 84)
axE.set_xlabel("Longitude")
axE.set_ylabel("Latitude")
axE.set_title("Spatial distribution of the world's active (Holocene) volcanoes, "
              "coloured by time since last eruption", fontsize=13, loc="left")
axE.legend(loc="lower left", fontsize=8.5, framealpha=0.9)
axE.set_aspect("equal", adjustable="box")
# colorbar as an inset so it does not reduce the map width
cax = axE.inset_axes([1.012, 0.08, 0.013, 0.84])
cbar = figM.colorbar(sc, cax=cax, orientation="vertical")
cbar.set_ticks([np.log10(v) for v in [0.1, 1, 10, 100, 1000, 10000]])
cbar.set_ticklabels(["0.1", "1", "10", "100", "1k", "10k"])
cbar.set_label("Years since last eruption (log scale)", fontsize=9)

# zoom boxes drawn + numbered on the overview
for i, (name, x0, x1, y0, y1) in enumerate(REGIONS, 1):
    axE.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none",
                            edgecolor="#1a1a1a", linewidth=1.0, zorder=4))
    axE.text(x1, y1, str(i), fontsize=9, fontweight="bold", color="#1a1a1a",
             ha="left", va="bottom", zorder=5)

# --- six zoom panels ---
zoom_cells = [gsM[1, 0], gsM[1, 1], gsM[1, 2], gsM[2, 0], gsM[2, 1], gsM[2, 2]]
for (name, x0, x1, y0, y1), cell, i in zip(REGIONS, zoom_cells,
                                           range(1, len(REGIONS) + 1)):
    axz = figM.add_subplot(cell)
    plot_volcanoes(axz, s_dated=34, s_undated=18)
    n_here = int(dated["Longitude"].between(x0, x1).mul(
        dated["Latitude"].between(y0, y1)).sum())
    axz.set_title(f"{i}.  {name}  (n={n_here})", fontsize=10, loc="left")
    # datalim: axes fills its cell (uniform, aligned grid) while keeping
    # geographic shapes undistorted; the box is expanded to fit, not shrunk
    axz.set_aspect("equal", adjustable="datalim")
    axz.set_xlim(x0, x1)
    axz.set_ylim(y0, y1)
    axz.tick_params(labelsize=7)

figM.text(0.5, 0.005,
          f"Data: GVP Volcanoes of the World (Holocene volcanoes n={len(vol)}; "
          f"{len(dated)} with a dated last eruption, {n_undated} undated). "
          f"Reference year {REF_YEAR}. Colour scale shared across all panels. "
          f"Basemap: Natural Earth 110m.",
          ha="center", fontsize=8, color="#555555")

pngM = os.path.join(HERE, "fig_volcano_map.png")
svgM = os.path.join(HERE, "fig_volcano_map.svg")
figM.savefig(pngM, dpi=200, bbox_inches="tight")
figM.savefig(svgM, bbox_inches="tight")
print("wrote", pngM)
print("wrote", svgM)
print("wrote", os.path.join(HERE, "last_eruption_per_volcano.csv"))

# ----------------------------------------------- quick text summary
print("\n--- summary ---")
print(f"Holocene volcanoes: {len(vol)}  (dated {len(dated)}, undated {n_undated})")
for g in TYPE_ORDER:
    sub = dated[dated["Type_group"] == g]["years_since"]
    if len(sub):
        print(f"  {g:24s} n={len(sub):4d}  median repose {sub.median():8.0f} yr")

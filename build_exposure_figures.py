"""
build_exposure_figures.py
-------------------------
Alternative / companion figures embedding POPULATION EXPOSURE alongside time
since last eruption, for Kennedy et al. (terminology paper).

Population source: GVP E3WebApp Holocene volcanoes layer (LandScan-based
population within 5/10/30/100 km), keyed by Volcano_Number -- the same numbers
shown on GVP volcano profile pages, consistent with the Global Volcano Model /
Auker et al. (2015) exposure approach already cited in the manuscript.

Inputs (in parent folder):  gvp_holocene_volcanoes.csv, gvp_population_exposure.csv,
                            raw/ne_110m_admin_0_countries.geojson
Outputs (exposure_figs/):
    fig_exposure_vs_repose.png/.svg   (2-panel: scatter + exposure-by-tier bar)
    fig_exposure_map.png/.svg         (world map, size = pop within 30 km)
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exposure_figs")
os.makedirs(OUT, exist_ok=True)
REF_YEAR = 2026
RKM = "Within_30km"   # exposure radius used throughout

# ---------------------------------------------------------------- load + join
vol = pd.read_csv(os.path.join(HERE, "gvp_holocene_volcanoes.csv"))
pop = pd.read_csv(os.path.join(HERE, "gvp_population_exposure.csv")).rename(
    columns={"VolcanoNumber": "Volcano_Number"})
df = vol.merge(pop[["Volcano_Number", "Within_5km", "Within_10km",
                    "Within_30km", "Within_100km"]],
               on="Volcano_Number", how="left")
df["years_since"] = REF_YEAR - df["Last_Eruption_Year"]


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


df["Type_group"] = df["Primary_Volcano_Type"].apply(type_group)

TYPE_ORDER = ["Caldera", "Stratovolcano / complex", "Shield",
              "Monogenetic / field", "Other"]
TYPE_COLORS = {"Caldera": "#b2182b", "Stratovolcano / complex": "#ef8a62",
               "Shield": "#f19c3f", "Monogenetic / field": "#2166ac",
               "Other": "#969696"}

# tier thresholds (yr) from draft Table 2
T_ERUPT, T_HIGH, T_MOD = 0.252, 500, 12000
FLOOR_X = 0.04   # ~2 weeks, so 2026 eruptions plot at left edge
FLOOR_Y = 1      # people: plot zeros at 1 on log axis

dd = df[df[RKM].notna()].copy()
dd["x"] = (REF_YEAR - dd["Last_Eruption_Year"]).clip(lower=FLOOR_X)
dd["y"] = dd[RKM].clip(lower=FLOOR_Y)
dated = dd[dd["Last_Eruption_Year"].notna()].copy()

# ===================================== FIGURE 1: exposure vs repose (scatter)
fig = plt.figure(figsize=(9.5, 6.6))
axa = fig.add_subplot(111)
# tier band shading
bands = [(FLOOR_X, T_ERUPT, "#fde0dd", "Erupting"),
         (T_ERUPT, T_HIGH, "#fff2cc", "High"),
         (T_HIGH, T_MOD, "#e6f2da", "Moderate")]
for x0, x1, c, lab in bands:
    axa.axvspan(x0, x1, color=c, alpha=0.7, zorder=0)
    axa.text(np.sqrt(x0 * x1), 1.4e7, lab, ha="center", va="top", fontsize=8.5,
             color="#555555")
for g in TYPE_ORDER:
    s = dated[dated["Type_group"] == g]
    axa.scatter(s["x"], s["y"], s=18, c=TYPE_COLORS[g], edgecolor="white",
                linewidth=0.2, alpha=0.85, label=g, zorder=3)
axa.set_xscale("log")
axa.set_yscale("log")
axa.set_xlim(FLOOR_X, 2e4)
axa.set_ylim(0.5, 2e7)
axa.set_xlabel("Time since last eruption (years, log scale)")
axa.set_ylabel("Population within 30 km (log scale)")
axa.set_title("Population exposure vs. time since last eruption "
              "— each point a volcano", fontsize=11, loc="left")
axa.legend(fontsize=7.5, loc="lower left", framealpha=0.9, title="Volcano type",
           title_fontsize=8)

# number the high-exposure, long-repose volcanoes (the risk-mislabel argument)
LABELS = ["Tatun Volcanic Group", "Chichinautzin", "Campi Flegrei",
          "Nevado de Toluca", "Auckland Volcanic Field", "Barva",
          "San Pablo Volcanic Field", "La Malinche"]
picks = []
for nm in LABELS:
    hit = dated[dated["Volcano_Name"].str.contains(nm.split(",")[0], case=False,
                                                   na=False)]
    if len(hit):
        picks.append(hit.iloc[0])
picks = sorted(picks, key=lambda r: r["y"], reverse=True)
keylines = []
for i, r in enumerate(picks, 1):
    axa.scatter([r["x"]], [r["y"]], s=70, facecolor="none", edgecolor="black",
                linewidth=0.9, zorder=4)
    axa.annotate(str(i), (r["x"], r["y"]), xytext=(4, 3),
                 textcoords="offset points", fontsize=8, fontweight="bold",
                 zorder=5)
    repose = int(REF_YEAR - r["Last_Eruption_Year"])
    keylines.append(f"{i}. {r['Volcano_Name']} — {r['y']/1e6:.1f}M, {repose:,} yr")
box = ("Long-repose, high-exposure volcanoes\n"
       "(a time-only label understates their risk):\n" + "\n".join(keylines))
axa.text(0.985, 0.03, box, transform=axa.transAxes, ha="right", va="bottom",
         fontsize=6.8, bbox=dict(fc="#fff3cd", ec="#cccccc", pad=0.5), zorder=6)

fig.savefig(os.path.join(OUT, "fig_exposure_vs_repose.png"), dpi=200,
            bbox_inches="tight")
fig.savefig(os.path.join(OUT, "fig_exposure_vs_repose.svg"), bbox_inches="tight")
print("wrote fig_exposure_vs_repose")

# ===================================== FIGURE 2: total exposure by active tier
figB, axb = plt.subplots(figsize=(6.2, 5.4))


def tier(ys):
    if pd.isna(ys):
        return "Undated"
    if ys <= T_ERUPT:
        return "Erupting"
    if ys <= T_HIGH:
        return "High"
    return "Moderate"


df["tier"] = df["years_since"].apply(tier)
order = ["Erupting", "High", "Moderate", "Undated"]
colors = ["#67000d", "#ef3b2c", "#fdae61", "#cccccc"]
sums = [df.loc[df["tier"] == t, RKM].sum(skipna=True) / 1e6 for t in order]
counts = [int((df["tier"] == t).sum()) for t in order]
bars = axb.bar(order, sums, color=colors, edgecolor="white")
for b, s, n in zip(bars, sums, counts):
    axb.text(b.get_x() + b.get_width() / 2, s, f"{s:.1f}M\n({n} volc.)",
             ha="center", va="bottom", fontsize=8)
axb.set_ylabel("Total population within 30 km (millions)")
axb.set_title("Population exposure by active-tier\n"
              "(sum of per-volcano pop. within 30 km)", fontsize=11, loc="left")
axb.set_ylim(0, max(sums) * 1.18)
axb.tick_params(axis="x", labelsize=9)
axb.text(0.5, -0.16, "People near several volcanoes are counted more than once; "
         "Pleistocene/dormant\nexcluded (no exposure data).",
         transform=axb.transAxes, ha="center", fontsize=7, color="#666666")
figB.savefig(os.path.join(OUT, "fig_exposure_by_tier.png"), dpi=200,
             bbox_inches="tight")
figB.savefig(os.path.join(OUT, "fig_exposure_by_tier.svg"), bbox_inches="tight")
print("wrote fig_exposure_by_tier")

# ============================================================ FIGURE 2 (map)
world = gpd.read_file(os.path.join(HERE, "raw",
                                   "ne_110m_admin_0_countries.geojson"))
figM, axM = plt.subplots(figsize=(14, 7.2))
world.plot(ax=axM, color="#d4d6d9", edgecolor="#9aa0a6", linewidth=0.4, zorder=0)
m = dated.copy()
# marker size scales with sqrt(pop) so area ~ population
size = 6 + np.sqrt(m["y"]) / 6.0
sc = axM.scatter(m["Longitude"], m["Latitude"], s=size,
                 c=np.log10((REF_YEAR - m["Last_Eruption_Year"]).clip(lower=0.1)),
                 cmap="plasma_r", vmin=np.log10(0.1), vmax=np.log10(12000),
                 edgecolor="black", linewidth=0.25, alpha=0.8, zorder=3)
axM.set_xlim(-180, 180)
axM.set_ylim(-78, 84)
axM.set_aspect("equal", adjustable="box")
axM.set_xlabel("Longitude")
axM.set_ylabel("Latitude")
axM.set_title("Active volcanoes: marker size = population within 30 km, "
              "colour = time since last eruption", fontsize=12, loc="left")
cax = axM.inset_axes([1.012, 0.08, 0.013, 0.84])
cbar = figM.colorbar(sc, cax=cax)
cbar.set_ticks([np.log10(v) for v in [0.1, 1, 10, 100, 1000, 10000]])
cbar.set_ticklabels(["0.1", "1", "10", "100", "1k", "10k"])
cbar.set_label("Years since last eruption (log)", fontsize=9)
# size legend
for pv in [10000, 100000, 1000000, 5000000]:
    axM.scatter([], [], s=6 + np.sqrt(pv) / 6.0, c="#888888", edgecolor="black",
                linewidth=0.25, label=f"{pv:,}")
axM.legend(loc="lower left", fontsize=7.5, title="Pop. within 30 km",
           title_fontsize=8, labelspacing=1.1, framealpha=0.9, borderpad=0.8)
figM.text(0.5, 0.02, "Data: GVP Volcanoes of the World; population within 30 km "
          "(GVP / LandScan). Reference year {}. Basemap: Natural Earth 110m."
          .format(REF_YEAR), ha="center", fontsize=7.5, color="#555555")
figM.savefig(os.path.join(OUT, "fig_exposure_map.png"), dpi=200,
             bbox_inches="tight")
figM.savefig(os.path.join(OUT, "fig_exposure_map.svg"), bbox_inches="tight")
print("wrote fig_exposure_map")

# ---- console summary ----
print("\n--- exposure summary (within 30 km) ---")
for t, s, n in zip(order, sums, counts):
    print(f"  {t:10s} {n:4d} volcanoes  total {s:7.1f}M")
print(f"  volcanoes with pop data: {df[RKM].notna().sum()} / {len(df)}")

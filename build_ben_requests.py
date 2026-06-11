"""
build_ben_requests.py
---------------------
Figures requested by Ben Kennedy (email, review of the terminology paper):

  1. fig_cutoff_sensitivity  -- revised "panel d" analysis:
       (a) distribution of repose with candidate cut-offs (92 d, 100 yr, 500 yr,
           12 kyr) and the 100-500 yr band that the high->moderate move reshuffles;
       (b) category counts under the 500-yr vs 100-yr high/moderate boundary,
           PLUS a dedicated "Active but undated" column (the 366).
       Does a 100-yr cut-off even out the numbers? (Campi Flegrei -> moderate.)

  2. fig_repose_vs_recurrence -- is repose time informative? Scatter of repose
       vs mean recurrence interval (volcanoes with >=3 confirmed eruptions),
       1:1 "due" line, Spearman correlation.

  3. fig_repose_by_type -- box-and-whisker of repose period (and recurrence
       interval) by volcano type, with Kruskal-Wallis statistics.

Inputs : gvp_holocene_volcanoes.csv, gvp_holocene_eruptions.csv
Outputs: ben_figs/*.png + *.svg, and a printed summary table for the text.

Keeps REF_YEAR, type_group() and the draft Table 2 thresholds consistent with
the other figure scripts.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import Rectangle
from scipy.stats import kruskal, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ben_figs")
os.makedirs(OUT, exist_ok=True)
REF_YEAR = 2026

# thresholds (yr) -- draft Table 2, plus Ben's candidate 100-yr boundary
T_ERUPT, T_HIGH, T_MOD = 0.252, 500, 12000
T_HIGH_ALT = 100  # Ben's proposed high->moderate cut-off (~a human lifetime)


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


TYPE_ORDER = ["Caldera", "Stratovolcano / complex", "Shield",
              "Monogenetic / field", "Other"]
TYPE_COLORS = {"Caldera": "#b2182b", "Stratovolcano / complex": "#ef8a62",
               "Shield": "#f1b25a", "Monogenetic / field": "#67a9cf",
               "Other": "#9aa6b8"}

# ---------------------------------------------------------------- load
vol = pd.read_csv(os.path.join(HERE, "gvp_holocene_volcanoes.csv"))
eru = pd.read_csv(os.path.join(HERE, "gvp_holocene_eruptions.csv"))
vol["Type_group"] = vol["Primary_Volcano_Type"].apply(type_group)
vol["years_since"] = REF_YEAR - vol["Last_Eruption_Year"]
dated = vol[vol["Last_Eruption_Year"].notna()].copy()
n_undated = int(vol["Last_Eruption_Year"].isna().sum())
FLOOR = 0.04
dated["ys_plot"] = dated["years_since"].clip(lower=FLOOR)

# ---------------------------------------------- recurrence per volcano
conf = eru[(eru["Activity_Type"] == "Confirmed Eruption") &
           (eru["StartDateYear"].notna())].copy()
rec = []
for vn, grp in conf.groupby("Volcano_Number"):
    yrs = np.sort(grp["StartDateYear"].values.astype(float))
    n = len(yrs)
    if n < 3:
        continue
    span = yrs[-1] - yrs[0]
    if span <= 0:
        continue
    mri = span / (n - 1)                      # mean recurrence interval
    gaps = np.diff(yrs)
    rec.append({"Volcano_Number": int(vn), "n_eru": n,
                "mri": mri, "median_gap": float(np.median(gaps)),
                "last_eru": yrs[-1]})
rec = pd.DataFrame(rec)
rec = rec.merge(vol[["Volcano_Number", "Volcano_Name", "Type_group",
                     "years_since"]], on="Volcano_Number", how="left")
rec["repose"] = rec["years_since"].clip(lower=FLOOR)

# ============================================================ FIGURE 1
fig = plt.figure(figsize=(12, 5.2))
gs = gridspec.GridSpec(1, 2, width_ratios=[1.25, 1.0], wspace=0.26)

# --- (a) distribution with candidate cut-offs ---
axA = fig.add_subplot(gs[0])
bins = np.logspace(np.log10(0.03), np.log10(15000), 38)
axA.hist(dated["ys_plot"], bins=bins, color="#4d4d4d", edgecolor="white", lw=0.4)
axA.set_xscale("log")
ymax = axA.get_ylim()[1]
# shade the 100-500 yr band that the high->moderate move reshuffles
axA.add_patch(Rectangle((T_HIGH_ALT, 0), T_HIGH - T_HIGH_ALT, ymax,
                        facecolor="#5aa9ff", alpha=0.16, zorder=0))
n_band = int(((dated["years_since"] > T_HIGH_ALT) &
              (dated["years_since"] <= T_HIGH)).sum())
for x, lab, c in [(T_ERUPT, "92 d", "#67000d"), (T_HIGH_ALT, "100 yr", "#1a9850"),
                  (T_HIGH, "500 yr", "#2166ac"), (T_MOD, "12 kyr", "#444444")]:
    axA.axvline(x, color=c, ls="--", lw=1.3)
    axA.text(x, ymax * 0.97, lab, rotation=90, ha="right", va="top",
             fontsize=8.5, color=c)
axA.set_xlim(0.025, 30000)
axA.set_xlabel("Time since last eruption (years, log scale)")
axA.set_ylabel("Number of volcanoes")
axA.set_title("a)  Repose distribution and candidate high→moderate cut-offs",
              fontsize=11, loc="left")

# --- (b) category counts under 500 vs 100 yr, + undated column ---
axB = fig.add_subplot(gs[1])
ys = dated["years_since"]
n_erupt = int((ys <= T_ERUPT).sum())
# 500-yr scheme
h500 = int(((ys > T_ERUPT) & (ys <= T_HIGH)).sum())
m500 = int(((ys > T_HIGH) & (ys <= T_MOD)).sum())
# 100-yr scheme
h100 = int(((ys > T_ERUPT) & (ys <= T_HIGH_ALT)).sum())
m100 = int(((ys > T_HIGH_ALT) & (ys <= T_MOD)).sum())

cats = ["Erupting", "High", "Moderate"]
v500 = [n_erupt, h500, m500]
v100 = [n_erupt, h100, m100]
x = np.arange(len(cats))
w = 0.38
b1 = axB.bar(x - w/2, v500, w, color="#ef8a62", label="500-yr boundary (current)")
b2 = axB.bar(x + w/2, v100, w, color="#1a9850", label="100-yr boundary (proposed)")
# undated as its own column
axB.bar(len(cats), n_undated, w*1.6, color="#c9c9c9", hatch="//",
        edgecolor="#7a7a7a", label="Active but undated")
for rects in (b1, b2):
    for r in rects:
        axB.text(r.get_x()+r.get_width()/2, r.get_height()+6, str(int(r.get_height())),
                 ha="center", va="bottom", fontsize=8)
axB.text(len(cats), n_undated+6, str(n_undated), ha="center", va="bottom", fontsize=8)
axB.set_xticks(list(x) + [len(cats)])
axB.set_xticklabels(cats + ["Undated"])
axB.set_ylabel("Number of volcanoes")
axB.set_title("b)  Category counts: 500-yr vs 100-yr high/moderate split",
              fontsize=11, loc="left")
axB.legend(fontsize=8, loc="upper right", framealpha=0.95)
even = len(dated) / 3
axB.axhline(even, color="#888", ls=":", lw=1)
axB.text(2.4, even, f"even split\n({even:.0f} each)", fontsize=7.5,
         color="#666", va="bottom", ha="left")

fig.suptitle("Cut-off sensitivity for the active-volcano tiers "
             "(GVP Holocene volcanoes, ref. year 2026)", fontsize=12, y=1.0)
fig.savefig(os.path.join(OUT, "fig_cutoff_sensitivity.png"), dpi=200, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "fig_cutoff_sensitivity.svg"), bbox_inches="tight")

# ============================================================ FIGURE 2
fig2, ax = plt.subplots(figsize=(7.6, 7))
for g in TYPE_ORDER:
    sub = rec[rec["Type_group"] == g]
    if len(sub) == 0:
        continue
    ax.scatter(sub["mri"], sub["repose"], s=26, alpha=0.75,
               color=TYPE_COLORS[g], edgecolor="white", linewidth=0.3,
               label=f"{g} ({len(sub)})")
lim = [0.5, 1e5]
ax.plot(lim, lim, "k--", lw=1, zorder=0)
ax.text(2e4, 2e4*1.15, "repose = mean interval\n(“due”)", fontsize=8,
        rotation=45, ha="center", va="bottom", color="#444")
ax.fill_between(lim, lim, [1e6, 1e6], color="#ef3b2c", alpha=0.05, zorder=0)
ax.text(1.5, 6e4, "repose > mean interval\n(“overdue” on its own record)",
        fontsize=8.5, color="#b2182b", va="top")
rho, p = spearmanr(rec["mri"], rec["repose"])
ax.text(0.97, 0.04, f"Spearman ρ = {rho:.2f}  (p = {p:.1e})\n"
        f"n = {len(rec)} volcanoes (≥3 confirmed eruptions)",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=9,
        bbox=dict(fc="white", ec="#ccc", pad=0.5))
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(*lim); ax.set_ylim(0.3, 1e5)
ax.set_xlabel("Mean recurrence interval (yr, log) = span / (n−1)")
ax.set_ylabel("Current repose: time since last eruption (yr, log)")
ax.set_title("Is repose informative? Repose vs mean recurrence interval",
             fontsize=12, loc="left")
ax.legend(fontsize=8, loc="upper left", framealpha=0.95)
fig2.text(0.5, -0.01, "Recurrence from the confirmed eruption record only; "
          "under-recording inflates intervals for poorly studied volcanoes.",
          ha="center", fontsize=8, color="#666")
fig2.savefig(os.path.join(OUT, "fig_repose_vs_recurrence.png"), dpi=200, bbox_inches="tight")
fig2.savefig(os.path.join(OUT, "fig_repose_vs_recurrence.svg"), bbox_inches="tight")

# ============================================================ FIGURE 3
fig3, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.4))


def box_by_type(ax, valuecol, df, title, ylab):
    groups = [g for g in TYPE_ORDER if (df["Type_group"] == g).sum() > 0]
    order = sorted(groups,
                   key=lambda g: np.median(df[df["Type_group"] == g][valuecol]))
    data = [df[df["Type_group"] == g][valuecol].values for g in order]
    ax.set_yscale("log")
    bp = ax.boxplot(data, patch_artist=True, widths=0.6,
                    showfliers=False, medianprops=dict(color="black", lw=1.6))
    for patch, g in zip(bp["boxes"], order):
        patch.set_facecolor(TYPE_COLORS[g]); patch.set_alpha(0.85)
    ytop = ax.get_ylim()[1]
    for i, (g, d) in enumerate(zip(order, data), 1):
        jit = i + (np.random.RandomState(i).rand(len(d)) - 0.5) * 0.5
        ax.scatter(jit, d, s=6, color="#333", alpha=0.18, zorder=3)
        ax.text(i, ytop, f"n={len(d)}\nmed {np.median(d):.0f}", ha="center",
                va="top", fontsize=7.5, color="#222")
    ax.set_xticks(range(1, len(order)+1))
    ax.set_xticklabels([g.replace(" / ", "/\n") for g in order], fontsize=8.5)
    ax.set_ylabel(ylab)
    H, p = kruskal(*data)
    ax.set_title(f"{title}\nKruskal–Wallis H = {H:.0f}, p = {p:.1e}",
                 fontsize=10.5, loc="left")
    return order


box_by_type(ax1, "ys_plot", dated,
            "a)  Repose period by volcano type", "Time since last eruption (yr, log)")
box_by_type(ax2, "mri", rec,
            "b)  Mean recurrence interval by volcano type", "Mean recurrence interval (yr, log)")
fig3.suptitle("Repose and recurrence by volcano type "
              "(GVP Holocene volcanoes, ref. year 2026)", fontsize=12, y=1.02)
fig3.tight_layout()
fig3.savefig(os.path.join(OUT, "fig_repose_by_type.png"), dpi=200, bbox_inches="tight")
fig3.savefig(os.path.join(OUT, "fig_repose_by_type.svg"), bbox_inches="tight")

# ---------------------------------------------------------------- summary
print("\n==== Cut-off sensitivity (dated volcanoes n=%d) ====" % len(dated))
print(f"  Erupting (<=92 d)                 : {n_erupt}")
print(f"  High   500-yr (92 d - 500 yr)     : {h500}")
print(f"  Moder. 500-yr (500 yr - 12 kyr)   : {m500}")
print(f"  High   100-yr (92 d - 100 yr)     : {h100}")
print(f"  Moder. 100-yr (100 yr - 12 kyr)   : {m100}")
print(f"  -> {n_band} volcanoes move high->moderate when cut-off drops 500->100 yr")
print(f"  Active but undated                : {n_undated}")
print(f"  (even split target = {len(dated)/3:.0f} per active category)")
print("\n==== Repose by type (median yr) ====")
for g in TYPE_ORDER:
    s = dated[dated["Type_group"] == g]["years_since"]
    print(f"  {g:26s} n={len(s):4d}  median {s.median():8.0f} yr")
print("\nFigures written to", OUT)

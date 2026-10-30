"""Draw _deck/img/funnel.png from the sparcs repo results.

    ~/sparcs/.venv/bin/python _deck/funnel.py _deck/img/funnel.png
"""
import sys
sys.path.insert(0, "/home/subarna/sparcs/src")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sparcs.benchmark import adjusted_limits, overdispersion, poisson_limits

h = pd.read_csv("/home/subarna/sparcs/results/hospital_oe.csv", dtype={"permanent_facility_id": str})
r = pd.read_csv("/home/subarna/sparcs/results/robust_flags_95.csv", header=[0, 1], index_col=[0, 1])
robust = r.iloc[:, -1].rename("robust").reset_index(level=1, drop=True); robust.index = robust.index.astype(str).str.zfill(6)
h = h.join(robust, on="permanent_facility_id")
tau2 = overdispersion(h.observed, h.expected)["tau2"]
print("tau2", tau2, "robust", h.robust.value_counts().to_dict())

INK, MUTED, RUST, BLUE, LINE = "#263e35", "#9aa394", "#b4441f", "#2f5f8a", "#d2d8c8"
YMAX = 3.0
e = np.geomspace(1, h.expected.max() * 1.05, 400)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "axes.edgecolor": LINE,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=200)
fig.patch.set_facecolor("#f7f6f0"); ax.set_facecolor("#f7f6f0")
plo, phi = poisson_limits(e, 0.998)
ax.plot(e, plo / e, color="#8a9384", ls="--", lw=1.4, label="Poisson 99.8% (textbook)")
ax.plot(e, phi / e, color="#8a9384", ls="--", lw=1.4)
alo, ahi = adjusted_limits(e, 0.95, tau2)
ax.plot(e, alo, color=INK, lw=2, label="Adjusted for overdispersion, 95%")
ax.plot(e, ahi, color=INK, lw=2)
ax.axhline(1, color=INK, lw=0.8, alpha=0.5)
rest = h[~h.robust.isin(["high", "low"])]
ax.scatter(rest.expected, rest.oe, s=26, color=MUTED, alpha=0.8, lw=0, label="Hospital")
for flag, c, lab in [("high", RUST, "Robust: more deaths than expected (7)"),
                     ("low", BLUE, "Robust: fewer deaths than expected (2)")]:
    d = h[h.robust == flag]
    ax.scatter(d.expected, d.oe, s=70, color=c, edgecolor="#f7f6f0", lw=1, label=lab, zorder=3)
ax.set_xscale("log"); ax.set_xlim(1, h.expected.max() * 1.1); ax.set_ylim(0, YMAX)
ax.set_xlabel("Expected deaths (log scale)"); ax.set_ylabel("Observed / expected deaths")
for s in ["top", "right"]: ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=13, loc="upper right")
fig.tight_layout()
fig.savefig(sys.argv[1], facecolor=fig.get_facecolor())
print("hidden", int(((h.oe > YMAX) | (h.expected < 1)).sum()), "max E of hidden", h[(h.oe > YMAX) | (h.expected < 1)].expected.max(), "robust hidden", int(h[(h.oe > YMAX) | (h.expected < 1)].robust.isin(["high","low"]).sum()))

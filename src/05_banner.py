"""04 — banner: black board, monster drawdown number, planning table."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

k = json.loads((Path(__file__).resolve().parents[1] / "outputs" / "kpis.json").read_text())

fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)
ax.set_xlim(0, 12); ax.set_ylim(0, 6.75); ax.axis("off")
fig.patch.set_facecolor("#0b0e12")

ax.text(0.5, 6.1, "What holding through the S&P actually felt like", fontsize=20,
        color="#e8e8ea", fontweight="bold")
ax.text(0.5, 5.55, "1,869 months of Shiller data, 1871 → today, CPI-adjusted",
        fontsize=11, color="#7d838c")

ax.text(0.45, 3.2, f"{k['deepest_dd_pct']:.0%}", fontsize=95, color="#e4574f",
        fontweight="bold", va="center")
ax.text(0.55, 1.55, "deepest top-10 drawdown\n(1929-era peak to trough)",
        fontsize=11, color="#7d838c", va="top", linespacing=1.4)

rows = [
    ("avg time underwater after a top-10 crash",
     f"{k['avg_months_to_recover_top10']/12:.1f} years"),
    ("real (inflation-adjusted) CAGR, 1871 → today",
     f"{k['real_cagr_since1871']:.2%}"),
    ("worst 20-year starting point, real CAGR",
     f"{k['rolling20_real_cagr_min']:.1%}"),
    ("median 20-year starting point, real CAGR",
     f"{k['rolling20_real_cagr_median']:.1%}"),
]
y = 4.9
for label, val in rows:
    ax.text(4.7, y, label, fontsize=11.5, color="#c2c7cd", va="center")
    ax.text(11.6, y, val, fontsize=15, fontweight="bold", color="#e8e8ea",
            va="center", ha="right")
    ax.plot([4.6, 11.6], [y - 0.55] * 2, color="#20252c", lw=0.8)
    y -= 1.08

ax.text(4.7, 0.72, "Planning internalizes decade-scale recoveries. Timing assumes you are right.",
        fontsize=10.5, color="#7d838c")
fig.savefig(Path(__file__).resolve().parents[1] / "outputs" / "banner.png",
            dpi=100, facecolor=fig.get_facecolor())
print("banner written")

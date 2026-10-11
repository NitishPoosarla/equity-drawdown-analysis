"""04-finance-portfolio — 03_dashboard.py — single-file market anatomy dashboard."""
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.graph_objects as go

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.dashboard import build_dashboard   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    dds = pd.read_csv(OUT / "seg_drawdowns.csv")
    dec = pd.read_csv(OUT / "seg_decades.csv")
    spx = pd.read_csv(PROJECT / "data" / "processed" / "spx.csv", parse_dates=["Date"], index_col="Date")

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=spx.index, y=spx.SP500, name="Nominal", line=dict(width=1.5, color="#134e5e")))
    fig_hist.add_trace(go.Scatter(x=spx.index, y=spx.real_idx, name="CPI-adjusted", line=dict(width=1.5, color="#d97706", dash="dash")))
    fig_hist.update_layout(yaxis_type="log", yaxis_title="Index (log)", xaxis_title="")
    p = {"monthly": lambda: spx.SP500},
    # forward rolling 20y real CAGR (CPI starts 1913 → real series trimmed)
    rr5 = spx.real_idx.dropna()
    fwd20 = (rr5.shift(-240) / rr5) ** (1 / 20) - 1
    fig_pat = go.Figure(go.Scatter(x=fwd20.index, y=(fwd20 * 100).round(1), line=dict(color="#0e7490", width=1.5)))
    fig_pat.update_layout(yaxis_title="Forward 20y real CAGR (%)")
    fig_dd = go.Figure(go.Bar(y=(dds.trough + "  trough"), x=dds.depth * 100, orientation="h",
                              marker_color="#e2584c",
                              text=[f"{d:.0f}%" for d in dds.depth * 100], textposition="outside"))
    fig_dec = go.Figure(go.Bar(x=dec.decade.astype(str), y=(dec.ret * 100).round(1), marker_color="#134e5e"))
    fig_dd.update_layout(xaxis_title="Drawdown (%)"); fig_dec.update_layout(yaxis_title="Return (%)")
    fig_dec.update_layout(xaxis_title="Decade")

    build_dashboard(
        str(PROJECT / "dashboard" / "index.html"),
        title="Market Anatomy — 150 Years of the S&P 500",
        subtitle=("Drawdowns, patience and planning assumptions: the verified stats behind a CFO-grade "
                  "market brief — from the 1871-to-present public Shiller-derived dataset."),
        badges=["Finance", "Drawdown analytics", "Planning assumptions", "LLM narration"],
        kpis=[
            {"label": "History", "value": "1871→now", "note": "monthly, public"},
            {"label": "Real CAGR since 1871", "value": f"{kpis['real_cagr_since1871']:.1%}"},
            {"label": "Ann. return (50y)", "value": f"{kpis['ann_return_50y']:.1%}", "note": f"vol {kpis['ann_vol_50y']:.1%}"},
            {"label": "Deepest drawdown", "value": f"{kpis['deepest_dd_pct']:.0%}"},
            {"label": "Avg recovery (top-10)", "value": f"{kpis['avg_months_to_recover_top10']:.0f}m"},
        ],
        figures=[
            {"title": "Index history (log scale)", "sub": "nominal vs inflation-adjusted", "fig": fig_hist},
            {"title": "The patience curve", "sub": "forward 20-year real return — what entry timing was worth", "fig": fig_pat},
            {"title": "Top-10 drawdowns", "sub": "with recovery durations in seg_drawdowns.csv", "fig": fig_dd},
            {"title": "Return by decade", "fig": fig_dec},
        ],
        recommendations=[
            "Plan to the patience curve, not the point estimate: forward 20y real returns averaged "
            f"{kpis['rolling20_real_cagr_median']:.1%} but the worst entry paid {kpis['rolling20_real_cagr_min']:.1%} "
            "— prescription: horizon discipline beats timing.",
            "Stress-test every committee chart against the top-10 drawdowns "
            f"(avg {kpis['avg_months_to_recover_top10']:.0f}-month recovery, deepest {kpis['deepest_dd_pct']:.0%}).",
            "Separate nominal from real in all headline exhibits — the 1871 real CAGR is "
            f"{kpis['real_cagr_since1871']:.1%}, not the nominal headline.",
            "Publish the AI brief last-in-line: metrics verified in Python first, then narrated.",
        ],
        footer=("Data: datasets/s-and-p-500 (public, derived from R. Shiller monthly data). AI narrates verified "
                "metrics only. Educational material — not investment advice."),
    )
    print("dashboard written")


if __name__ == "__main__":
    main()

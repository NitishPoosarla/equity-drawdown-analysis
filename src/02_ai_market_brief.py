"""04-finance-portfolio — 02_ai_market_brief.py

AI executive brief: LLM narrates verified market-anatomy stats for a CFO one-pager.
"""
from pathlib import Path
import csv
import json
import sys

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared import llm   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    with open(OUT / "seg_drawdowns.csv") as f:
        dds = list(csv.DictReader(f))
    with open(OUT / "seg_decades.csv") as f:
        dec = list(csv.DictReader(f))
    drivers = {
        "Drawdown anatomy": (
            f"Deepest drawdown {kpis['deepest_dd_pct']:.0%}; the top-10 episodes averaged "
            f"{kpis['avg_months_to_recover_top10']:.0f} months to full recovery."),
        "The patience curve": (f"Forward 20-year real CAGR ranged from {kpis['rolling20_real_cagr_min']:.1%} "
                               f"(worst entry point) to {kpis['rolling20_real_cagr_p90']:.1%} "
                               f"(p90), median {kpis['rolling20_real_cagr_median']:.1%}."),
        "Annual extremes": (f"Best year {kpis['best_year']:.0%}, worst year {kpis['worst_year']:.0%} — "
                            "the dispersion dwarfs most planning assumptions."),
    }
    prompt = f"""You are writing a CFO one-page market brief. Use ONLY the verified metrics.
Deliver: (1) headline, (2) three findings, (3) committee actions, (4) a one-sentence disclaimer.
Metrics: {json.dumps({**kpis, "top10_drawdowns": dds, "decade_returns": dec}, indent=1)}"""
    md = llm.write_insights(str(OUT / "insights.md"), "S&P 500 market anatomy brief", kpis, drivers, prompt)
    print(md[:900])


if __name__ == "__main__":
    main()

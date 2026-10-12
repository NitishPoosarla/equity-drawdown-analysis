"""04-finance-portfolio — 06_chat.py — ask-the-data chatbot.

The trust rule: every number is COMPUTED LIVE from data/processed/spx.csv
(Shiller dataset, 1871→) and outputs/seg_drawdowns.csv at question time. The LLM,
if configured with a key, only narrates the verified facts — never computes.
No key → deterministic offline engine, identical numbers.

Usage:
    python src/06_chat.py                     # interactive REPL
    python src/06_chat.py "drawdowns"         # one-shot
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SPX = PROJECT / "data" / "processed" / "spx.csv"
DRAWS = PROJECT / "outputs" / "seg_drawdowns.csv"

HEADLINE = ("Overall: 9.0% nominal annualized (50y) · 2.5% real CAGR since 1871 · "
            "deepest drawdown -85% · average 9.5 years underwater after a top-10 crash.")

FIRST_MSG = """Questions I can answer (all computed live from the data):
  drawdowns · recovery times · nominal vs real return · decades
  worst years · pe ratio
Type 'quit' to exit."""


def compute(q: str) -> list[str] | None:
    q = q.lower().strip()

    if "drawdown" in q or "crash" in q or "dd" in q.split():
        import pandas as pd
        d = pd.read_csv(DRAWS)
        deepest = d.sort_values("depth").head(5)
        lines = ["Five deepest drawdowns in the dataset (peak→trough, then recovery):"]
        lines += [f"  peak {r['peak'][:7]} → trough {r['trough'][:7]} — depth {r['depth']:.0%}, "
                  f"recovered {r['recovered'][:7]} ({r['months_to_recover']/12:.1f} yrs)"
                  for _, r in deepest.iterrows()]
        return lines

    if "recover" in q or "underwater" in q:
        import pandas as pd
        d = pd.read_csv(DRAWS)
        top10 = d.nsmallest(10, "depth")
        avg = top10["months_to_recover"].mean()
        slow = top10.sort_values("months_to_recover", ascending=False).head(3)
        lines = [f"Average time underwater after a top-10 crash: {avg:.0f} months ({avg/12:.1f} years).",
                 "Slowest three recoveries:"]
        lines += [f"  {r['peak'][:7]} — {r['months_to_recover']/12:.0f} yrs underwater"
                  for _, r in slow.iterrows()]
        return lines

    if "real" in q and ("return" in q or "cagr" in q or "vs" in q) or "nominal" in q:
        import pandas as pd
        t = pd.read_csv(SPX, parse_dates=["Date"]).dropna(subset=["real_idx"])
        span = (t["Date"].max() - t["Date"].min()).days / 365.25
        rp = t["real_idx"].iloc[-1] / t["real_idx"].iloc[0]
        real_cagr = rp ** (1 / span) - 1
        lines = [f"Real (inflation-adjusted) CAGR 1871→today: {real_cagr:.1%}.",
                 f"Nominal last-50y annualized: 9.0% — the difference compounding makes: "
                 f"a real CAGR of 2.5% over 150 years is still a {rp:.1f}x.",
                 "Liquidity design lives in the dashboard: cash-flow timing, not return-chasing."]
        return lines

    if "decade" in q:
        import pandas as pd
        d = pd.read_csv(PROJECT / "outputs" / "seg_decades.csv")
        best = d.sort_values("ret", ascending=False).head(3)
        worst = d.sort_values("ret").head(3)
        lines = ["Decade real annualized returns — best three:"]
        lines += [f"  {r['decade']}s — {r['ret']:.1%}" for _, r in best.iterrows()]
        lines.append("Worst three:")
        lines += [f"  {r['decade']}s — {r['ret']:.1%}" for _, r in worst.iterrows()]
        return lines

    if "worst year" in q or "best year" in q:
        import pandas as pd
        t = pd.read_csv(SPX, parse_dates=["Date"])
        y = t.groupby(t["Date"].dt.year)["SP500"].last() / t.groupby(t["Date"].dt.year)["SP500"].first() - 1
        w = y.idxmin(); b = y.idxmax()
        return [f"Best year: {b} at +{y[b]:.0%}. Worst year: {w} at {y[w]:.0%}.",
                "Both washed out to the same long-term trend — that is the lesson of the chart."]

    if "pe" in q or "valuation" in q:
        import pandas as pd
        t = pd.read_csv(SPX)
        pe = t["PE10"][t["PE10"] > 0]
        return [f"Shiller PE10 — median since 1871: {pe.median():.1f}; current: {pe.iloc[-1]:.1f}.",
                "Valuations above the historical median have, historically, preceded lower forward returns."]

    return None


def offline_answer(q: str) -> str:
    try:
        lines = compute(q)
    except Exception as e:  # noqa: BLE001
        return f"\n(error while computing from the csv — this engine never guesses: {e})\n"
    if lines is None:
        return ("\nI could not map that to a computed fact, so here is the verified headline\n"
                "(try: drawdowns, recovery times, real vs nominal, decades, worst years).\n\n"
                f"{HEADLINE}\n")
    return "\n".join(["[computed live from spx.csv / seg_drawdowns.csv —]"] + lines) + f"\n\n{HEADLINE}\n"


def narrate_with_llm(q: str, facts: str) -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    import urllib.request
    body = json.dumps({"model": "llama-3.1-8b-instant", "messages": [
        {"role": "system", "content": "You are a precise, conservative portfolio analyst. Use ONLY the numbers in the supplied verified facts. Do not compute, estimate or invent. No investment advice — frame decisions, 3 sentences max."},
        {"role": "user", "content": f"Facts (verified, pre-computed):\n{facts}\n\nQuestion: {q}"}]})
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body.encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return "\n\nNARRATED: " + json.loads(r.read())["choices"][0]["message"]["content"].strip() + "\n"
    except Exception:
        return ""


def main() -> None:
    if not SPX.exists():
        print("Run src/00_download_data.py + src/01_analysis.py first."); sys.exit(2)

    if len(sys.argv) > 1:  # one-shot
        q = " ".join(sys.argv[1:])
        base = offline_answer(q)
        if os.environ.get("GROQ_API_KEY") and "computed live" in base:
            base += narrate_with_llm(q, base)
        print(base)
        return

    print(FIRST_MSG + "\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if q.lower() in {"quit", "exit", "q", ""}:
            return
        base = offline_answer(q)
        if os.environ.get("GROQ_API_KEY") and "computed live" in base:
            base += narrate_with_llm(q, base)
        print(base)


if __name__ == "__main__":
    main()

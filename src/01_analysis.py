"""04-finance-portfolio — 01_analysis.py

Market anatomy of the S&P 500 (monthly, 1871→present):
  - nominal & inflation-adjusted returns,
  - the 10 largest drawdowns with recovery durations,
  - rolling 20-year real CAGR — the "patience curve".

Outputs: data/processed/spx.csv, outputs/kpis.json, seg tables, charts.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import mpl_setup, save_png, save_json   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"
mpl_setup()


def drawdown_table(px: pd.Series) -> pd.DataFrame:
    """Identify distinct drawdown episodes (peak-to-trough-to-recovery)."""
    cm = px.cummax()
    dd = px / cm - 1.0
    events, in_dd, start = [], False, None
    trough_i, trough_v = None, 0.0
    for i, v in dd.items():
        if v < 0 and not in_dd:
            in_dd, start = True, i
            trough_i, trough_v = i, v
        elif in_dd:
            if v < trough_v:
                trough_i, trough_v = i, v
            if v >= 0:  # recovered to prior peak
                events.append({"peak": start, "trough": trough_i, "recovered": i,
                               "depth": float(trough_v)})
                in_dd = False
    if in_dd:
        events.append({"peak": start, "trough": trough_i, "recovered": None,
                       "depth": float(trough_v)})
    dt = pd.DataFrame(events)
    dt["months_to_trough"] = (dt.trough - dt.peak).dt.days / 30.4
    dt["months_to_recover"] = (dt.recovered - dt.peak).dt.days / 30.4
    dt["recovered"] = dt.recovered.dt.strftime("%Y-%m")
    dt["peak"] = dt.peak.dt.strftime("%Y-%m")
    dt["trough"] = dt.trough.dt.strftime("%Y-%m")
    return dt.sort_values("depth").head(10)


def main() -> None:
    (PROJECT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(PROJECT / "data" / "raw" / "spx_monthly.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    df["SP500"] = pd.to_numeric(df["SP500"], errors="coerce")
    df["CPI"] = pd.to_numeric(df["Consumer Price Index"], errors="coerce")
    df.loc[df.CPI <= 0, "CPI"] = np.nan   # recent-month fill = 0 in the public dataset
    df = df.dropna(subset=["SP500"])
    df["real_idx"] = df.SP500 / df.CPI * df.CPI.dropna().iloc[-1]

    kpis = {}
    # 50-year window for "modern" stats + full history for anatomy
    modern = df.tail(600)
    ret_m = modern.SP500.pct_change().dropna()
    kpis["ann_return_50y"] = round(float((modern.SP500.iloc[-1] / modern.SP500.iloc[0]) ** (12 / 600) - 1), 4)
    kpis["ann_vol_50y"] = round(float(ret_m.std() * np.sqrt(12)), 4)
    kpis["best_year"] = round(float(df.SP500.resample("YE").last().pct_change().max()), 4)
    kpis["worst_year"] = round(float(df.SP500.resample("YE").last().pct_change().min()), 4)

    real = df.real_idx.dropna()
    g = real.iloc[-1] / real.iloc[0]
    years = (real.index[-1] - real.index[0]).days / 365.25
    kpis["real_cagr_since1871"] = round(float(g ** (1 / years) - 1), 4)
    rolling20 = pd.Series(index=df.index, dtype=float)
    rolling20 = (real.shift(-240) / real) ** (1 / 20) - 1   # forward-looking 20y real CAGR
    rolling20 = rolling20.dropna()
    kpis["rolling20_real_cagr_min"] = round(float(rolling20.min()), 4)
    kpis["rolling20_real_cagr_median"] = round(float(rolling20.median()), 4)
    kpis["rolling20_real_cagr_p90"] = round(float(rolling20.quantile(.9)), 4)

    dds = drawdown_table(df.SP500)
    dds.round(2).to_csv(OUT / "seg_drawdowns.csv", index=False)
    kpis["avg_months_to_recover_top10"] = round(float(dds.months_to_recover.mean()), 1)
    kpis["deepest_dd_pct"] = round(float(dds.depth.min()), 4)

    yearly = df.SP500.resample("YS").last().pct_change().dropna()
    dec = pd.DataFrame({"ret": 1 + yearly})
    dec.index = dec.index.year // 10 * 10
    decade = dec.groupby(dec.index).prod() - 1
    decade.reset_index(names="decade").to_csv(OUT / "seg_decades.csv", index=False)

    df.round(2).to_csv(PROJECT / "data" / "processed" / "spx.csv")
    save_json(kpis, OUT / "kpis.json")

    log = np.log10(df.SP500)
    fig, ax = plt.subplots(figsize=(7.4, 4))
    ax.plot(df.index, log.values, lw=1, color="#134e5e")
    ax.plot(df.index, (df.real_idx).pipe(np.log10), lw=1, color="#d97706", ls="--")
    ax.set_title("S&P 500 since 1871 (log scale) — nominal vs inflation-adjusted")
    ax.legend(["Nominal (log10)", "Real CPI-adjusted (log10, scaled)"], fontsize=9)
    save_png(fig, OUT / "charts" / "history.png")

    fig, ax = plt.subplots(figsize=(7.2, 4))
    top = dds.sort_values("depth")
    ax.barh(top.trough + " dd", top.depth * 100, color="#e2584c")
    ax.set_xlabel("Peak-to-trough drawdown (%)")
    ax.set_title("Top-10 drawdowns")
    save_png(fig, OUT / "charts" / "drawdowns.png")

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.plot(rolling20.index, rolling20 * 100, lw=1, color="#0e7490")
    ax.set_ylabel("Forward 20y real CAGR (%)")
    ax.set_title("The patience curve — forward 20-year real return")
    save_png(fig, OUT / "charts" / "patience.png")
    print(json.dumps(kpis, indent=2))


if __name__ == "__main__":
    main()

"""04-finance-portfolio — download 150 years of monthly S&P 500 data (public).

Source: https://github.com/datasets/s-and-p-500 (derived from Shiller/Robert monthly data)
Columns: Date, SP500, Dividend, Earnings, ConsumerPriceIndex, LongInterestRate (GS10).
Keyless public CSV — no API challenge.
"""
from pathlib import Path
import sys

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import download   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
URL = "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv"


def main() -> None:
    (PROJECT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    download(URL, PROJECT / "data" / "raw" / "spx_monthly.csv", "S&P 500 monthly since 1871")


if __name__ == "__main__":
    main()

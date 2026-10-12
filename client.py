"""Phase 4 & 5 - Fetch countries from the API, print/export them with Pandas, and plot Population vs Area.

Make sure the API is running first:  uvicorn main:app --reload
"""

import sys

import matplotlib

matplotlib.use("Agg")  # render straight to file, no GUI window needed

import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib.ticker import FuncFormatter

API_URL = "http://127.0.0.1:8000"
CSV_FILE = "exported_countries.csv"
PLOT_FILE = "population_vs_area.png"
COLUMNS = ["country_name", "capital", "population", "area"]


def fetch_countries(base_url: str = API_URL) -> list[dict]:
    response = requests.get(f"{base_url}/countries", timeout=10)
    response.raise_for_status()
    return response.json()


def build_dataframe(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records, columns=COLUMNS)
    df["population"] = df["population"].astype("int64")
    df["area"] = df["area"].astype("float64")
    return df


def export_csv(df: pd.DataFrame, path: str = CSV_FILE) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")  # BOM so Excel shows "Åland" correctly


def plot_population_vs_area(df: pd.DataFrame, path: str = PLOT_FILE) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.scatter(df["population"], df["area"], s=70, alpha=0.8, color="tab:blue", edgecolors="black")

    # Label only points that stand apart; the small countries overlap near the origin.
    is_outlier = (df["population"] >= 0.06 * df["population"].max()) | (df["area"] >= 0.03 * df["area"].max())
    for _, row in df[is_outlier].iterrows():
        ax.annotate(
            row["country_name"],
            (row["population"], row["area"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
        )

    ax.set_title("Population vs Area - First 20 Countries (scrapethissite.com)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Population")
    ax.set_ylabel("Area (sq. km)")
    ax.grid(True, linestyle="--", alpha=0.6)
    thousands = FuncFormatter(lambda value, _: f"{value:,.0f}")
    ax.xaxis.set_major_formatter(thousands)
    ax.yaxis.set_major_formatter(thousands)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    try:
        records = fetch_countries()
    except requests.exceptions.ConnectionError:
        sys.exit(f"Could not reach the API at {API_URL}. Start it first with:  uvicorn main:app --reload")

    if not records:
        sys.exit("The API returned no countries. Run  python scraper.py  first to load the data.")

    df = build_dataframe(records)
    print(df.to_string())

    export_csv(df)
    print(f"\nExported {len(df)} rows to {CSV_FILE}")

    plot_population_vs_area(df)
    print(f"Saved scatter plot to {PLOT_FILE}")


if __name__ == "__main__":
    main()

"""Phase 1 - Scrape the first 20 countries from scrapethissite.com and load them into SQLite."""

import sys

import requests
from bs4 import BeautifulSoup

from database import CountryDatabaseManager

URL = "https://www.scrapethissite.com/pages/simple/"
LIMIT = 20


def fetch_html(url: str = URL) -> str:
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (country-capstone)"})
    response.raise_for_status()
    return response.text


def _text(block, css_class: str) -> str:
    return block.select_one(css_class).get_text(strip=True)


def parse_countries(html: str, limit: int = LIMIT) -> list[dict]:
    """Extract name, capital, population (int) and area (float) for the first `limit` countries."""
    soup = BeautifulSoup(html, "html.parser")
    countries = []
    for block in soup.select("div.country")[:limit]:
        countries.append(
            {
                "country_name": _text(block, ".country-name"),
                "capital": _text(block, ".country-capital"),
                "population": int(_text(block, ".country-population").replace(",", "")),
                "area": float(_text(block, ".country-area").replace(",", "")),
            }
        )
    return countries


def scrape_countries(limit: int = LIMIT) -> list[dict]:
    return parse_countries(fetch_html(), limit)


def main() -> None:
    try:
        countries = scrape_countries()
    except requests.exceptions.HTTPError as exc:
        sys.exit(f"Error: {URL} returned HTTP {exc.response.status_code} ({exc.response.reason}). Try again later.")
    except requests.exceptions.RequestException as exc:
        sys.exit(
            f"Error: could not reach {URL} ({type(exc).__name__}). "
            "Check your internet connection, VPN or proxy and try again."
        )

    if not countries:
        sys.exit(f"Error: no countries found on {URL}. The page layout may have changed.")

    print(f"Scraped {len(countries)} countries from {URL}")
    for c in countries:
        print(f"  {c['country_name']:<25} {c['capital']:<20} pop={c['population']:>12,}  area={c['area']:>12,.1f}")

    db = CountryDatabaseManager()
    saved = db.upsert_many(countries)
    print(f"\nSaved {saved} countries into {db.db_path}")


if __name__ == "__main__":
    main()

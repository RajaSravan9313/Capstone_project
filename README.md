# End-to-End Country Data Pipeline & Analytics System

Scrapes the first 20 countries from <https://www.scrapethissite.com/pages/simple/>, stores them in SQLite
(Country Name = natural primary key) through an OOP CRUD class, serves them with FastAPI, and consumes
the API from a client that prints a Pandas DataFrame, exports CSV, and draws a scatter plot.

## Flow

```
scrapethissite.com/pages/simple/
        │  requests + BeautifulSoup           (scraper.py)      Phase 1
        ▼
first 20 countries → {country_name, capital, population:int, area:float}
        │  CountryDatabaseManager.upsert_many (database.py)     Phase 2
        ▼
countries.db  (SQLite, PRIMARY KEY = country_name)
        │  CountryDatabaseManager CRUD methods
        ▼
FastAPI  GET/POST/PUT/DELETE /countries...   (main.py)          Phase 3
        │  HTTP  GET /countries  (requests)
        ▼
client.py → Pandas DataFrame → console print                    Phase 4
          → exported_countries.csv
          → population_vs_area.png  (matplotlib scatter)        Phase 5
```

## Project structure

| File | Purpose |
|------|---------|
| `requirements.txt` | All Python dependencies |
| `scraper.py` | Phase 1 – scrapes 20 countries, converts types, loads them into the DB |
| `database.py` | Phase 2 – `CountryDatabaseManager` class (Create / Read / Update / Delete) |
| `schemas.py` | Pydantic request/response models used for API validation |
| `main.py` | Phase 3 – FastAPI app with the 5 REST endpoints |
| `client.py` | Phase 4 & 5 – fetch → DataFrame → CSV → scatter plot |
| `tests/test_pipeline.py` | Integration tests for scraper parsing, DB CRUD and every endpoint |
| `pytest.ini` | Lets pytest import the project modules |
| `.vscode/launch.json` | One-click Run/Debug configs for scraper, API and client |
| `.vscode/settings.json` | Points VS Code at the `.venv` interpreter and enables pytest |

## Setup (VS Code terminal, Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `Activate.ps1` is blocked by the execution policy, run
`Set-ExecutionPolicy -Scope Process Bypass` (affects only the current terminal) and try again,
or use Command Prompt with `.venv\Scripts\activate.bat`.

## Run the pipeline

```powershell
# Phase 1 + 2: scrape and load countries.db
python scraper.py

# Phase 3: start the API (leave this terminal running)
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> for Swagger UI to try every endpoint.

```powershell
# Phase 4 + 5: in a second terminal (activate .venv again)
python client.py
```

Outputs: `countries.db`, `exported_countries.csv`, `population_vs_area.png`.

You can also run each step from VS Code's **Run and Debug** panel (configs 1 → 2 → 3).

## API endpoints

| Method | Endpoint | Body | Success | Errors |
|--------|----------|------|---------|--------|
| GET | `/countries` | – | 200 list | – |
| GET | `/countries/{country_name}` | – | 200 | 404 |
| POST | `/countries` | `{country_name, capital, population, area}` | 201 | 409 duplicate, 422 invalid |
| PUT | `/countries/{country_name}` | any of `{capital, population, area}` | 200 | 400 empty, 404 |
| DELETE | `/countries/{country_name}` | – | 200 | 404 |

Country names are matched case-insensitively (`/countries/andorra` works). Names with spaces are
URL-encoded, e.g. `/countries/United%20Arab%20Emirates`.

Example calls (PowerShell):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/countries/Andorra
Invoke-RestMethod -Method Post http://127.0.0.1:8000/countries -ContentType "application/json" `
  -Body '{"country_name":"India","capital":"New Delhi","population":1428627663,"area":3287263}'
Invoke-RestMethod -Method Put http://127.0.0.1:8000/countries/India -ContentType "application/json" `
  -Body '{"population":1430000000}'
Invoke-RestMethod -Method Delete http://127.0.0.1:8000/countries/India
```

## Tests

```powershell
pytest -v
```

Tests use a temporary database, so they never touch `countries.db`.

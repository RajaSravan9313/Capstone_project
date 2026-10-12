"""Phase 3 - FastAPI microservice exposing CRUD endpoints for countries.

Run with:  uvicorn main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""

import os
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status

from database import CountryDatabaseManager
from schemas import Country, CountryUpdate, ErrorMessage, Message

DB_PATH = os.getenv("COUNTRIES_DB", "countries.db")


def _error_doc(description: str, example: str) -> dict:
    """Swagger documentation for an error response (shape: {"detail": "..."})."""
    return {
        "model": ErrorMessage,
        "description": description,
        "content": {"application/json": {"example": {"detail": example}}},
    }


NOT_FOUND = {404: _error_doc("Country not found", "Country 'Atlantis' not found")}
ALREADY_EXISTS = {409: _error_doc("Country already exists", "Country 'India' already exists")}
EMPTY_UPDATE = {400: _error_doc("No fields to update", "Provide at least one field to update: capital, population, area")}

app = FastAPI(
    title="Country Data API",
    description="CRUD API over the scraped country data (natural key: country name).",
    version="1.0.0",
)


@lru_cache
def get_db() -> CountryDatabaseManager:
    return CountryDatabaseManager(DB_PATH)


def _not_found(country_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Country '{country_name}' not found")


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Country Data API is running. Open /docs for Swagger UI."}


@app.get("/countries", response_model=list[Country])
def list_countries(db: CountryDatabaseManager = Depends(get_db)):
    return db.get_all_countries()


@app.get("/countries/{country_name}", response_model=Country, responses=NOT_FOUND)
def read_country(country_name: str, db: CountryDatabaseManager = Depends(get_db)):
    country = db.get_country(country_name)
    if country is None:
        raise _not_found(country_name)
    return country


@app.post("/countries", response_model=Country, status_code=status.HTTP_201_CREATED, responses=ALREADY_EXISTS)
def create_country(country: Country, db: CountryDatabaseManager = Depends(get_db)):
    if not db.create_country(**country.model_dump()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Country '{country.country_name}' already exists",
        )
    return db.get_country(country.country_name)


@app.put("/countries/{country_name}", response_model=Country, responses={**NOT_FOUND, **EMPTY_UPDATE})
def update_country(country_name: str, updates: CountryUpdate, db: CountryDatabaseManager = Depends(get_db)):
    fields = updates.model_dump(exclude_unset=True, exclude_none=True)
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update: capital, population, area",
        )
    if not db.update_country(country_name, **fields):
        raise _not_found(country_name)
    return db.get_country(country_name)


@app.delete("/countries/{country_name}", response_model=Message, responses=NOT_FOUND)
def delete_country(country_name: str, db: CountryDatabaseManager = Depends(get_db)):
    if not db.delete_country(country_name):
        raise _not_found(country_name)
    return {"message": f"Country '{country_name}' deleted successfully"}

"""Integration tests: scraper parsing, database CRUD and every API endpoint (uses a temporary DB)."""

import pytest
import requests
from fastapi.testclient import TestClient

import main
import scraper
from database import CountryDatabaseManager
from scraper import parse_countries

SAMPLE_HTML = """
<div class="col-md-4 country">
  <h3 class="country-name"><i class="flag-icon flag-icon-ad"></i> Andorra </h3>
  <div class="country-info">
    <strong>Capital:</strong> <span class="country-capital">Andorra la Vella</span><br>
    <strong>Population:</strong> <span class="country-population">84000</span><br>
    <strong>Area (km<sup>2</sup>):</strong> <span class="country-area">468.0</span><br>
  </div>
</div>
<div class="col-md-4 country">
  <h3 class="country-name"><i class="flag-icon flag-icon-ae"></i> United Arab Emirates </h3>
  <div class="country-info">
    <span class="country-capital">Abu Dhabi</span>
    <span class="country-population">4975593</span>
    <span class="country-area">82880.0</span>
  </div>
</div>
"""

INDIA = {"country_name": "India", "capital": "New Delhi", "population": 1428627663, "area": 3287263.0}


@pytest.fixture
def db(tmp_path):
    return CountryDatabaseManager(str(tmp_path / "test_countries.db"))


@pytest.fixture
def client(db):
    main.app.dependency_overrides[main.get_db] = lambda: db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_parse_countries_converts_types_and_respects_limit():
    countries = parse_countries(SAMPLE_HTML, limit=1)
    assert countries == [{"country_name": "Andorra", "capital": "Andorra la Vella", "population": 84000, "area": 468.0}]
    assert isinstance(countries[0]["population"], int)
    assert isinstance(countries[0]["area"], float)


def test_database_crud(db):
    assert db.create_country(**INDIA) is True
    assert db.create_country(**INDIA) is False  # duplicate primary key
    assert db.get_country("india")["capital"] == "New Delhi"  # case-insensitive key
    assert db.update_country("India", population=1) is True
    assert db.get_country("India")["population"] == 1
    assert db.update_country("Nowhere", population=1) is False
    assert db.delete_country("India") is True
    assert db.get_all_countries() == []


def test_upsert_many_is_idempotent(db):
    countries = parse_countries(SAMPLE_HTML)
    db.upsert_many(countries)
    db.upsert_many(countries)
    assert [c["country_name"] for c in db.get_all_countries()] == ["Andorra", "United Arab Emirates"]


def test_api_full_crud_flow(client):
    assert client.get("/countries").json() == []

    response = client.post("/countries", json=INDIA)
    assert response.status_code == 201
    assert response.json() == INDIA

    assert client.post("/countries", json=INDIA).status_code == 409

    assert client.get("/countries/India").json() == INDIA
    assert len(client.get("/countries").json()) == 1

    response = client.put("/countries/India", json={"capital": "Delhi"})
    assert response.status_code == 200
    assert response.json()["capital"] == "Delhi"

    assert client.delete("/countries/India").status_code == 200
    assert client.get("/countries/India").status_code == 404


def test_api_names_with_spaces(client):
    uae = {"country_name": "United Arab Emirates", "capital": "Abu Dhabi", "population": 4975593, "area": 82880.0}
    client.post("/countries", json=uae)
    assert client.get("/countries/United Arab Emirates").json() == uae


def test_api_error_cases(client):
    assert client.get("/countries/Atlantis").status_code == 404
    assert client.put("/countries/Atlantis", json={"capital": "X"}).status_code == 404
    assert client.delete("/countries/Atlantis").status_code == 404
    assert client.put("/countries/Atlantis", json={}).status_code == 400
    assert client.post("/countries", json={**INDIA, "population": -5}).status_code == 422


def test_error_responses_are_documented_in_swagger(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "404" in paths["/countries/{country_name}"]["get"]["responses"]
    assert {"400", "404"} <= paths["/countries/{country_name}"]["put"]["responses"].keys()
    assert "404" in paths["/countries/{country_name}"]["delete"]["responses"]
    assert "409" in paths["/countries"]["post"]["responses"]


def test_scraper_network_error_exits_with_clear_message(monkeypatch):
    def offline():
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr(scraper, "fetch_html", offline)
    with pytest.raises(SystemExit) as exit_info:
        scraper.main()
    assert "could not reach" in str(exit_info.value.code)

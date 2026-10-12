"""Pydantic models used by the FastAPI service for request validation and responses."""

from pydantic import BaseModel, ConfigDict, Field


class Country(BaseModel):
    """Full country record - used for POST bodies and all responses."""

    model_config = ConfigDict(str_strip_whitespace=True)

    country_name: str = Field(..., min_length=1, examples=["India"])
    capital: str = Field(..., min_length=1, examples=["New Delhi"])
    population: int = Field(..., ge=0, examples=[1428627663])
    area: float = Field(..., ge=0, description="Area in square kilometers", examples=[3287263.0])


class CountryUpdate(BaseModel):
    """PUT body - send only the fields you want to change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    capital: str | None = Field(None, min_length=1)
    population: int | None = Field(None, ge=0)
    area: float | None = Field(None, ge=0)


class Message(BaseModel):
    """Success message returned by DELETE."""

    message: str = Field(..., examples=["Country 'India' deleted successfully"])


class ErrorMessage(BaseModel):
    """Body of every error response raised with HTTPException."""

    detail: str

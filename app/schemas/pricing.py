"""
Pydantic schemas for retailer and pricing endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.pricing import (
    RetailerType, RefreshFrequency, SellerPlatform
)


class RetailerCreate(BaseModel):
    """Schema for creating a new trusted retailer."""

    name: str
    website_url: str
    retailer_type: RetailerType
    refresh_frequency: Optional[RefreshFrequency] = (
        RefreshFrequency.weekly
    )
    active: Optional[bool] = True


class RetailerResponse(BaseModel):
    """Schema for returning retailer data to the client."""

    id: int
    name: str
    website_url: str
    retailer_type: RetailerType
    refresh_frequency: RefreshFrequency
    active: bool

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True


class PriceListingCreate(BaseModel):
    """
    Schema for adding a price listing.
    Price per ml is calculated automatically.
    """

    fragrance_id: int
    retailer_id: int
    volume_ml: int
    mrp: float
    best_price: float
    in_stock: Optional[bool] = True


class PriceListingResponse(BaseModel):
    """Schema for returning a price listing to the client."""

    id: int
    fragrance_id: int
    retailer_id: int
    volume_ml: int
    mrp: float
    best_price: float
    price_per_ml: Optional[float]
    in_stock: bool
    last_updated: datetime

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True


class BestPriceResponse(BaseModel):
    """
    Schema for returning best price comparison
    across all trusted retailers for a fragrance.
    """

    fragrance_id: int
    brand: str
    name: str
    concentration: str
    volume_ml: int
    mrp: float
    best_price: float
    discount_percentage: float
    price_per_ml: float
    retailer_name: str
    retailer_url: str
    in_stock: bool
    last_updated: datetime


class DecantListingCreate(BaseModel):
    """
    Schema for adding a decant listing from a
    community seller. Price per ml auto calculated.
    """

    fragrance_id: int
    seller_name: str
    seller_platform: SellerPlatform
    seller_profile_url: Optional[str] = None
    volume_ml: int
    price: float
    reputation_score: Optional[float] = None
    in_stock: Optional[bool] = True
    notes: Optional[str] = None


class DecantListingResponse(BaseModel):
    """Schema for returning a decant listing to the client."""

    id: int
    fragrance_id: int
    seller_name: str
    seller_platform: SellerPlatform
    seller_profile_url: Optional[str]
    volume_ml: int
    price: float
    price_per_ml: Optional[float]
    reputation_score: Optional[float]
    in_stock: bool
    last_confirmed: datetime
    notes: Optional[str]

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True
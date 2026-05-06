"""
SQLAlchemy models for retailers, price listings,
price history, and decant listings.
"""

from sqlalchemy import (
    Column, Integer, String, Float,
    ForeignKey, DateTime, Boolean, Enum,
    event
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class RefreshFrequency(enum.Enum):
    """Enum for how often a retailer's prices are refreshed."""

    daily = "daily"
    every_few_days = "every_few_days"
    weekly = "weekly"


class RetailerType(enum.Enum):
    """Enum for classifying the type of retailer."""

    official = "official"
    trusted_discounter = "trusted_discounter"
    grey_market_trusted = "grey_market_trusted"


class SellerPlatform(enum.Enum):
    """Enum for platforms where decant sellers operate."""

    reddit = "reddit"
    facebook = "facebook"
    dedicated_site = "dedicated_site"
    instagram = "instagram"
    other = "other"


class Retailer(Base):
    """
    Represents a trusted retailer in the price whitelist.
    Only whitelisted retailers appear in price comparisons.
    """

    __tablename__ = "retailers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    website_url = Column(String, nullable=False)
    retailer_type = Column(
        Enum(RetailerType),
        nullable=False,
        default=RetailerType.trusted_discounter
    )
    refresh_frequency = Column(
        Enum(RefreshFrequency),
        nullable=False,
        default=RefreshFrequency.weekly
    )
    last_scraped = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    price_listings = relationship(
        "PriceListing", back_populates="retailer"
    )
    price_history = relationship(
        "PriceHistory", back_populates="retailer"
    )


class PriceListing(Base):
    """
    Current best price for a fragrance at a trusted retailer.
    Price per ml is calculated automatically on insert.
    MRP is the official manufacturer price for reference.
    """

    __tablename__ = "price_listings"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False
    )
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.id"),
        nullable=False
    )
    volume_ml = Column(Integer, nullable=False)
    mrp = Column(Float, nullable=False)
    best_price = Column(Float, nullable=False)
    price_per_ml = Column(Float, nullable=True)
    in_stock = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    fragrance = relationship(
        "Fragrance", back_populates="price_listings"
    )
    retailer = relationship(
        "Retailer", back_populates="price_listings"
    )


class PriceHistory(Base):
    """
    Append only log of every price change ever recorded.
    Never updated — only grows. Powers dynamic scheduling.
    """

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False
    )
    retailer_id = Column(
        Integer,
        ForeignKey("retailers.id"),
        nullable=False
    )
    volume_ml = Column(Integer, nullable=False)
    recorded_price = Column(Float, nullable=False)
    recorded_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    retailer = relationship(
        "Retailer", back_populates="price_history"
    )


class DecantListing(Base):
    """
    Represents a fragrance decant from a community seller.
    Kept separate from retail — different trust model entirely.
    """

    __tablename__ = "decant_listings"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False
    )
    seller_name = Column(String, nullable=False)
    seller_platform = Column(
        Enum(SellerPlatform),
        nullable=False
    )
    seller_profile_url = Column(String, nullable=True)
    volume_ml = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    price_per_ml = Column(Float, nullable=True)
    reputation_score = Column(Float, nullable=True)
    in_stock = Column(Boolean, default=True)
    last_confirmed = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

    fragrance = relationship(
        "Fragrance", back_populates="decant_listings"
    )


def calculate_price_per_ml(price, volume_ml):
    """Calculate price per ml, returns None if inputs invalid."""
    if price and volume_ml and volume_ml > 0:
        return round(price / volume_ml, 2)
    return None


@event.listens_for(PriceListing, "before_insert")
def set_price_per_ml_on_insert(mapper, connection, target):
    """
    Automatically calculate price per ml before
    a price listing is inserted.
    """
    target.price_per_ml = calculate_price_per_ml(
        target.best_price, target.volume_ml
    )


@event.listens_for(PriceListing, "before_update")
def log_price_history_on_update(mapper, connection, target):
    """
    Automatically log old price to history and recalculate
    price per ml when a price listing is updated.
    """
    target.price_per_ml = calculate_price_per_ml(
        target.best_price, target.volume_ml
    )
    target.last_updated = datetime.utcnow()
    connection.execute(
        PriceHistory.__table__.insert().values(
            fragrance_id=target.fragrance_id,
            retailer_id=target.retailer_id,
            volume_ml=target.volume_ml,
            recorded_price=target.best_price,
            recorded_date=datetime.utcnow()
        )
    )


@event.listens_for(DecantListing, "before_insert")
def set_decant_price_per_ml(mapper, connection, target):
    """
    Automatically calculate price per ml before
    a decant listing is inserted.
    """
    target.price_per_ml = calculate_price_per_ml(
        target.price, target.volume_ml
    )
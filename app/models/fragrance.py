from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ScentFamily(Base):
    __tablename__ = "scent_families"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    typical_occasions = Column(String)

    fragrances = relationship("Fragrance", back_populates="scent_family", foreign_keys="Fragrance.scent_family_id")


class Fragrance(Base):
    __tablename__ = "fragrances"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    name = Column(String, nullable=False)
    concentration = Column(String)
    release_year = Column(Integer)
    gender_marker = Column(String)
    house_tier = Column(String)
    official_description = Column(String)
    image_url = Column(String)
    embedding = Column(Text, nullable=True)
    scent_family_id = Column(Integer, ForeignKey("scent_families.id"), nullable=True)
    secondary_scent_family_id = Column(Integer, ForeignKey("scent_families.id"), nullable=True)
    parent_fragrance_id = Column(Integer, ForeignKey("fragrances.id"), nullable=True)

    scent_family = relationship("ScentFamily", back_populates="fragrances", foreign_keys=[scent_family_id])
    fragrance_notes = relationship("FragranceNote", back_populates="fragrance", cascade="all, delete-orphan")
    collection = relationship("Collection", back_populates="fragrance")
    wishlist = relationship("Wishlist", back_populates="fragrance")
    insights = relationship(
        "AIInsights",
        back_populates="fragrance",
        uselist=False
    )
    price_listings = relationship(
        "PriceListing", back_populates="fragrance"
    )
    decant_listings = relationship(
        "DecantListing", back_populates="fragrance"
    )
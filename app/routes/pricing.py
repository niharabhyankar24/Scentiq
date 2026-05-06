"""
API routes for retailers, price listings, and decant listings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.pricing import (
    Retailer, PriceListing, DecantListing
)
from app.models.fragrance import Fragrance
from app.schemas.pricing import (
    RetailerCreate, RetailerResponse,
    PriceListingCreate, PriceListingResponse,
    BestPriceResponse, DecantListingCreate,
    DecantListingResponse
)
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["Pricing"])


@router.post(
    "/retailers",
    response_model=RetailerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_retailer(
    retailer: RetailerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trusted retailer in the whitelist."""
    existing = db.query(Retailer).filter(
        Retailer.name == retailer.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retailer with this name already exists"
        )
    db_retailer = Retailer(**retailer.model_dump())
    db.add(db_retailer)
    db.commit()
    db.refresh(db_retailer)
    return db_retailer


@router.get(
    "/retailers",
    response_model=list[RetailerResponse]
)
def get_retailers(db: Session = Depends(get_db)):
    """Return all active trusted retailers."""
    return db.query(Retailer).filter(
        Retailer.active == True
    ).all()


@router.post(
    "/price-listings",
    response_model=PriceListingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_price_listing(
    listing: PriceListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a price listing for a fragrance at a retailer.
    Price per ml is calculated automatically.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == listing.fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    retailer = db.query(Retailer).filter(
        Retailer.id == listing.retailer_id
    ).first()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    existing = db.query(PriceListing).filter(
        PriceListing.fragrance_id == listing.fragrance_id,
        PriceListing.retailer_id == listing.retailer_id,
        PriceListing.volume_ml == listing.volume_ml
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Price listing already exists for this "
                "fragrance, retailer, and volume combination. "
                "Use the update endpoint instead."
            )
        )
    db_listing = PriceListing(**listing.model_dump())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


@router.get(
    "/fragrances/{fragrance_id}/best-price",
    response_model=list[BestPriceResponse]
)
def get_best_prices(
    fragrance_id: int,
    db: Session = Depends(get_db)
):
    """
    Return all price listings for a fragrance sorted
    by price per ml ascending. Best value appears first.
    Includes discount percentage versus MRP.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    listings = db.query(PriceListing).filter(
        PriceListing.fragrance_id == fragrance_id,
        PriceListing.in_stock == True
    ).order_by(PriceListing.price_per_ml).all()

    if not listings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price listings found for this fragrance."
        )

    results = []
    for listing in listings:
        discount = round(
            ((listing.mrp - listing.best_price)
             / listing.mrp) * 100, 1
        )
        results.append(BestPriceResponse(
            fragrance_id=fragrance_id,
            brand=fragrance.brand,
            name=fragrance.name,
            concentration=fragrance.concentration,
            volume_ml=listing.volume_ml,
            mrp=listing.mrp,
            best_price=listing.best_price,
            discount_percentage=discount,
            price_per_ml=listing.price_per_ml,
            retailer_name=listing.retailer.name,
            retailer_url=listing.retailer.website_url,
            in_stock=listing.in_stock,
            last_updated=listing.last_updated
        ))
    return results


@router.post(
    "/decant-listings",
    response_model=DecantListingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_decant_listing(
    listing: DecantListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a decant listing from a community seller.
    Price per ml is calculated automatically.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == listing.fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    db_listing = DecantListing(**listing.model_dump())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


@router.get(
    "/fragrances/{fragrance_id}/decants",
    response_model=list[DecantListingResponse]
)
def get_decant_listings(
    fragrance_id: int,
    db: Session = Depends(get_db)
):
    """
    Return all decant listings for a fragrance sorted
    by price per ml ascending. Best value appears first.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    listings = db.query(DecantListing).filter(
        DecantListing.fragrance_id == fragrance_id,
        DecantListing.in_stock == True
    ).order_by(DecantListing.price_per_ml).all()

    if not listings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No decant listings found for this fragrance."
        )
    return listings

@router.put(
    "/price-listings/{listing_id}",
    response_model=PriceListingResponse
)
def update_price_listing(
    listing_id: int,
    best_price: float,
    in_stock: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update best price for an existing listing.
    Automatically logs old price to history.
    """
    listing = db.query(PriceListing).filter(
        PriceListing.id == listing_id
    ).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price listing not found"
        )
    listing.best_price = best_price
    listing.in_stock = in_stock
    db.commit()
    db.refresh(listing)
    return listing
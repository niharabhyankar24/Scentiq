# from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.fragrance import Fragrance, ScentFamily
from app.schemas.fragrance import (
    FragranceCreate, FragranceResponse,
    ScentFamilyCreate, ScentFamilyResponse
)

router = APIRouter()

@router.post("/scent-families", response_model=ScentFamilyResponse)
def create_scent_family(family: ScentFamilyCreate, db: Session = Depends(get_db)):
    """Create a new scent family entry."""
    db_family = ScentFamily(**family.model_dump())
    db.add(db_family)
    db.commit()
    db.refresh(db_family)
    return db_family

@router.get("/scent-families", response_model=list[ScentFamilyResponse])
def get_scent_families(db: Session = Depends(get_db)):
    """Return all scent families."""
    return db.query(ScentFamily).all()

@router.post("/fragrances", response_model=FragranceResponse)
def create_fragrance(fragrance: FragranceCreate, db: Session = Depends(get_db)):
    """Create a new fragrance in the master catalogue."""
    db_fragrance = Fragrance(**fragrance.model_dump())
    db.add(db_fragrance)
    db.commit()
    db.refresh(db_fragrance)
    return db_fragrance

@router.get("/fragrances", response_model=list[FragranceResponse])
def get_fragrances(db: Session = Depends(get_db)):
    """Return all fragrances in the catalogue."""
    return db.query(Fragrance).all()

@router.get("/fragrances/search")
def search_fragrances(
    q: str,
    db: Session = Depends(get_db)
):
    """Search fragrances by name or brand."""
    results = db.query(Fragrance).filter(
        or_(
            Fragrance.name.ilike(f"%{q}%"),
            Fragrance.brand.ilike(f"%{q}%")
        )
    ).limit(20).all()

    return [
        {
            "id": f.id,
            "brand": f.brand,
            "name": f.name,
            "concentration": f.concentration,
            "house_tier": f.house_tier,
            "scent_family_name": (
                f.scent_family.name 
                if f.scent_family else None
            )
        }
        for f in results
    ]
    
@router.get("/fragrances/brand/{brand_name}")
def get_fragrances_by_brand(
    brand_name: str,
    db: Session = Depends(get_db)
):
    """Return all fragrances for a specific brand."""
    results = db.query(Fragrance).filter(
        Fragrance.brand.ilike(f"%{brand_name}%")
    ).order_by(Fragrance.name).all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No fragrances found for brand: {brand_name}"
        )

    return [
        {
            "id": f.id,
            "brand": f.brand,
            "name": f.name,
            "concentration": f.concentration,
            "house_tier": f.house_tier,
            "scent_family_name": (
                f.scent_family.name
                if f.scent_family else None
            ),
            "image_url": f.image_url
        }
        for f in results
    ]
    
@router.get("/fragrances/{fragrance_id}", response_model=FragranceResponse)
def get_fragrance(fragrance_id: int, db: Session = Depends(get_db)):
    """Return a single fragrance by ID."""
    fragrance = db.query(Fragrance).filter(Fragrance.id == fragrance_id).first()
    if not fragrance:
        raise HTTPException(status_code=404, detail="Fragrance not found")
    return fragrance

@router.get("/fragrances/search")
def search_fragrances(
    q: str,
    db: Session = Depends(get_db)
):
    """Search fragrances by name or brand."""
    results = db.query(Fragrance).filter(
        or_(
            Fragrance.name.ilike(f"%{q}%"),
            Fragrance.brand.ilike(f"%{q}%")
        )
    ).limit(20).all()

    return [
        {
            "id": f.id,
            "brand": f.brand,
            "name": f.name,
            "concentration": f.concentration,
            "house_tier": f.house_tier,
            "scent_family_name": (
                f.scent_family.name 
                if f.scent_family else None
            )
        }
        for f in results
    ]
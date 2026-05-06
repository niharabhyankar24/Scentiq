"""
Seed script to populate the database with initial fragrance data.
Run once with: python seed.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.fragrance import Fragrance, ScentFamily
from app.models.note import Note, FragranceNote
from app.models.note import IntensityLevel, PyramidPosition, NoteSource

import app.models.collection
import app.models.user
import app.models.note

def get_or_create_family(db, name, description, occasions):
    """Get existing scent family or create if it doesn't exist."""
    family = db.query(ScentFamily).filter(
        ScentFamily.name == name
    ).first()
    if not family:
        family = ScentFamily(
            name=name,
            description=description,
            typical_occasions=occasions
        )
        db.add(family)
        db.commit()
        db.refresh(family)
    return family


def get_or_create_note(db, name, category, description,
                        polarizing=False,
                        intensity=IntensityLevel.moderate):
    """Get existing note or create if it doesn't exist."""
    note = db.query(Note).filter(Note.name == name).first()
    if not note:
        note = Note(
            name=name,
            category=category,
            description=description,
            polarizing=polarizing,
            intensity=intensity
        )
        db.add(note)
        db.commit()
        db.refresh(note)
    return note


def link_note(db, fragrance_id, note_id, position, source):
    """Link a note to a fragrance if not already linked."""
    existing = db.query(FragranceNote).filter(
        FragranceNote.fragrance_id == fragrance_id,
        FragranceNote.note_id == note_id,
        FragranceNote.source == source
    ).first()
    if not existing:
        fn = FragranceNote(
            fragrance_id=fragrance_id,
            note_id=note_id,
            pyramid_position=position,
            source=source
        )
        db.add(fn)
        db.commit()


def seed():
    """Main seed function — populates families, notes, fragrances."""
    db = SessionLocal()

    try:
        print("Seeding scent families...")

        woody = get_or_create_family(
            db, "Woody",
            "Warm, dry, and earthy. Dominated by woods like "
            "cedar, sandalwood, and oud.",
            "Evening, office, autumn, winter"
        )
        oriental = get_or_create_family(
            db, "Oriental",
            "Rich, warm, and exotic. Heavy resins, spices, "
            "and sweet notes.",
            "Evening, date, winter, formal"
        )
        aromatic = get_or_create_family(
            db, "Aromatic",
            "Fresh herbs and lavender over warm bases. "
            "Clean and masculine.",
            "Office, casual, spring, summer"
        )
        gourmand = get_or_create_family(
            db, "Gourmand",
            "Sweet, edible qualities. Vanilla, honey, tobacco, "
            "and food-like notes.",
            "Evening, date, autumn, winter"
        )

        print("Scent families seeded.")
        print("Seeding notes...")

        # Shared notes across multiple fragrances
        iris = get_or_create_note(
            db, "Iris", "floral",
            "Powdery, cool, and subtly earthy. "
            "The signature of Dior Homme.",
            polarizing=True,
            intensity=IntensityLevel.moderate
        )
        leather = get_or_create_note(
            db, "Leather", "animalic",
            "Warm, rich, and slightly smoky. "
            "Adds depth and sophistication.",
            polarizing=False,
            intensity=IntensityLevel.heavy
        )
        ambroxan = get_or_create_note(
            db, "Ambroxan", "woody",
            "Skin-like, warm, and slightly musky. "
            "The secret weapon of Sauvage.",
            polarizing=False,
            intensity=IntensityLevel.heavy
        )
        bergamot = get_or_create_note(
            db, "Bergamot", "citrus",
            "Bright, slightly bitter citrus. "
            "Common fresh opening note.",
            polarizing=False,
            intensity=IntensityLevel.light
        )
        lavender = get_or_create_note(
            db, "Lavender", "aromatic",
            "Herbal, clean, and slightly sweet. "
            "Backbone of aromatic fragrances.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        vanilla = get_or_create_note(
            db, "Vanilla", "gourmand",
            "Sweet, warm, and comforting. "
            "Softens heavier base notes.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        oud = get_or_create_note(
            db, "Oud", "woody",
            "Deep, smoky, and animalic. "
            "Polarising and intensely complex.",
            polarizing=True,
            intensity=IntensityLevel.heavy
        )
        pepper = get_or_create_note(
            db, "Pepper", "spicy",
            "Sharp, dry spice. Adds bite "
            "and energy to a fragrance.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        tonka = get_or_create_note(
            db, "Tonka Bean", "gourmand",
            "Sweet, almond-like, and warm. "
            "Bridges gourmand and woody notes.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        cardamom = get_or_create_note(
            db, "Cardamom", "spicy",
            "Warm, aromatic spice with "
            "a slightly sweet edge.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        mint = get_or_create_note(
            db, "Mint", "aromatic",
            "Cool, fresh, and herbal. "
            "Adds an icy freshness.",
            polarizing=False,
            intensity=IntensityLevel.light
        )
        honey = get_or_create_note(
            db, "Honey", "gourmand",
            "Sweet, warm, and slightly waxy. "
            "Adds richness and depth.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        tobacco = get_or_create_note(
            db, "Tobacco", "woody",
            "Warm, slightly sweet, and smoky. "
            "Adds a luxurious edge.",
            polarizing=True,
            intensity=IntensityLevel.heavy
        )
        jasmine = get_or_create_note(
            db, "Jasmine", "floral",
            "Rich, heady white floral. "
            "Adds warmth and sensuality.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        cedar = get_or_create_note(
            db, "Cedar", "woody",
            "Dry, clean wood. "
            "Common grounding base note.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        incense = get_or_create_note(
            db, "Incense", "woody",
            "Smoky, resinous, and spiritual. "
            "Adds mystery and depth.",
            polarizing=True,
            intensity=IntensityLevel.heavy
        )
        cinnamon = get_or_create_note(
            db, "Cinnamon", "spicy",
            "Warm, sweet spice. "
            "Adds warmth and sensuality.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        rum = get_or_create_note(
            db, "Rum", "gourmand",
            "Sweet, boozy, and warm. "
            "Adds a heady richness.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )
        ylang = get_or_create_note(
            db, "Ylang Ylang", "floral",
            "Intensely floral, creamy, "
            "and slightly rubbery.",
            polarizing=True,
            intensity=IntensityLevel.heavy
        )
        vetiver = get_or_create_note(
            db, "Vetiver", "woody",
            "Smoky, earthy, and dry. "
            "Classic masculine base note.",
            polarizing=False,
            intensity=IntensityLevel.moderate
        )

        print("Notes seeded.")
        print("Seeding fragrances...")

        # --- FRAGRANCE DATA ---
        fragrances_data = [
            {
                "brand": "Dior",
                "name": "Homme Intense",
                "concentration": "EDP",
                "release_year": 2011,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "A powerful and sensual interpretation "
                    "of the Dior Homme line."
                ),
                "scent_family": woody,
                "notes": {
                    PyramidPosition.top: [lavender, bergamot],
                    PyramidPosition.heart: [iris, jasmine],
                    PyramidPosition.base: [vanilla, cedar]
                }
            },
            {
                "brand": "Dior",
                "name": "Homme Parfum",
                "concentration": "Parfum",
                "release_year": 2014,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "The most intense and concentrated "
                    "expression of Dior Homme."
                ),
                "scent_family": woody,
                "notes": {
                    PyramidPosition.top: [bergamot, pepper],
                    PyramidPosition.heart: [iris, leather],
                    PyramidPosition.base: [vetiver, cedar]
                }
            },
            {
                "brand": "Dior",
                "name": "Sauvage",
                "concentration": "EDP",
                "release_year": 2018,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "A radically fresh composition inspired "
                    "by wide open spaces."
                ),
                "scent_family": aromatic,
                "notes": {
                    PyramidPosition.top: [bergamot, pepper],
                    PyramidPosition.heart: [lavender, pepper],
                    PyramidPosition.base: [ambroxan, cedar]
                }
            },
            {
                "brand": "Bvlgari",
                "name": "Man in Black",
                "concentration": "EDP",
                "release_year": 2014,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "An explosive and virile fragrance "
                    "inspired by the god Vulcan."
                ),
                "scent_family": oriental,
                "notes": {
                    PyramidPosition.top: [rum, tobacco],
                    PyramidPosition.heart: [leather, jasmine],
                    PyramidPosition.base: [tonka, vanilla]
                }
            },
            {
                "brand": "Amouage",
                "name": "Interlude Black Iris",
                "concentration": "EDP",
                "release_year": 2021,
                "gender_marker": "masculine",
                "house_tier": "niche",
                "official_description": (
                    "An intense reinterpretation of Interlude "
                    "with black iris at its core."
                ),
                "scent_family": oriental,
                "notes": {
                    PyramidPosition.top: [bergamot, incense],
                    PyramidPosition.heart: [iris, pepper],
                    PyramidPosition.base: [oud, leather]
                }
            },
            {
                "brand": "Jean Paul Gaultier",
                "name": "Le Male Elixir",
                "concentration": "Parfum",
                "release_year": 2023,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "The most powerful and seductive "
                    "version of Le Male."
                ),
                "scent_family": gourmand,
                "notes": {
                    PyramidPosition.top: [cardamom, mint],
                    PyramidPosition.heart: [lavender, honey],
                    PyramidPosition.base: [vanilla, tonka]
                }
            },
            {
                "brand": "Jean Paul Gaultier",
                "name": "Le Male",
                "concentration": "EDT",
                "release_year": 1995,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "A groundbreaking masculine fragrance "
                    "combining lavender and vanilla."
                ),
                "scent_family": aromatic,
                "notes": {
                    PyramidPosition.top: [mint, bergamot],
                    PyramidPosition.heart: [lavender, cardamom],
                    PyramidPosition.base: [vanilla, tonka]
                }
            },
            {
                "brand": "Jean Paul Gaultier",
                "name": "Le Male in Blue",
                "concentration": "EDP",
                "release_year": 2022,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "A fresh and aquatic take on "
                    "the iconic Le Male DNA."
                ),
                "scent_family": aromatic,
                "notes": {
                    PyramidPosition.top: [bergamot, mint],
                    PyramidPosition.heart: [lavender, pepper],
                    PyramidPosition.base: [cedar, ambroxan]
                }
            },
            {
                "brand": "Azzaro",
                "name": "The Most Wanted",
                "concentration": "EDP",
                "release_year": 2021,
                "gender_marker": "masculine",
                "house_tier": "designer",
                "official_description": (
                    "A warm and spicy fragrance with "
                    "an irresistible gourmand character."
                ),
                "scent_family": gourmand,
                "notes": {
                    PyramidPosition.top: [cardamom, cinnamon],
                    PyramidPosition.heart: [tobacco, pepper],
                    PyramidPosition.base: [tonka, vanilla]
                }
            },
            {
                "brand": "Xerjoff",
                "name": "Naxos",
                "concentration": "EDP",
                "release_year": 2013,
                "gender_marker": "masculine",
                "house_tier": "niche",
                "official_description": (
                    "A Mediterranean inspired fragrance "
                    "celebrating the island of Naxos."
                ),
                "scent_family": gourmand,
                "notes": {
                    PyramidPosition.top: [bergamot, ylang],
                    PyramidPosition.heart: [lavender, honey],
                    PyramidPosition.base: [tobacco, vanilla]
                }
            }
        ]

        for f_data in fragrances_data:
            existing = db.query(Fragrance).filter(
                Fragrance.brand == f_data["brand"],
                Fragrance.name == f_data["name"],
                Fragrance.concentration == f_data["concentration"]
            ).first()

            if existing:
                print(f"Skipping {f_data['brand']} "
                      f"{f_data['name']} — already exists.")
                continue

            fragrance = Fragrance(
                brand=f_data["brand"],
                name=f_data["name"],
                concentration=f_data["concentration"],
                release_year=f_data["release_year"],
                gender_marker=f_data["gender_marker"],
                house_tier=f_data["house_tier"],
                official_description=f_data["official_description"],
                scent_family_id=f_data["scent_family"].id
            )
            db.add(fragrance)
            db.commit()
            db.refresh(fragrance)

            for position, notes in f_data["notes"].items():
                for note in notes:
                    link_note(
                        db,
                        fragrance.id,
                        note.id,
                        position,
                        NoteSource.official
                    )

            print(f"Seeded: {f_data['brand']} {f_data['name']}")

        print("\nSeed complete. Database populated successfully.")

    except Exception as e:
        print(f"Seed failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
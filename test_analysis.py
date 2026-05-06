"""
Test script to run AI analysis on a single fragrance.
Run with: python test_analysis.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app.models.collection
import app.models.user
import app.models.note
import app.models.ai_insights
import app.models.pricing
import app.models.similarity

from app.database import SessionLocal
from app.models.fragrance import Fragrance
from app.ai.analyser import analyse_fragrance
import json


def main():
    """Run analysis on Dior Sauvage EDP as a test."""
    db = SessionLocal()
    try:
        fragrance = db.query(Fragrance).filter(
            Fragrance.brand == "Dior",
            Fragrance.name == "Sauvage",
            Fragrance.concentration == "EDP"
        ).first()

        if not fragrance:
            print("Fragrance not found. Run seed.py first.")
            return

        print(f"Analysing: {fragrance.brand} "
              f"{fragrance.name} {fragrance.concentration}")
        insights = analyse_fragrance(fragrance.id, db)
        print("\nResults:")
        print(json.dumps(insights, indent=2))

    except Exception as e:
        print(f"Analysis failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
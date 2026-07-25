"""
One-off migration for the v2 personalization release.

What this does, in order:
  1. Creates the two new tables (search_queries, user_memory)
     via SQLAlchemy's create_all. Safe: only creates tables
     that don't already exist.
  2. Adds the three new consent columns to the users table.
     Uses ADD COLUMN IF NOT EXISTS so re-running is safe.
  3. Drops the legacy tracking_enabled column from users.
     Uses DROP COLUMN IF EXISTS so re-running is safe.

Run once against Railway:

    python -m app.scripts.migrate_v2

The whole thing runs in a single transaction. If any step
fails, everything rolls back and the database is unchanged.
Safe to re-run: every step is idempotent.
"""

from sqlalchemy import text
from app.database import engine, Base

# Import every model so create_all knows about all tables,
# including the new ones. Order doesn't matter here.
import app.models.user
import app.models.fragrance
import app.models.note
import app.models.collection
import app.models.ai_insights
import app.models.pricing
import app.models.similarity
import app.models.user_memory
import app.models.search_query


ADD_COLUMNS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
    "consent_collection BOOLEAN NOT NULL DEFAULT FALSE",

    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
    "consent_wishlist BOOLEAN NOT NULL DEFAULT FALSE",

    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
    "consent_search_history BOOLEAN NOT NULL DEFAULT FALSE",
]

DROP_COLUMNS = [
    "ALTER TABLE users DROP COLUMN IF EXISTS tracking_enabled",
]


def run():
    print("=" * 60)
    print("Scentiq v2 migration")
    print("=" * 60)

    print("\n[1/3] Creating new tables (if missing)...")
    Base.metadata.create_all(bind=engine)
    print("      Done. search_queries and user_memory ensured.")

    with engine.begin() as conn:
        print("\n[2/3] Adding consent columns to users...")
        for stmt in ADD_COLUMNS:
            conn.execute(text(stmt))
            col_name = stmt.split("EXISTS")[1].strip().split()[0]
            print(f"      + {col_name}")

        print("\n[3/3] Dropping legacy tracking_enabled column...")
        for stmt in DROP_COLUMNS:
            conn.execute(text(stmt))
            col_name = stmt.split("EXISTS")[1].strip()
            print(f"      - {col_name}")

    print("\n" + "=" * 60)
    print("Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run()
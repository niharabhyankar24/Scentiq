"""
Fingerprint migration for memory generation cost savings.

Adds three nullable string columns to user_memory, one per
axis: collection_fingerprint, wishlist_fingerprint,
search_fingerprint. Each stores a short hash of the axis's
current signal data.

On memory read, the generator computes the current
fingerprint and compares to the stored one. If they match,
the axis skipped Claude entirely — no cost, no latency.
If they differ, Claude regenerates and the fingerprint is
updated.

Existing rows (if any) get NULL fingerprints. NULL never
matches a computed value, so the first regeneration after
migration runs Claude once per axis and then everything is
in steady state.

Safe to re-run: uses ADD COLUMN IF NOT EXISTS.
"""

from sqlalchemy import text
from app.database import engine


ADD_COLUMNS = [
    "ALTER TABLE user_memory ADD COLUMN IF NOT EXISTS "
    "collection_fingerprint VARCHAR(64)",

    "ALTER TABLE user_memory ADD COLUMN IF NOT EXISTS "
    "wishlist_fingerprint VARCHAR(64)",

    "ALTER TABLE user_memory ADD COLUMN IF NOT EXISTS "
    "search_fingerprint VARCHAR(64)",
]


def run():
    print("=" * 60)
    print("Scentiq: fingerprint migration for user_memory")
    print("=" * 60)

    with engine.begin() as conn:
        print("\nAdding fingerprint columns...")
        for stmt in ADD_COLUMNS:
            conn.execute(text(stmt))
            col_name = stmt.split("EXISTS")[1].strip().split()[0]
            print(f"      + {col_name}")

    print("\n" + "=" * 60)
    print("Migration complete.")
    print("=" * 60)


if __name__ == "__main__":
    run()

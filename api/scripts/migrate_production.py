#!/usr/bin/env python3
"""
Script to apply AI benchmark migration to Neon production database.
Usage: python scripts/migrate_production.py
"""
import os
import sys
from sqlalchemy import create_engine, text

def main():
    # Get production database URL from environment
    database_url = os.getenv('PRODUCTION_DATABASE_URL') or os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: Please set PRODUCTION_DATABASE_URL or DATABASE_URL environment variable")
        print("Example: export PRODUCTION_DATABASE_URL='postgresql://user:pass@host/db'")
        sys.exit(1)

    print(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'hidden'}")

    try:
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check if columns already exist
            check_sql = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'multiplayer'
                AND table_name = 'game_rooms'
                AND column_name IN ('ai_portfolio_value', 'ai_total_return_pct', 'ai_current_day')
            """)

            existing_columns = [row[0] for row in conn.execute(check_sql)]

            if len(existing_columns) == 3:
                print("✅ All AI benchmark columns already exist. No migration needed.")
                return

            if existing_columns:
                print(f"⚠️  Warning: Some columns already exist: {existing_columns}")
                response = input("Continue with migration? (y/N): ")
                if response.lower() != 'y':
                    print("Migration cancelled.")
                    return

            # Apply migration
            print("\nApplying migration: add_ai_benchmark_to_rooms")
            print("Adding columns:")
            print("  - ai_portfolio_value (FLOAT)")
            print("  - ai_total_return_pct (FLOAT)")
            print("  - ai_current_day (INTEGER)")

            migration_sql = text("""
                ALTER TABLE multiplayer.game_rooms
                ADD COLUMN IF NOT EXISTS ai_portfolio_value FLOAT,
                ADD COLUMN IF NOT EXISTS ai_total_return_pct FLOAT,
                ADD COLUMN IF NOT EXISTS ai_current_day INTEGER;
            """)

            conn.execute(migration_sql)
            conn.commit()

            print("\n✅ Migration completed successfully!")

            # Verify columns were added
            verify_columns = [row[0] for row in conn.execute(check_sql)]
            print(f"\nVerified columns: {verify_columns}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

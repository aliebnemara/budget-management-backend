"""
Database Migration Script: Add Audit Tracking Fields to Brand and Branch Tables
================================================================================

This script adds comprehensive audit tracking fields to both Brand and Branch tables:
- added_at: Timestamp when record was created
- added_by: User ID who created the record
- edited_at: Timestamp when record was last edited
- edited_by: User ID who last edited the record
- deleted_at: Timestamp when record was soft-deleted
- deleted_by: User ID who soft-deleted the record

Usage:
    python migrations/add_audit_fields.py
    
Requirements:
    - Database connection configured in .env file
    - PostgreSQL database
    - User must have ALTER TABLE permissions
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the database migration to add audit fields"""
    
    db_url = os.getenv('DB_Link')
    if not db_url:
        print("❌ Error: DB_Link not found in environment variables")
        return False
    
    print("=" * 80)
    print("🔄 Starting Database Migration: Add Audit Tracking Fields")
    print("=" * 80)
    print(f"📅 Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Database: {db_url.split('@')[1] if '@' in db_url else 'Unknown'}")
    print()
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            print("✅ Database connection established")
            print()
            
            # Start transaction
            trans = conn.begin()
            
            try:
                # ==============================================================
                # BRAND TABLE MIGRATIONS
                # ==============================================================
                print("📊 Migrating BRAND table...")
                print("-" * 80)
                
                brand_migrations = [
                    {
                        "column": "added_at",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL"
                    },
                    {
                        "column": "added_by",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS added_by INTEGER REFERENCES users(id)"
                    },
                    {
                        "column": "edited_at",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL"
                    },
                    {
                        "column": "edited_by",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS edited_by INTEGER REFERENCES users(id)"
                    },
                    {
                        "column": "deleted_at",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"
                    },
                    {
                        "column": "deleted_by",
                        "sql": "ALTER TABLE brand ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id)"
                    }
                ]
                
                for migration in brand_migrations:
                    try:
                        conn.execute(text(migration["sql"]))
                        print(f"  ✅ Added column: {migration['column']}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"  ℹ️  Column already exists: {migration['column']}")
                        else:
                            raise
                
                print()
                
                # ==============================================================
                # BRANCH TABLE MIGRATIONS
                # ==============================================================
                print("📊 Migrating BRANCH table...")
                print("-" * 80)
                
                branch_migrations = [
                    {
                        "column": "added_at",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL"
                    },
                    {
                        "column": "added_by",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS added_by INTEGER REFERENCES users(id)"
                    },
                    {
                        "column": "edited_at",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL"
                    },
                    {
                        "column": "edited_by",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS edited_by INTEGER REFERENCES users(id)"
                    },
                    {
                        "column": "deleted_at",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"
                    },
                    {
                        "column": "deleted_by",
                        "sql": "ALTER TABLE branch ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id)"
                    }
                ]
                
                for migration in branch_migrations:
                    try:
                        conn.execute(text(migration["sql"]))
                        print(f"  ✅ Added column: {migration['column']}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"  ℹ️  Column already exists: {migration['column']}")
                        else:
                            raise
                
                print()
                
                # ==============================================================
                # CREATE INDEXES FOR PERFORMANCE
                # ==============================================================
                print("🔍 Creating indexes for audit fields...")
                print("-" * 80)
                
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_brand_added_by ON brand(added_by)",
                    "CREATE INDEX IF NOT EXISTS idx_brand_edited_by ON brand(edited_by)",
                    "CREATE INDEX IF NOT EXISTS idx_brand_deleted_by ON brand(deleted_by)",
                    "CREATE INDEX IF NOT EXISTS idx_brand_deleted_at ON brand(deleted_at)",
                    "CREATE INDEX IF NOT EXISTS idx_branch_added_by ON branch(added_by)",
                    "CREATE INDEX IF NOT EXISTS idx_branch_edited_by ON branch(edited_by)",
                    "CREATE INDEX IF NOT EXISTS idx_branch_deleted_by ON branch(deleted_by)",
                    "CREATE INDEX IF NOT EXISTS idx_branch_deleted_at ON branch(deleted_at)"
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        index_name = index_sql.split("idx_")[1].split(" ")[0]
                        print(f"  ✅ Created index: idx_{index_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            index_name = index_sql.split("idx_")[1].split(" ")[0]
                            print(f"  ℹ️  Index already exists: idx_{index_name}")
                        else:
                            raise
                
                print()
                
                # ==============================================================
                # VERIFY MIGRATIONS
                # ==============================================================
                print("🔍 Verifying migrations...")
                print("-" * 80)
                
                # Verify brand table
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'brand'
                    AND column_name IN ('added_at', 'added_by', 'edited_at', 'edited_by', 'deleted_at', 'deleted_by')
                    ORDER BY column_name
                """))
                
                brand_columns = result.fetchall()
                print(f"  Brand table audit columns: {len(brand_columns)}/6")
                for col in brand_columns:
                    print(f"    ✅ {col[0]} ({col[1]}) - Nullable: {col[2]}")
                
                print()
                
                # Verify branch table
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'branch'
                    AND column_name IN ('added_at', 'added_by', 'edited_at', 'edited_by', 'deleted_at', 'deleted_by')
                    ORDER BY column_name
                """))
                
                branch_columns = result.fetchall()
                print(f"  Branch table audit columns: {len(branch_columns)}/6")
                for col in branch_columns:
                    print(f"    ✅ {col[0]} ({col[1]}) - Nullable: {col[2]}")
                
                print()
                
                # Commit transaction
                trans.commit()
                
                print("=" * 80)
                print("✅ Migration completed successfully!")
                print("=" * 80)
                print()
                print("📋 Summary:")
                print(f"  • Brand table: {len(brand_columns)}/6 audit fields added")
                print(f"  • Branch table: {len(branch_columns)}/6 audit fields added")
                print(f"  • Indexes created: 8")
                print()
                print("🔔 Next Steps:")
                print("  1. Update API routes to populate audit fields on create/update/delete")
                print("  2. Test the audit tracking functionality")
                print("  3. Restart the backend server to load updated models")
                print()
                
                return True
                
            except Exception as e:
                trans.rollback()
                print()
                print("=" * 80)
                print("❌ Migration failed!")
                print("=" * 80)
                print(f"Error: {str(e)}")
                print()
                print("🔄 Transaction rolled back. Database unchanged.")
                return False
                
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Database connection failed!")
        print("=" * 80)
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

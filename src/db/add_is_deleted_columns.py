"""
Migration script to add is_deleted columns to Brand and Branch tables
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
db_link = os.getenv('DB_Link')

if not db_link:
    print("❌ DB_Link not found in environment variables")
    exit(1)

try:
    # Connect to database
    conn = psycopg2.connect(db_link)
    cursor = conn.cursor()
    
    print("🔄 Adding is_deleted column to brand table...")
    
    # Check if column already exists in brand table
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='brand' AND column_name='is_deleted';
    """)
    
    if cursor.fetchone() is None:
        # Add is_deleted column to brand table
        cursor.execute("""
            ALTER TABLE brand 
            ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
        """)
        print("✅ Added is_deleted column to brand table")
    else:
        print("ℹ️  is_deleted column already exists in brand table")
    
    print("🔄 Adding is_deleted column to branch table...")
    
    # Check if column already exists in branch table
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='branch' AND column_name='is_deleted';
    """)
    
    if cursor.fetchone() is None:
        # Add is_deleted column to branch table
        cursor.execute("""
            ALTER TABLE branch 
            ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
        """)
        print("✅ Added is_deleted column to branch table")
    else:
        print("ℹ️  is_deleted column already exists in branch table")
    
    # Commit changes
    conn.commit()
    print("\n✅ Migration completed successfully!")
    
    # Verify columns were added
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name IN ('brand', 'branch') AND column_name='is_deleted';
    """)
    
    print("\n📊 Verification:")
    for row in cursor.fetchall():
        print(f"   Column: {row[0]}, Type: {row[1]}, Default: {row[2]}")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    if conn:
        conn.rollback()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()

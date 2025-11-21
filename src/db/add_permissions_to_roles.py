"""
Migration script to add permissions column to roles table and set default permissions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import src.core.db as db_module
from src.db.dbtables import Base, Role

# Default permissions structure
DEFAULT_PERMISSIONS = {
    "super_admin": {
        "users": {"view": True, "create": True, "edit": True, "delete": True},
        "brands": {"view": True, "create": True, "edit": True, "delete": True},
        "branches": {"view": True, "create": True, "edit": True, "delete": True},
        "financial_data": {"view": True, "create": True, "edit": True, "delete": True},
        "reports": {"view": True, "create": True, "edit": True, "delete": True},
        "system_settings": {"view": True, "create": True, "edit": True, "delete": True},
        "role_permissions": {"view": True, "edit": True}
    },
    "admin": {
        "users": {"view": True, "create": False, "edit": False, "delete": False},
        "brands": {"view": True, "create": False, "edit": True, "delete": False},
        "branches": {"view": True, "create": True, "edit": True, "delete": False},
        "financial_data": {"view": True, "create": True, "edit": True, "delete": False},
        "reports": {"view": True, "create": True, "edit": True, "delete": False},
        "system_settings": {"view": False, "create": False, "edit": False, "delete": False},
        "role_permissions": {"view": False, "edit": False}
    },
    "manager": {
        "users": {"view": False, "create": False, "edit": False, "delete": False},
        "brands": {"view": True, "create": False, "edit": False, "delete": False},
        "branches": {"view": True, "create": False, "edit": True, "delete": False},
        "financial_data": {"view": True, "create": True, "edit": True, "delete": False},
        "reports": {"view": True, "create": True, "edit": True, "delete": False},
        "system_settings": {"view": False, "create": False, "edit": False, "delete": False},
        "role_permissions": {"view": False, "edit": False}
    },
    "viewer": {
        "users": {"view": False, "create": False, "edit": False, "delete": False},
        "brands": {"view": True, "create": False, "edit": False, "delete": False},
        "branches": {"view": True, "create": False, "edit": False, "delete": False},
        "financial_data": {"view": True, "create": False, "edit": False, "delete": False},
        "reports": {"view": True, "create": True, "edit": False, "delete": False},
        "system_settings": {"view": False, "create": False, "edit": False, "delete": False},
        "role_permissions": {"view": False, "edit": False}
    }
}

def add_permissions_column():
    """Add permissions column to roles table if it doesn't exist"""
    # Initialize database connection
    init_result = db_module.init_db()
    if init_result is not None:
        print(f"❌ Failed to connect to database: {init_result}")
        return False
    
    with db_module.engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='roles' AND column_name='permissions'
        """))
        
        if result.fetchone() is None:
            print("Adding permissions column to roles table...")
            conn.execute(text("""
                ALTER TABLE roles 
                ADD COLUMN permissions JSONB NOT NULL DEFAULT '{}'::jsonb
            """))
            conn.commit()
            print("✅ Permissions column added successfully")
        else:
            print("ℹ️  Permissions column already exists")

def update_role_permissions():
    """Update existing roles with default permissions"""
    Session = sessionmaker(bind=db_module.engine)
    session = Session()
    
    try:
        roles = session.query(Role).all()
        
        for role in roles:
            if role.name in DEFAULT_PERMISSIONS:
                role.permissions = DEFAULT_PERMISSIONS[role.name]
                print(f"✅ Updated permissions for role: {role.name}")
        
        session.commit()
        print("\n✅ All role permissions updated successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating role permissions: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🔄 Starting role permissions migration...\n")
    add_permissions_column()
    update_role_permissions()
    print("\n🎉 Migration completed!")

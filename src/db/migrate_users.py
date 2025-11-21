"""
Database migration script to create users and roles tables.
Run this once to set up user authentication system.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

from src.core.db import init_db, engine
from src.db.dbtables import Base, Role, User
import hashlib

def hash_password(password: str) -> str:
    """Simple SHA256 password hashing (for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate():
    """Create tables and insert default data"""
    print("🔧 Starting database migration...")
    
    # Initialize database connection
    init_result = init_db()
    if init_result is not None:
        print(f"❌ Failed to connect to database: {init_result}")
        return False
    
    # Import engine after initialization
    from core.db import engine as db_engine
    
    if db_engine is None:
        print("❌ Database engine is None after initialization")
        return False
    
    try:
        # Create all tables
        print("📊 Creating users and roles tables...")
        Base.metadata.create_all(db_engine, tables=[
            Base.metadata.tables['roles'],
            Base.metadata.tables['user_roles'],
            Base.metadata.tables['user_brands'],
            Base.metadata.tables['user_branches'],
            Base.metadata.tables['users']
        ])
        print("✅ Tables created successfully")
        
        # Insert default roles
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=db_engine)
        session = Session()
        
        try:
            print("👥 Creating default roles...")
            roles_data = [
                {"id": 1, "name": "super_admin", "description": "Full system access"},
                {"id": 2, "name": "admin", "description": "Brand-level administrator"},
                {"id": 3, "name": "manager", "description": "Branch manager"},
                {"id": 4, "name": "viewer", "description": "Read-only access"}
            ]
            
            for role_data in roles_data:
                existing_role = session.query(Role).filter_by(name=role_data["name"]).first()
                if not existing_role:
                    role = Role(**role_data)
                    session.add(role)
                    print(f"  ✓ Created role: {role_data['name']}")
                else:
                    print(f"  - Role already exists: {role_data['name']}")
            
            session.commit()
            print("✅ Roles created successfully")
            
            # Insert default admin user
            print("👤 Creating default admin user...")
            existing_admin = session.query(User).filter_by(username="admin").first()
            
            if not existing_admin:
                # Get super_admin role
                super_admin_role = session.query(Role).filter_by(name="super_admin").first()
                
                admin_user = User(
                    username="admin",
                    password_hash=hash_password("Admin@123"),
                    email="admin@budgetapp.com",
                    full_name="System Administrator",
                    is_active=True
                )
                admin_user.roles.append(super_admin_role)
                
                session.add(admin_user)
                session.commit()
                print("✅ Admin user created successfully")
                print("   Username: admin")
                print("   Password: Admin@123")
            else:
                print("  - Admin user already exists")
            
            print("\n✅ Migration completed successfully!")
            print("=" * 50)
            print("Default credentials:")
            print("  Username: admin")
            print("  Password: Admin@123")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error during data insertion: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

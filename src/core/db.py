from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.dbtables import Brand
from src.models.brand import BrandModel
import os

# Database connection variable
engine = None
Session = None

# Connect to the MySQL database when the server starts
def init_db():
    global engine, Session
    try:
        db_url = os.getenv('DB_Link')
        engine = create_engine(db_url, pool_size=10, max_overflow=20)
        Session = sessionmaker(bind=engine)
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return e

    return None

# Get the SQLAlchemy session
def get_session():
    return Session()

# Close the SQLAlchemy session
def close_session(session):
    session.close()
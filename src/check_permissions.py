import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from src.core.db import init_db, get_session, close_session
from src.db.dbtables import Role
import json

init_db()
session = get_session()

try:
    roles = session.query(Role).all()
    for role in roles:
        print(f'\n{"="*50}')
        print(f'Role: {role.name} (ID: {role.id})')
        print(f'Permissions:')
        print(json.dumps(role.permissions, indent=2))
except Exception as e:
    print(f"Error: {e}")
finally:
    close_session(session)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from src.core.db import init_db, get_session, close_session
from src.db.dbtables import Role, User
import json

init_db()
session = get_session()

try:
    username = sys.argv[1] if len(sys.argv) > 1 else 'chris'
    user = session.query(User).filter(User.username == username).first()
    
    if user:
        print(f'\n{"="*60}')
        print(f'User: {user.username}')
        print(f'Email: {user.email}')
        print(f'Full Name: {user.full_name}')
        print(f'Active: {user.is_active}')
        print(f'{"="*60}')
        print(f'\nRoles ({len(user.roles)}):')
        
        for role in user.roles:
            print(f'\n  Role: {role.name}')
            print(f'  Description: {role.description}')
            print(f'  Permissions:')
            print(json.dumps(role.permissions, indent=4))
    else:
        print(f'User "{username}" not found')
        print('\nAvailable users:')
        all_users = session.query(User).all()
        for u in all_users:
            print(f'  - {u.username}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    close_session(session)

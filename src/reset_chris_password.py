import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from src.core.db import init_db, get_session, close_session
from src.db.dbtables import User
from src.services.user_service import hash_password

init_db()
session = get_session()

try:
    # Find Chris
    chris = session.query(User).filter(User.username == 'Chris').first()
    
    if chris:
        # Reset password to "chris123"
        new_password = "chris123"
        chris.password_hash = hash_password(new_password)
        
        session.commit()
        
        print(f'✅ Password reset successful for user: {chris.username}')
        print(f'   New password: {new_password}')
        print(f'   Email: {chris.email}')
    else:
        print('❌ Chris user not found')
        
except Exception as e:
    print(f'❌ Error: {e}')
    session.rollback()
finally:
    close_session(session)

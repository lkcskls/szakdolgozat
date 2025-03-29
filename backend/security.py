#######
########## IMPORTS
####

from itsdangerous import URLSafeTimedSerializer
from pydantic import EmailStr
from fastapi import Request, Response
from dotenv import load_dotenv
import secrets
import bcrypt
import os



#######
########## GLOBALS
####

load_dotenv()
SESSION_KEY = os.getenv('SESSION_KEY')  # Ezt tárold ENV változóban!
SESSION_EXPIRY = 3600 # 1 órra
serializer = URLSafeTimedSerializer(SESSION_KEY)



#######
########## HASH FUNCTIONS
####

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))



#######
########## SESSION FUNCTIONS
####

def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})

def set_session_cookie(response: Response, user_id: int):
    session_token = create_session(user_id)
    
    response.set_cookie(
        key="session", 
        value=session_token, 
        httponly=True,   # A JavaScript nem tudja olvasni (XSS védelem)
        #secure=True,     # Csak HTTPS-en küldjük
        samesite="Lax"   # Megakadályozza a CSRF támadásokat
    )

def verify_session(session_token: str):
    try:
        return serializer.loads(session_token, max_age=SESSION_EXPIRY)
    except:
        return None



#######
########## BACKUP KEY FUNTIONS
####

def gen_backup_key(length: int = 16) -> str:
    return secrets.token_hex(length // 2) 


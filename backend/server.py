#######
########## IMPORTS
####

from contextlib import asynccontextmanager
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, HTTPException, Depends, status, Security, Response
# from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import secrets
from redis import Redis
import json
import os
# import jwt



#######
########## GLOBALS
####

load_dotenv()
SUPABASE_URL= os.getenv('SUPABASE_URL')
SUPABASE_KEY= os.getenv('SUPABASE_KEY')



#######
########## SCHEMAS
####

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SessionData(BaseModel):
    user_id: int

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    second_email: EmailStr
    password_hash: str
    # backup_key_hash: str # ez ne legyen benne a típusban, csak az adatbázisban
    algo: str
    has_key: bool
    key_number: int
    encrypted_files: list[str]



#######
########## FUNCTIONS
####

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis(host="localhost", port=6379)
    print("✅ Server: setup ready")

    yield 
    
    app.state.redis.close()
    print("🛑 Server: shutdown complete")

async def get_current_user(session_id: str = Depends(lambda session_id=None: session_id)):
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = app.state.reids.get(f"session:{session_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return {"user_id": int(user_id)}



#######
########## SETUP
####

app = FastAPI(lifespan=lifespan)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



#######
########## ROUTES
####

@app.get("/")
async def root():
    return {"admin": "Hello hacker! ;)"}

@app.post("/api/register/")
async def register(name: str, email: EmailStr, second_email: EmailStr, password: str):
    
    backup_key = 'biztonsági kulcs'

    password_hash = 'psw hash'
    backup_key_hash = 'bk hash'
    
    
    new_user = {
        'name': name,
        'email': email,
        'second_email': second_email,
        'password_hash': password_hash,
        'backup_key_hash': backup_key_hash,
        'algo': 'DEFAULT_ALGO',
        'has_key': False,
        'key_number': 0,
        'encrypted_files': '',
    } 
    
    #supabase.table('user').insert(new_user).execute()
    
    return {'message': 'Registration successful', 'user': new_user, 'backup_key': backup_key}

@app.get("/api/login/")
async def login(data: LoginRequest, response: Response):
    # hashing password

    # looking for email in db

    # looking for password in db

    # email.password == password && password.email == email
    if (True):
        app.state.redis.setex(f"session:{session_id}", 3600, str(user_id))  # 1 óra lejárat
        
        session_id = secrets.token_hex(32)  # Véletlenszerű session ID
        user_id = 1  # Példa felhasználó ID

        # HTTP-only cookie beállítása
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="Lax",  # vagy "Strict" a nagyobb biztonság érdekében
            #secure=True  # Csak HTTPS-en működik
        )
        
        return {"message": "Login successful"}

@app.get("/api/logout")
async def logout(response: Response, session_id: str = Depends(lambda session_id=None: session_id)):
    if session_id:
        app.state.redis.delete(f"session:{session_id}")

    response.delete_cookie("session_id")
    return {"message": "Logged out"}
















@app.get("/api/user")
async def get_user(id: int, ):
    return {'message': 'Hi :)'}

@app.put("/api/user")
async def edit_user():
    return {'message': 'Hi :)'}
    
@app.get("/api/files")
async def get_files():
    return {'message': 'Hi :)'}

@app.delete("/api/files")
async def delete_file():
    return {'message': 'Hi :)'}

@app.post("/api/upload")
async def upload():
    return {'message': 'Hi :)'}

@app.get("/api/download")
async def download():
    return {'message': 'Hi :)'}

@app.get("/api/algos")
async def get_algos():
    return {'message': 'Hi :)'}

@app.post("/api/switch-algo")
async def switch_algo():
    return {'message': 'Hi :)'}

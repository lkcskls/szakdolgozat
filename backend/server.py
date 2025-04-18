#######
########## IMPORTS
####

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from security import hash_password, verify_password, set_session_cookie, verify_session, gen_backup_key
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Security, Response, Request, UploadFile, File
from dotenv import load_dotenv
from typing import Optional, List
from redis import Redis
from pathlib import Path
import secrets
import shutil
import json
import uuid
import os


#######
########## GLOBALS
####

load_dotenv()
SUPABASE_URL    = os.getenv('SUPABASE_URL')
SUPABASE_KEY    = os.getenv('SUPABASE_KEY')
DEFAULT_ALGO    = 'AES_256'
UPLOADS_DIR     = Path("uploads")

#######
########## SCHEMAS
####

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    second_email: EmailStr
    password: str

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

class UploadRequest(BaseModel):
    encrypted: Optional[bool] = False
    force: Optional[bool] = False  # Ha igaz, újranevezi a feltöltött fájlt, aminek ütközik a neve



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

def is_email_taken(email: EmailStr) -> bool:
    response = supabase.table("user").select("id").eq("email", email).execute()
    return len(response.data) > 0 

def check_file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)

def generate_unique_filename(file_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name, ext = os.path.splitext(file_name)
    return f"{name}_{timestamp}{ext}"

def authenticate_user(session_token: str) -> int:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = verify_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = session_data["user_id"]
    return user_id



#######
########## SETUP
####

app = FastAPI(lifespan=lifespan)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://172.20.10.2:3000", "http://localhost:3000", "https://drake-heroic-chow.ngrok-free.app", "http://drake-heroic-chow.ngrok-free.app", "https://lkb-v2.vercel.app", "https://lkb-v2.vercel.app" , "https://lkb-v2-git-dev-koloas-projects.vercel.app"],  # Frontend domain, amit engedélyezel
    allow_origins=["http://localhost:3000"],  # Frontend domain, amit engedélyezel
    allow_credentials=True,
    #allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Engedélyezett HTTP módszerek
    allow_methods=["*"],  # Engedélyezett HTTP módszerek
    #allow_headers=["Content-Type", "Authorization"],  # Engedélyezett fejlécek
    allow_headers=["*"],  # Engedélyezett fejlécek
)


#######
########## ROUTES
####

@app.get("/")
async def root():
    return {"admin": "Hello hacker! ;)"}

@app.post("/api/register")
async def register(data: RegisterRequest):
    name = data.name
    email = data.email
    second_email = data.second_email
    password = data.password

    if is_email_taken(email):
        raise HTTPException(status_code=400, detail="Email already in use")
    
    if email == second_email:
        raise HTTPException(status_code=400, detail="The main and the secondary email can not be the same")

    backup_key = gen_backup_key()

    password_hash =hash_password(password)
    backup_key_hash = hash_password(backup_key)
    
    new_user = {
        'name': name,
        'email': email,
        'second_email': second_email,
        'password_hash': password_hash,
        'backup_key_hash': backup_key_hash,
        'algo': DEFAULT_ALGO,
        'has_key': False,
        'key_number': 0,
    } 
    
    supabase.table('user').insert(new_user).execute()

    return {'message': 'Registration successful', 'backup_key': backup_key}

@app.post("/api/login")
async def login(data: LoginRequest, response: Response):
    user = supabase.table("user").select("*").eq("email", data.email).single().execute().data

    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    set_session_cookie(response, user['id'])
    return {"message": "Login successful", 'user_id': user['id']}

@app.post("/api/logout")
async def logout(response: Response):
    #response.delete_cookie("session_token")
    #response.delete_cookie("session_token", path="/api") 
    response.delete_cookie(
        "session_token", 
        httponly=True,  # Az HttpOnly flag is szükséges a törléshez
        secure=False,   # A Secure flag itt is fontos, hogy megfelelő legyen
        samesite="Lax", # Azonos beállítás a törléshez
        path="/"        # Az alapértelmezett path, ha nem volt specifikálva
    )
    return {"message": "Logged out successfully"}

@app.get("/api/user")
async def get_user(request: Request):
    user_id = authenticate_user(request.cookies.get("session_token"))

    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user:
        return {
            'id': user['id'],
            'name': user['name'], 
            'email': user['email'], 
            'second_email': user['second_email'], 
            'algo': user['algo'], 
        }
    else: 
        raise HTTPException(404, 'User not found')

@app.put("/api/user")
async def edit_user(request: Request, name: Optional[str] = None, email: Optional[EmailStr] = None, second_email: Optional[EmailStr] = None, password: Optional[str] = None, algo: Optional[str] = None):
    
    user_id = authenticate_user(request.cookies.get("session_token"))
    
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}

    if name:
        update_data["name"] = name

    if email:
        if is_email_taken(request.email, user["id"]):
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = email

    if second_email:
        update_data["second_email"] = second_email

    if password:
        hashed_password = hash_password(password)
        update_data["password_hash"] = hashed_password

    if algo:
        update_data["algo"] = algo

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    response = supabase.table("user").update(update_data).eq("id", user["id"]).execute().data

    if not response:
        raise HTTPException(status_code=500, detail="Database update failed")

    return {"message": "User updated successfully"}

@app.get("/api/files")
async def get_files(request: Request,):
    user_id = authenticate_user(request.cookies.get("session_token"))

    result = supabase.table('files').select('*').eq('user_id', user_id).execute().data

    return result

@app.delete("/api/files")
async def delete_file(
    request: Request, 
    filename: Optional[str] = "",
    uuid: Optional[str] = ""
):
    user_id = authenticate_user(request.cookies.get("session_token"))
    
    if filename != "":
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', filename).execute().data
        if result:
            file_path = UPLOADS_DIR / str(user_id) / result[0]['uuid']
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            response = supabase.table("files").delete().eq("user_id", user_id).eq("filename", filename).execute()
            if not response:
                raise HTTPException(status_code=500, detail="Failed to delete record from database.")

            try:
                os.remove(file_path)
                return {"message": f"File '{filename}' deleted successfully."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        else:
            raise HTTPException(status_code=404, detail=f"File not found")

    elif uuid != "":
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('uuid', uuid).execute().data
        if result:
            file_path = UPLOADS_DIR / str(user_id) / uuid
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            response = supabase.table("files").delete().eq("user_id", user_id).eq("uuid", uuid).execute()
            if not response:
                raise HTTPException(status_code=500, detail="Failed to delete record from database.")

            try:
                os.remove(file_path)
                return {"message": f"File '{uuid}' deleted successfully."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        else:
            raise HTTPException(status_code=404, detail=f"File not found")

    else:
        raise HTTPException(status_code=400, detail="No parameter given")

@app.post("/api/upload")
async def upload(
    request: Request, 
    force: Optional[bool] = False, 
    encrypted: Optional[bool] = False, 
    files: List[UploadFile] = File(...) 
):
    user_id = authenticate_user(request.cookies.get("session_token"))
    
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_directory = f"uploads/{user['id']}"

    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    file_responses = []

    for file in files:
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', file.filename).execute()
        exists = result.data

        # UUID és új fájlútvonal
        file_uuid = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_uuid}{file_extension}"
        file_path = os.path.join(user_directory, new_filename)

        if exists and force:
            ...
            # átnevezés
        elif exists:
            raise HTTPException(400, "Filename already in use")

        try:
            if encrypted:
                ...
                # titkosítás
            else:
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
            
            res = supabase.table('files').insert({"filename": file.filename, "user_id": user_id, "encrypted": encrypted, "uuid": new_filename}).execute()
            if not res:
                    raise HTTPException(400, 'Supabase error while updating encrypted_files')
            
            file_responses.append({"file": file.filename, "status": "uploaded", "error": ''})

        except Exception as e:
            file_responses.append({"file": file.filename, "status": "failed", "error": str(e)})

    return {"message": "Files processed successfully", "files": file_responses}

@app.get("/api/download")
async def download(
    request: Request, 
    filename: Optional[str] = "",
    uuid: Optional[str] = ""
):
    user_id = authenticate_user(request.cookies.get("session_token"))

    if filename != "":
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', filename).execute().data

        if result:
            file_path = UPLOADS_DIR / str(user_id) / result[0]['uuid']
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            return FileResponse(path=file_path, filename=filename)
    
    elif uuid != "":
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('uuid', uuid).execute().data
        if result:
            file_path = UPLOADS_DIR / str(user_id) / uuid
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            return FileResponse(path=file_path, filename=filename)
    
    else:
        raise HTTPException(status_code=400, detail="No parameter given")





@app.get("/api/algos")
async def get_algos():
    return {'algos': [{'name': 'AES_128'}, {'name': 'AES_256'}]}

@app.post("/api/switch-algo")
async def switch_algo():
    # Ha van kulcsa a felhasználónak, akkor bekéri és bekéri azz új algot is
        # Ellenőrzi, hogy a kulcs megfelelő-e
            # Ha igen, kititkosít minden titkosított dolgot
    
    # Generál egy új kulcsot az új algo-nak
        # Elmenti a Hash-ét és az algo nevét az adatbázisban
            # Letitkosítja a korábban titkosított fájlokat

    return {'message': 'Hi :)'}




"""
## auth starts
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = verify_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = session_data["user_id"]
## auth ends
"""
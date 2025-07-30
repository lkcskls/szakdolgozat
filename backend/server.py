
#######
########## IMPORTS
####

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from security import hash_password, verify_password, set_session_cookie, delete_session_cookie, generate_key, authenticate_user
from services import decrypt_file, encrypt_file, is_email_taken, is_filename_taken, get_user_by_id, get_user_by_email, encrypt_user_files, decrypt_user_files, lifespan
from fastapi import FastAPI, HTTPException, Response, Request, UploadFile, File
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List
import shutil
import uuid
import os



#######
########## GLOBALS
####

load_dotenv()
SUPABASE_URL    = os.getenv('SUPABASE_URL')
SUPABASE_KEY    = os.getenv('SUPABASE_KEY')
DEFAULT_ALGO    = 'AES-256'
ALGOS           = [{'name': 'AES-256'}, {'name': 'ChaCha20'}]
UPLOADS_DIR     = Path("uploads")
TEMP_DIR        = Path("temp")



#######
########## SCHEMAS
####

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
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
    password_hash: str
    algo: str
    has_key: bool

class UploadRequest(BaseModel):
    encrypted: Optional[bool] = False
    force: Optional[bool] = False  # Ha igaz, újranevezi a feltöltött fájlt, aminek ütközik a neve

class AlgoChangeRequest(BaseModel):
    algo: str
    key_hex: Optional[str] = ""



#######
########## SETUP
####

app = FastAPI(lifespan=lifespan)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



#######
########## ROUTES
####

@app.post("/api/register")
async def register(data: RegisterRequest):
    name = data.name
    email = data.email
    password = data.password

    #input validáció
    if is_email_taken(supabase, email, -1):
        raise HTTPException(status_code=400, detail="Email already in use")
    if len(name) < 5:
        raise HTTPException(status_code=400, detail="Name must be at least 5 characters")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    #jelszavak biztonságos mentése
    password_hash = hash_password(password)
    
    #új user elmentése
    new_user = {
        'name': name,
        'email': email,
        'password_hash': password_hash,
        'algo': DEFAULT_ALGO,
        'has_key': False,
    } 
    response = supabase.table('user').insert(new_user).execute().data
    if not response:
        raise HTTPException(status_code=400, detail="Failed to create user")

    return {'message': 'Registration successful'}

@app.post("/api/login")
async def login(data: LoginRequest, response: Response):
    #felhasználó lekérése email alapján
    user = get_user_by_email(supabase, data.email)

    #felhasználó és a jelszó ellenőrzése
    if not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    #session_token beállítása
    set_session_cookie(response, user['id'])
    
    #user_id visszaadása
    return {"message": "Login successful", 'user_id': user['id']}

@app.post("/api/logout")
async def logout(response: Response):
    #session_token törlése
    delete_session_cookie(response)
    return {"message": "Logged out successfully"}

@app.get("/api/user")
async def get_user(request: Request):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))

    #felhasználó lekérése
    user = get_user_by_id(supabase, user_id)

    #user visszaadása
    return {
        'id': user['id'],
        'name': user['name'], 
        'email': user['email'], 
        'algo': user['algo'], 
    }

@app.put("/api/user")
async def edit_user(request: Request, name: Optional[str] = None, email: Optional[EmailStr] = None, password: Optional[str] = None, new_password: Optional[str] = None):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)

    update_data = {}

    #módosítandó adatok kigyűjtése és validálása
    if name:
        if len(name) < 5 :
            raise HTTPException(status_code=400, detail="Name must be at least 5 characters")
        update_data["name"] = name
    if email:
        if is_email_taken(supabase, email, user_id):
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = email
    if password and new_password:
        if not verify_password(password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid password")
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        hashed_password = hash_password(new_password)
        update_data["password_hash"] = hashed_password

    #ha nem érkezett egy valid paraméter sem
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    #user frissítése
    response = supabase.table("user").update(update_data).eq("id", user["id"]).execute().data
    if not response:
        raise HTTPException(status_code=500, detail="Failed to update database")

    return {"message": "User updated successfully"}

@app.get("/api/files")
async def get_files(request: Request):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))

    #fájl adatok lekérése és visszaadása
    try:
        response = supabase.table('files').select('*').eq('user_id', user_id).execute().data
        return response
    except:
        raise HTTPException(status_code=500, detail=f"Database error")

@app.delete("/api/files")
async def delete_file(
    request: Request, 
    filename: str,
    key_hex: Optional[str] = "", 
):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #törlés filename alapján
    if filename != "":
        #fájl lekérése fájlnév alapján
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', filename).execute().data
        
        #ha létezik a fájl az adatbázisban
        if result:
            if result[0]['encrypted'] and not verify_password(key_hex, user['secret_key_hash']):
                raise HTTPException(status_code=401, detail="Invalid secret key")

            #fájl létezésének ellenőrzése a fájlrendszerben (uuid alapján)
            file_path = UPLOADS_DIR / str(user_id) / result[0]['uuid']
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            #fájl törlése az adatbázisból (filename alapján)
            response = supabase.table("files").delete().eq("user_id", user_id).eq("filename", filename).execute()
            if not response:
                raise HTTPException(status_code=500, detail="Failed to delete from database")

            #fájl törlése a fájlrendszerből (uuid alapján)
            try:
                os.remove(file_path)
                return {"message": f"File '{filename}' deleted successfully."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete from server")
        
        #ha nem létezik a fájl az adatbázisban
        else:
            raise HTTPException(status_code=404, detail=f"File not found")
    else:
        raise HTTPException(status_code=400, detail=f"Invalid filename")

@app.post("/api/upload")
async def upload(
    request: Request, 
    encrypted: Optional[bool] = False, 
    key_hex: Optional[str] = "", 
    files: List[UploadFile] = File(...) 
):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)

    #felhasználó utvonalának meghatározása, és ha kell létrehozása    
    user_directory = Path("uploads") / str(user["id"])
    user_directory.mkdir(parents=True, exist_ok=True)
    
    file_responses = []

    #kapott fájlok feldolgozása
    for file in files:
        #fájl mentése
        try:
            #filename létezésének ellenőrzése
            if is_filename_taken(supabase, file.filename, user_id):
                raise Exception("Filename already in use")
            
            #file_path meghatározása (új fájlnév: uuid.kiterjesztés)
            file_uuid = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            new_filename = f"{file_uuid}{file_extension}"
            file_path = user_directory / new_filename

            #titkosított fájl esetén
            if encrypted:
                #user-nek nincs kulcsa
                if not user['has_key']:
                    raise HTTPException(401, "You don't have secret key")
                #user-nek van kulcsa
                elif user['has_key']:
                    #nem adta meg a kulcsot
                    if key_hex == "":
                        raise HTTPException(401, 'Invalid secret key')
                    #rossz kulcsot adott meg
                    elif not verify_password(key_hex, user['secret_key_hash']):
                        raise HTTPException(401, 'Invalid secret key')
                #user-nek van kulcsa és ezt a kulcsot adta meg

                file_content = await file.read()
                
                #fájl titkosítása a felhasználó kulcsával, algoritmusával és mentése a felhasználó mappájába
                try:
                    encrypt_file(file_content, file_path, key_hex, user['algo'])
                except Exception as e:
                    raise Exception(f"{e}")
            
            #sima fájl esetén
            else:
                #fájl mentése a felhasználó mappájába
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
            
            #fájl adatainak feltöltése az adatbázisba
            res = supabase.table('files').insert({"filename": file.filename, "user_id": user_id, "encrypted": encrypted, "uuid": new_filename}).execute()
            if not res:
                raise HTTPException(500, 'Database error while updating files')
            
            #log
            file_responses.append({"file": file.filename, "status": "uploaded", "error": ''})

        except Exception as e:
            file_responses.append({"file": file.filename, "status": "failed", "error": str(e)})

    #logok visszaadása
    return file_responses

@app.get("/api/download")
async def download(
    request: Request, 
    filename: str,
    key_hex: Optional[str] = ""
):
    print('download')
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #fájl adatainak lekérése
    result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', filename).execute().data

    #ha létezik a fájl az adatbázisban
    if result:
        #fájl létezésének ellenőrzése a fájlrendszerben
        file_path = UPLOADS_DIR / str(user_id) / result[0]['uuid']
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        #titkosított fájl
        if result[0]['encrypted']:
            #felhasználó nem adott meg titkos kulcsot
            if key_hex == "":
                raise HTTPException(status_code=400, detail="Invalid secret key")
            
            #user-nek van titkos kulcsa, de nem egyezik a felhasználó által megadottal
            if user['secret_key_hash'] and not verify_password(key_hex, user['secret_key_hash']):
                raise HTTPException(status_code=401, detail="Invalid secret key")
            #user-nek van titkos kulcs (mivel van titkosított fájlja), és megegyezik a felhasználó által megadottal
            
            #kititkosítás
            try:
                #átmeneti útvonal meghatározása
                decrypted_file_path = TEMP_DIR / f"decrypted_{result[0]['uuid']}"

                #fájl kititkosítása a felhasználó mappájából az átmeneti útvonalra
                decrypt_file(file_path, decrypted_file_path, key_hex, user['algo'])

                #kititkosított fájl visszaadása az átmeneti útvonalról
                return FileResponse(
                    decrypted_file_path,  
                    filename=filename,
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Decryption failed")
                
        #sima fájl
        else:
            #fájl visszaadása a felhasználó mappájából
            return FileResponse(path=file_path, filename=filename)

@app.get("/api/algos")
async def get_algos():
    return ALGOS

@app.get("/api/encrypt-details")
async def get_user_algo(request: Request):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #user algoritmusának és has_key paraméterének visszaadása
    return { "algo": user['algo'], "has_secret_key": user['has_key']}

@app.post("/api/switch-algo")
async def switch_algo(request: Request, algo_request: AlgoChangeRequest):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #megadott algoritmus ellenőrzése
    allowed_algos = [item['name'] for item in ALGOS]
    if algo_request.algo not in allowed_algos:
        raise HTTPException(status_code=400, detail="Invalid algorithm")
    
    #titkosított fájlok lekérése
    encrypted_files = supabase.table('files').select('*').eq('user_id', user_id).eq('encrypted', True).execute().data
    
    #ha user-nek van titkosított fájlja
    if encrypted_files:
        #megadott titkos kulcs helyes
        if user['has_key'] and verify_password(algo_request.key_hex, user['secret_key_hash']):
            try:
                #user titkos fájljainak kititkosítása
                decrypt_user_files(user_id, algo_request.key_hex, encrypted_files, user['algo'], UPLOADS_DIR, TEMP_DIR)

                #user titkos fájljainak újratitkosítása
                encrypt_user_files(user_id, algo_request.key_hex, encrypted_files, algo_request.algo, TEMP_DIR, UPLOADS_DIR)

                #adatbázisban az algo frissítése
                update_response = supabase.table('user').update({'algo': algo_request.algo}).eq('id', user_id).execute()
                if not update_response:
                    raise HTTPException(status_code=400, detail="Failed to update database")
            except RuntimeError as e:
                print(f"{e}")
                raise HTTPException(status_code=400, detail="Failed re-encryption")

            #log
            return JSONResponse(content={"message": f"Algorithm updated to {algo_request.algo}"})
        
        #megadott titkos kulcs helytelen
        else:
            raise HTTPException(status_code=401, detail="Invalid secret key")
    
    #ha user-nek nincs titkosított fájlja
    else:
        #adatbázis frissítése
        update_response = supabase.table('user').update({'algo': algo_request.algo}).eq('id', user_id).execute()
        if not update_response:
            raise HTTPException(status_code=500, detail="Failed to update database")

        #log
        return JSONResponse(content={"message": f"Algorithm updated to {algo_request.algo}"})

@app.get("/api/gen-sk")
async def gen_sk(request: Request):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #user-nek már van kulcsa
    if user['has_key']:
        raise HTTPException(status_code=400, detail="You already have a secret key")
        
    #user-nek még nincs kulcsa
    else:
        #kulcsgenerálás
        key = generate_key()
        key_hex = key.hex()

        #adatbázis frissítése
        update_response = supabase.table('user').update({'has_key': True, 'secret_key_hash': hash_password(key_hex)}).eq('id', user_id).execute()
        if not update_response:
            raise HTTPException(status_code=500, detail=f"Failed to update database")
        
        #kulcs visszaadása
        return key_hex

@app.post("/api/verify-secret-key")
async def verify_sicret_key(request: Request, key_hex: str):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = get_user_by_id(supabase, user_id)
    
    #validáció visszaadása
    return verify_password(key_hex, user['secret_key_hash'])
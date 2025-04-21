#######
########## IMPORTS
####

from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from security import hash_password, verify_password, set_session_cookie, delete_session_cookie, verify_session, gen_backup_key, generate_key, aes_encrypt_file, aes_decrypt_file
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, Request, UploadFile, File
from dotenv import load_dotenv
from typing import Optional, List
from pathlib import Path
from io import BytesIO
import shutil
import uuid
import os



#######
########## GLOBALS
####

load_dotenv()
SUPABASE_URL    = os.getenv('SUPABASE_URL')
SUPABASE_KEY    = os.getenv('SUPABASE_KEY')
DEFAULT_ALGO    = 'AES_256'
ALGOS           = [{'name': 'AES_256'}, {'name': 'ChaCha20'}]
UPLOADS_DIR     = Path("uploads")
TEMP_DIR        = Path("temp")



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

class AlgoChangeRequest(BaseModel):
    algo: str
    current_sk: Optional[str] = ""



#######
########## FUNCTIONS
####

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Server: setup ready")

    yield 
    
    print("🛑 Server: shutdown complete")

def is_email_taken(email: EmailStr) -> bool:
    #email keresése az adatbázisban
    response = supabase.table("user").select("id").eq("email", email).execute()
    return len(response.data) > 0 

def authenticate_user(session_token: str) -> int:
    #ha nincs session_token
    if not session_token or session_token=="":
        raise HTTPException(status_code=401, detail="Not authenticated")

    #session_token ellenőrzése
    session_data = verify_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    #session_token-hez tartozó user_id visszaadása
    user_id = session_data["user_id"]
    return user_id

#chacha20
def encrypt_file(file_content: bytes, output_path: str, key_hex: str, algo: str):
    #kulcs átalakítása
    key_bytes = bytes.fromhex(key_hex)

    #AES_256
    if algo == "AES_256":
        #fájl titkosítása és mentése az output_path-ra
        input_file = BytesIO(file_content)
        encrypted_file = aes_encrypt_file(input_file, key_bytes)
        with open(output_path, "wb") as f:
            shutil.copyfileobj(encrypted_file, f)
    
    #egyéb algoritmus
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    #log
    print(f"{output_path} encrypt sikeres.")

#van + chacha20
def decrypt_file(input_path: str, output_path: str, key_hex: str, algo: str):
    #kulcs átalakítása
    key_bytes = bytes.fromhex(key_hex)

    #fájl megnyitása az input_path-ról 
    with open(input_path, "rb") as f:
        file_content = f.read()

    #fájl létezésének ellenőrzées

    #AES_256
    if algo == "AES_256":
        #fájl visszafejtése és mentése az output_path-ra
        decrypted_file = aes_decrypt_file(BytesIO(file_content), key_bytes)
        with open(output_path, "wb") as decrypted_f:
            decrypted_f.write(decrypted_file.read())
    
    #egyéb algoritmus
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    #log
    print(f"{input_path} → {output_path} decrypt sikeres.")

def encrypt_user_files(user_id: str, key: str, files_to_encrypt: list, algo: str):
    #user mappájának ellenőrzése, ha kell létrehozása
    user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)

    #fájlok feldolgozása
    for file in files_to_encrypt:
        #fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = os.path.join(TEMP_DIR, filename)
        output_path = os.path.join(user_upload_dir, filename)

        #fájl létezésének ellenőrzése
        if not os.path.exists(input_path):
            print(f"Fájl nem található: {input_path}, kihagyva.")
            continue

        #titkosítás
        try:
            encrypt_file(input_path, output_path, key, algo)
            print(f"Sikeresen titkosítva: {filename}")
        except Exception as e:
            print(f"Hiba a {filename} titkosításakor: {e}")

    #log
    print(f"Minden fájl titkosítva ide: {user_upload_dir}")

def decrypt_user_files(user_id: str, key: str, encrypted_files: list, algo: str):
    #átmeneti mappa ellenőrzése, ha kell létrehozása
    os.makedirs(TEMP_DIR, exist_ok=True)

    #fájlok feldolgozása
    for file in encrypted_files:
        #fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = os.path.join(UPLOADS_DIR, user_id, filename)
        output_path = os.path.join(TEMP_DIR, filename)

        #fájl létezésének ellenőrzése
        if not os.path.exists(input_path):
            print(f"Fájl nem található: {input_path}, kihagyva.")
            continue

        #visszafejtés
        try:
            decrypt_file(input_path, output_path, key, algo)
            print(f"Sikeresen kititkosítva: {filename}")
        except Exception as e:
            print(f"Hiba a {filename} kititkosításakor: {e}")

    #log
    print(f"Minden fájl kititkosítva ide: {TEMP_DIR}")



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

@app.get("/")
async def root():
    return {"admin": "Hello hacker! ;)"}

@app.post("/api/register")
async def register(data: RegisterRequest):
    name = data.name
    email = data.email
    second_email = data.second_email
    password = data.password

    #email létezésének ellenőrzése
    if is_email_taken(email):
        raise HTTPException(status_code=400, detail="Email already in use")
    
    #email egyezés ellenőrzése
    if email == second_email:
        raise HTTPException(status_code=400, detail="The main and the secondary email can not be the same")

    #visszaállítókulcs generálás
    backup_key = gen_backup_key()

    #jelszavak biztonságos mentése
    password_hash =hash_password(password)
    backup_key_hash = hash_password(backup_key)
    
    #új user elmentése
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

    #visszaállítókulcs visszaadása
    return {'message': 'Registration successful', 'backup_key': backup_key}

@app.post("/api/login")
async def login(data: LoginRequest, response: Response):
    #felhasználó lekérése email alapján
    user = supabase.table("user").select("*").eq("email", data.email).single().execute().data
    
    #felhasználó és a jelszó ellenőrzése
    if not user or not verify_password(data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

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
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data

    #user visszaadása ha létezik, különben 404
    if user:
        return {
            'id': user['id'],
            'name': user['name'], 
            'email': user['email'], 
            'second_email': user['second_email'], 
            'algo': user['algo'], 
        }
    else: 
        raise HTTPException(status_code=404, detail="User not found")

@app.put("/api/user")
async def edit_user(request: Request, name: Optional[str] = None, email: Optional[EmailStr] = None, second_email: Optional[EmailStr] = None, password: Optional[str] = None, algo: Optional[str] = None):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}

    #módosítandó adatok kigyűjtése
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

    #ha nem érkezett egy paraméter sem
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    #user frissítése
    response = supabase.table("user").update(update_data).eq("id", user["id"]).execute().data
    if not response:
        raise HTTPException(status_code=500, detail="Database update failed")

    return {"message": "User updated successfully"}

@app.get("/api/files")
async def get_files(request: Request,):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))

    #fájl adatok lekérése és visszaadása
    result = supabase.table('files').select('*').eq('user_id', user_id).execute().data
    return result

# csak ha érvényes a key_hex
@app.delete("/api/files")
async def delete_file(
    request: Request, 
    filename: Optional[str] = "",
    uuid: Optional[str] = ""
):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    
    #törlés filename alapján
    if filename != "":
        #fájl lekérése fájlnév alapján
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', filename).execute().data
        
        #ha létezik a fájl az adatbázisban
        if result:
            #fájl létezésének ellenőrzése a fájlrendszerben (uuid alapján)
            file_path = UPLOADS_DIR / str(user_id) / result[0]['uuid']
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            #fájl törlése az adatbázisból (filename alapján)
            response = supabase.table("files").delete().eq("user_id", user_id).eq("filename", filename).execute()
            if not response:
                raise HTTPException(status_code=500, detail="Failed to delete record from database.")

            #fájl törlése a fájlrendszerből (uuid alapján)
            try:
                os.remove(file_path)
                return {"message": f"File '{filename}' deleted successfully."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        
        #ha nem létezik a fájl az adatbázisban
        else:
            raise HTTPException(status_code=404, detail=f"File not found")

    #törlés uuid alapján
    elif uuid != "":
        #fájl lekérése fájlnév alapján
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('uuid', uuid).execute().data

        #ha létezik a fájl az adatbázisban
        if result:
            #fájl létezésének ellenőrzése a fájlrendszerben (uuid alapján)
            file_path = UPLOADS_DIR / str(user_id) / uuid
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
            
            #fájl törlése az adatbázisból (uuid alapján)
            response = supabase.table("files").delete().eq("user_id", user_id).eq("uuid", uuid).execute()
            if not response:
                raise HTTPException(status_code=500, detail="Failed to delete record from database.")

            #fájl törlése a fájlrendszerből (uuid alapján)
            try:
                os.remove(file_path)
                return {"message": f"File '{uuid}' deleted successfully."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        
        #ha nem létezik a fájl az adatbázisban
        else:
            raise HTTPException(status_code=404, detail=f"File not found")

    #ha sem filename, sem uuid nem lett megadva
    else:
        raise HTTPException(status_code=400, detail="No parameter given")

# van
@app.post("/api/upload")
async def upload(
    request: Request, 
    encrypted: Optional[bool] = False, 
    key_hex: Optional[str] = "", 
    files: List[UploadFile] = File(...) 
):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #felhasználó utvonalának meghatározása, és ha kell létrehozása    
    user_directory = f"uploads/{user['id']}"
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    file_responses = []

    #kapott fájlok feldolgozása
    for file in files:
        #file_path meghatározása (új fájlnév: uuid.kiterjesztés)
        file_uuid = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        new_filename = f"{file_uuid}{file_extension}"
        file_path = os.path.join(user_directory, new_filename)

        #filename létezésének ellenőrzése
        result = supabase.table('files').select('*').eq('user_id', user_id).eq('filename', file.filename).execute().data
        if result:
            raise HTTPException(400, "Filename already in use")

        #fájl mentése
        try:
            #titkosított fájl esetén
            if encrypted:
#user-nek nincs kulcsa -> Error (és akkor ezt a külön végponton meg kell csinálni fájlfeltöltés előtt)
                if not user['has_key']:
                    #kulcsgenerálás
                    key = generate_key()
                    key_hex = key.hex()
                    print(key_hex)
                    #user frissítése, kulcs-hash mentése
                    """
                    update_response = supabase.table("user").update({"has_key" : True, "secret_key_hash": hash_password(key_hex)}).eq("id", user_id).execute().data
                    if not update_response:
                        raise HTTPException(status_code=400, detail="Failed to update secret key")
                    """
                #user-nek van kulcsa, de nem jó kulcsot adott meg
                elif user['has_key'] and not verify_password(key_hex, user['secret_key_hash']):
                    raise HTTPException(401, 'Invalid secret key')
                #user-nek van kulcsa és ezt a kulcsot adta meg

                file_content = await file.read()
                
                #fájl titkosítása a felhasználó kulcsával, algoritmusával és mentése a felhasználó mappájába
                encrypt_file(file_content, file_path, key_hex, user['algo'])
            
            #sima fájl esetén
            else:
                #fájl mentése a felhasználó mappájába
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
            
            #fájl adatainak feltöltése az adatbázisba
            res = supabase.table('files').insert({"filename": file.filename, "user_id": user_id, "encrypted": encrypted, "uuid": new_filename}).execute()
            if not res:
                    raise HTTPException(400, 'Supabase error while updating files')
            
            #log
            file_responses.append({"file": file.filename, "status": "uploaded", "error": ''})

        except Exception as e:
            file_responses.append({"file": file.filename, "status": "failed", "error": str(e)})

    #logok visszaadása
    return {"message": "Files processed successfully", "files": file_responses}

@app.get("/api/download")
async def download(
    request: Request, 
    filename: str,
    key_hex: Optional[str] = ""
):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    print(key_hex)

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
                raise HTTPException(status_code=400, detail="No key_hex parameter given")
            
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
                raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")
        
        #sima fájl
        else:
            #fájl visszaadása a felhasználó mappájából
            return FileResponse(path=file_path, filename=filename)

@app.get("/api/algos")
async def get_algos():
    #ALGOS visszaadása
    return ALGOS

@app.get("/api/algo")
async def get_user_algo(request: Request):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #user algoritmusának és has_key paraméterének visszaadása
    return { "algo": user['algo'], "hasSecretKey": user['has_key']}

#van
@app.post("/api/switch-algo")
async def switch_algo(request: Request, algo_request: AlgoChangeRequest):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #megadott algoritmus ellenőrzése
    allowed_algos = [item['name'] for item in ALGOS]
    if algo_request.algo not in allowed_algos:
        raise HTTPException(status_code=400, detail="Invalid algorithm")
    
    #titkosított fájlok lekérése
    encrypted_files = supabase.table('files').select('*').eq('user_id', user_id).eq('encrypted', True).execute().data
    
    #ha user-nek van titkosított fájlja
    if encrypted_files:
        #megadott titkos kulcs helyes
        if verify_password(algo_request.current_sk, user['secret_key_hash']):
            
            #user titkos fájljainak kititkosítása
            decrypt_user_files(user_id, algo_request.current_sk, encrypted_files, user['algo'])
            
            #új kulcs generálás
            new_key = generate_key()
            new_key_hex = new_key.hex()
            
            #user titkos fájljainak újratitkosítás az új kulccsal
            encrypt_user_files(user_id, new_key_hex, encrypted_files, algo_request.algo)
            
            #adatbázisban a hash és az algo frissítése
            update_response = supabase.table('user').update({'secret_key_hash': hash_password(new_key_hex), 'algo': algo_request.algo}).eq('id', user_id).execute()
            if not update_response:
                raise HTTPException(status_code=400, detail="Failed to update secret key hash and algo")
            
#átmeneti fájlok törlése

            #új kulcs visszaadása
            return JSONResponse(content={"new_secret_key": f"${new_key_hex}"})
        
        #megadott titkos kulcs helytelen
        else:
            raise HTTPException(status_code=401, detail="Secret key invalid")
    
    #ha user-nek nincs titkosított fájlja
    else:
        #adatbázis frissítése
        update_response = supabase.table('user').update({'algo': algo_request.algo}).eq('id', user_id).execute()
        if not update_response:
            raise HTTPException(status_code=500, detail="Failed to update algorithm")

        #log
        return JSONResponse(content={"message": f"Algorithm updated to {algo_request.algo}"})
    

    

    # Van titkosított fájl?
        # ha van => van titkos kulcs => megnézzük, hogy egyezik-e a megadottal
            # ha egyezik => kititkosítani mindent, genrálni új kulcsot az új algóval, újratitkosítani mindent, firssíteni a kulcs hash-t és az algot
            # ha nem => Error
        # ha nincs => simán lecseréljük az algoritmus, és generálunk egy kulcsot

    return {'message': 'Hi :)'}

@app.post("/api/gen-sk")
async def gen_sk(request: Request, current_sk: Optional[str] = ""):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #user-nek már van kulcsa
    if user['has_key']:
        #if current_sk == "" or not verify_password(current_sk, user['secret_key_hash']):
        raise HTTPException(status_code=400, detail="You already have a secret key")
        #ha szeretnénk, hogy lehessen új kulcsot kérni:
            # titkosított fájlok kititkosítása a régi kulccsal
            # új kulcs generálás
            # titkosítás az új kulccsal
            # régi kulcs hashének lecserélése az új hashére
    #user-nek még nincs kulcsa
    else:
        #kulcsgenerálás
        key = generate_key()
        key_hex = key.hex()

        #adatbázis frissítése
        update_response = supabase.table('user').update({'has_key': True, 'secret_key_hash': hash_password(key_hex)}).eq('id', user_id).execute()
        if not update_response:
            raise HTTPException(status_code=500, detail="Failed to update algorithm")
        
        #kulcs visszaadása
        return key_hex



#######
########## DEPRACATED
####
    
@app.post("/api/algo")
async def set_user_algo(request: Request, algo_request: AlgoChangeRequest):
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ellenőrizd, hogy benne van-e a támogatott algoritmusokban
    allowed_algos = [item['name'] for item in ALGOS]
    if algo_request.algo not in allowed_algos:
        raise HTTPException(status_code=400, detail="Invalid algorithm")
    
    # Frissítés adatbázisban
    update_response = supabase.table('user').update({'algo': algo_request.algo}).eq('id', user_id).execute()
    if not update_response:
        raise HTTPException(status_code=500, detail="Failed to update algorithm")

    return JSONResponse(content={"message": f"Algorithm updated to {algo_request.algo}"})

def generate_unique_filename(file_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    name, ext = os.path.splitext(file_name)
    return f"{name}_{timestamp}{ext}"

def check_file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)



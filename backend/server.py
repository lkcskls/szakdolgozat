
#######
########## IMPORTS
####

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
from security import hash_password, verify_password, set_session_cookie, delete_session_cookie, verify_session, generate_key, aes_encrypt_file, aes_decrypt_file, chacha20_encrypt_file, chacha20_decrypt_file
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
########## FUNCTIONS
####

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Server: setup ready")

    yield 
    
    print("🛑 Server: shutdown complete")

def is_email_taken(email: EmailStr, user_id: int) -> bool:
    #email keresése az adatbázisban, a felhasználó kizárásával
    response = supabase.table("user").select("id").eq("email", email).neq("id", user_id).execute()
    return len(response.data) > 0 

def is_filename_taken(filename: str, user_id: int) -> bool:
    response = (
        supabase
        .table("files")
        .select("id")
        .eq("filename", filename)
        .eq("user_id", user_id)
        .execute()
    )
    return len(response.data) > 0

def authenticate_user(session_token: str) -> int:
    #ha nincs session_token
    if not session_token or session_token=="":
        raise HTTPException(status_code=401, detail="Invalid session token")

    #session_token ellenőrzése
    session_data = verify_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    #session_token-hez tartozó user_id visszaadása
    user_id = session_data["user_id"]
    return user_id

def get_user_by_id(supabase: Client, user_id: str):
    try:
        response = supabase.table("user").select("*").eq("id", user_id).execute()
        users = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error")

    #nincs user az adott id-vel, vagy több is van
    if not users or len(users)>1:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users[0]

def get_user_by_email(supabase: Client, email: EmailStr):
    try:
        response = supabase.table("user").select("*").eq("email", email).execute()
        users = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error")

    #nincs user az adott email-lel, vagy több is van
    if not users or len(users)>1:
        raise HTTPException(status_code=404, detail="Invalid email or password")
    
    return users[0]

def encrypt_file(file_content: bytes, output_path: Path, key_hex: str, algo: str):
    #kulcs átalakítása
    key_bytes = bytes.fromhex(key_hex)

    #output létrehozása, ha nincs
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #AES_256
    if algo == "AES_256":
        print('aes')
        #fájl titkosítása és mentése az output_path-ra
        try:
            input_file = BytesIO(file_content)
            encrypted_file = aes_encrypt_file(input_file, key_bytes)
            with output_path.open("wb") as f:
                shutil.copyfileobj(encrypted_file, f)
        except Exception as e:
            raise RuntimeError(f"encrypt_file: {e}")

    #ChaCha20
    elif algo == "ChaCha20":
        print('chacha')
        #fájl titkosítása és mentése az output_path-ra
        try:
            encrypted_file = chacha20_encrypt_file(BytesIO(file_content), key_bytes)
            with output_path.open("wb") as output_file:
                output_file.write(encrypted_file.read())
        except Exception as e:
            raise RuntimeError(f"encrypt_file: {e}")
    
    #egyéb algoritmus
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    #log
    print(f"{output_path} encrypt sikeres.")

def encrypt_user_files(user_id: str, key: str, files_to_encrypt: list, algo: str):
    #user mappájának ellenőrzése, létrehozása ha nincs
    user_upload_dir = Path(UPLOADS_DIR) / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    #fájlok feldolgozása
    for file in files_to_encrypt:
        #fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = TEMP_DIR / filename
        output_path = user_upload_dir / filename

        #fájl létezésének ellenőrzése
        if not input_path.exists():
            raise RuntimeError(f"Fájl nem található: {input_path}")

        #titkosítás
        try:
            with input_path.open("rb") as f:
                file_content = f.read()
            encrypt_file(file_content, output_path, key, algo)
            print(f"Sikeresen titkosítva: {filename}")
        except Exception as e:
            raise RuntimeError(f"Hiba a {input_path} titkosításakor: {e}")
        finally:
            #átmeneti fájl törlése
            if input_path.exists():
                input_path.unlink()
                print(f"Átmeneti fájl törölve: {input_path}")

    # log
    print(f"Minden fájl titkosítva ide: {user_upload_dir}")



    #log
    print(f"Minden fájl titkosítva ide: {user_upload_dir}")

def decrypt_file(input_path: Path, output_path: Path, key_hex: str, algo: str):
    #fájl létezésének ellenőrzése
    if not input_path.exists():
        print('a')
        raise FileNotFoundError(f"{input_path} can't be found")

    #fájl megnyitása az input_path-ról 
    with input_path.open("rb") as f:
        file_content = f.read()

    #output létrehozása, ha nincs
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #kulcs átalakítása
    key_bytes = bytes.fromhex(key_hex)

    #AES_256
    if algo == "AES_256":
        print("aes")
        #fájl visszafejtése és mentése az output_path-ra
        try:
            decrypted_file = aes_decrypt_file(BytesIO(file_content), key_bytes)
            with output_path.open("wb") as decrypted_f:
                decrypted_f.write(decrypted_file.read())
        except Exception as e:
            raise RuntimeError(f"encrypt_file: {e}")
    
    #ChaCha20
    elif algo == "ChaCha20":
        print("chacha")
        #fájl visszafejtése és mentése az output_path-ra
        try:
            decrypted_file = chacha20_decrypt_file(BytesIO(file_content), key_bytes)
            with output_path.open("wb") as output_file:
                output_file.write(decrypted_file.read())
        except Exception as e:
            raise RuntimeError(f"encrypt_file: {e}")
    
    #egyéb algoritmus
    else:
        print('b')
        raise ValueError(f"Unsupported algorithm: {algo}")

    #log
    print(f"{input_path} → {output_path} decrypt sikeres.")

def decrypt_user_files(user_id: str, key: str, encrypted_files: list, algo: str):
    # átmeneti mappa ellenőrzése, ha kell létrehozása
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # fájlok feldolgozása
    for file in encrypted_files:
        # fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = Path(UPLOADS_DIR / str(user_id) / filename)
        output_path = Path(TEMP_DIR / filename)

        # fájl létezésének ellenőrzése
        if not input_path.exists():
            raise RuntimeError(f"Fájl nem található: {input_path}")

        # visszafejtés
        try:
            decrypt_file(input_path, output_path, key, algo)
            print(f"Sikeresen kititkosítva: {filename}")
        except Exception as e:
            raise RuntimeError(f"Hiba az {input_path} kititkosításakor: {e}")

    # log
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
    password = data.password

    #input validáció
    if is_email_taken(email, -1):
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
async def edit_user(request: Request, name: Optional[str] = None, email: Optional[EmailStr] = None, password: Optional[str] = None):
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
        if is_email_taken(email, user_id):
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = email
    if password:
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        hashed_password = hash_password(password)
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
async def get_files(request: Request,):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))

    #fájl adatok lekérése és visszaadása
    result = supabase.table('files').select('*').eq('user_id', user_id).execute().data
    return result

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
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #felhasználó utvonalának meghatározása, és ha kell létrehozása    
    user_directory = Path("uploads") / str(user["id"])
    user_directory.mkdir(parents=True, exist_ok=True)
    
    file_responses = []

    #kapott fájlok feldolgozása
    for file in files:
        #fájl mentése
        try:
            #file_path meghatározása (új fájlnév: uuid.kiterjesztés)
            file_uuid = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            new_filename = f"{file_uuid}{file_extension}"
            file_path = user_directory / new_filename

            #filename létezésének ellenőrzése
            if is_filename_taken(file.filename, user_id):
                raise Exception("Filename already in use")

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
#ha ez sikertelen, akkor törlődjön a mappájából, vagy addig le se mentődjön
                raise HTTPException(500, 'Database error while updating files')
            
            #log
            file_responses.append({"file": file.filename, "status": "uploaded", "error": ''})

        except Exception as e:
            file_responses.append({"file": file.filename, "status": "failed", "error": str(e)})

    #logok visszaadása
    return file_responses
    return {"message": "Files processed successfully", "files": file_responses}

@app.get("/api/download")
async def download(
    request: Request, 
    filename: str,
    key_hex: Optional[str] = ""
):
    print('download')
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
        if user['has_key'] and verify_password(algo_request.key_hex, user['secret_key_hash']):
            try:
                #user titkos fájljainak kititkosítása
                decrypt_user_files(user_id, algo_request.key_hex, encrypted_files, user['algo'])

                #user titkos fájljainak újratitkosítása
                encrypt_user_files(user_id, algo_request.key_hex, encrypted_files, algo_request.algo)

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
    
    # A kulcsot nem bántjuk, egy kulccsal működik minden
    # Van titkosított fájl?
        # ha van => van titkos kulcs => megnézzük, hogy egyezik-e a megadottal
            # ha egyezik => kititkosítani mindent, újratitkosítani mindent, firssíteni az algot
            # ha nem => Error
        # ha nincs => simán lecseréljük az algoritmus
    
@app.get("/api/gen-sk")
async def gen_sk(request: Request, current_sk: Optional[str] = ""):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
            raise HTTPException(status_code=500, detail="Failed to update algorithm")
        
        #kulcs visszaadása
        return key_hex

@app.post("/api/verify-secret-key")
async def verify_sicret_key(request: Request, key_hex: str):
    #autentikáció
    user_id = authenticate_user(request.cookies.get("session_token"))
    user = supabase.table('user').select('*').eq('id', user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #validáció visszaadása
    return verify_password(key_hex, user['secret_key_hash'])


#######
########## DEPRACATED
####

def check_file_exists(file_path: str) -> bool:
    return os.path.exists(file_path)
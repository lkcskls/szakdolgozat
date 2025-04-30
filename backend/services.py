from contextlib import asynccontextmanager
import threading
from supabase import Client
from security import aes_encrypt_file, aes_decrypt_file, chacha20_encrypt_file, chacha20_decrypt_file
from pydantic import EmailStr
from pathlib import Path
from fastapi import FastAPI, HTTPException
from io import BytesIO
import shutil
import time
import os


#######
########## ON START-UP
####

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Server: setup ready")
    
    thread = threading.Thread(
        target=cleanup_folder, args=(5,"temp"), daemon=True
    )
    thread.start()

    yield
    
    print("🛑 Server: shutdown complete")

def cleanup_folder(wait_minutes=5, folder=None):
    if folder is None:
        return 0
    while(True):
        #jelenlegi fájlok lekárdezáse
        initial_files = {
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        }

        #várakozási idő
        print(f"{len(initial_files)} fájl várakozik törlésre. ({wait_minutes} perc)")
        time.sleep(wait_minutes * 60)

        #a wait_minutes perce a mappában lévő fájlok törlése
        deleted = []
        for filepath in initial_files:
            try:
                os.remove(filepath)
                deleted.append(filepath)
            except Exception as e:
                print(f"Nem sikerült törölni: {filepath} – {e}")

        print(f"{len(deleted)} fájl sikeresen törölve")


#######
########## USER FUNCTIONS
####

def is_email_taken(supabase: Client, email: EmailStr, user_id: int) -> bool:
    #email keresése az adatbázisban, a felhasználó kizárásával
    response = supabase.table("user").select("id").eq("email", email).neq("id", user_id).execute()
    return len(response.data) > 0 

def is_filename_taken(supabase: Client, filename: str, user_id: int) -> bool:
    response = (
        supabase
        .table("files")
        .select("id")
        .eq("filename", filename)
        .eq("user_id", user_id)
        .execute()
    )
    return len(response.data) > 0

def get_user_by_id(supabase: Client, user_id: str):
    try:
        response = supabase.table("user").select("*").eq("id", user_id).execute()
        users = response.data
    except:
        raise HTTPException(status_code=500, detail=f"Database error")

    #nincs user az adott id-vel, vagy több is van
    if not users or len(users)>1:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users[0]

def get_user_by_email(supabase: Client, email: EmailStr):
    try:
        response = supabase.table("user").select("*").eq("email", email).execute()
        users = response.data
    except:
        raise HTTPException(status_code=500, detail=f"Database error")

    #nincs user az adott email-lel, vagy több is van
    if not users or len(users)>1:
        raise HTTPException(status_code=404, detail="Invalid email or password")
    
    return users[0]



#######
########## FILE ENCRYPTION-DECRYPTION
####

def encrypt_file(file_content: bytes, output_path: Path, key_hex: str, algo: str):
    #kulcs átalakítása
    key_bytes = bytes.fromhex(key_hex)

    #output létrehozása, ha nincs
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #AES-256
    if algo == "AES-256":
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

def encrypt_user_files(user_id: str, key: str, files_to_encrypt: list, algo: str, from_dir:Path, to_dir:Path):
    #user mappájának ellenőrzése, létrehozása ha nincs
    user_upload_dir = Path(to_dir) / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    #fájlok feldolgozása
    for file in files_to_encrypt:
        #fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = from_dir / filename
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

    #AES-256
    if algo == "AES-256":
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

def decrypt_user_files(user_id: str, key: str, encrypted_files: list, algo: str, from_dir:Path, to_dir:Path):
    # átmeneti mappa ellenőrzése, ha kell létrehozása
    to_dir.mkdir(parents=True, exist_ok=True)

    # fájlok feldolgozása
    for file in encrypted_files:
        # fájlnév és útvonalak meghatározása
        filename = file['uuid']
        input_path = Path(from_dir / str(user_id) / filename)
        output_path = Path(to_dir / filename)

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
    print(f"Minden fájl kititkosítva ide: {to_dir}")

#######
########## IMPORTS
####

from itsdangerous import URLSafeTimedSerializer
from pydantic import EmailStr
from fastapi import Request, Response
from dotenv import load_dotenv
import secrets
import bcrypt
from io import BytesIO
import os


from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


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

#? Be lehet úgy állítani a session tokent, hogy a böngészőből is törlődjön a lejárat után

def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})

def set_session_cookie(response: Response, user_id: int):
    session_token = create_session(user_id)
    
    response.set_cookie(
        key="session_token", 
        value=session_token, 
        httponly=True,   # A JavaScript nem tudja olvasni (XSS védelem)
        secure=False,     # Csak HTTPS-en küldjük
        samesite="Lax",   # Lax: Megakadályozza a CSRF támadásokat
        max_age=SESSION_EXPIRY
    )

def verify_session(session_token: str):
    try:
        return serializer.loads(session_token, max_age=SESSION_EXPIRY)
    except:
        return None
    
def delete_session_cookie(response: Response):
    response.delete_cookie (
        key="session_token",
        httponly=True,  # HttpOnly beállítás
        secure=False,   # A Secure flag itt is fontos
        samesite="Lax", # Azonos samesite beállítás
        path="/"        # Ha az alapértelmezett path-on volt
    )



#######
########## BACKUP KEY FUNTIONS
####

def gen_backup_key(length: int = 16) -> str:
    return secrets.token_hex(length // 2) 



#######
########## ENCRYPTION-DECRYPTION
####

def generate_aes_key():
    return os.urandom(32)

# AES titkosítás a fájlhoz
def aes_encrypt_file(file: BytesIO, key: bytes):
    # Generálj egy egyedi inicializációs vektort (IV)
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Titkosítjuk a fájl tartalmát
    encrypted_file = BytesIO()
    encrypted_file.write(iv)  # Az IV-t először a fájlba írjuk

    # Fájl titkosítása blokkokban
    while chunk := file.read(1024):
        encrypted_chunk = encryptor.update(chunk)
        encrypted_file.write(encrypted_chunk)

    encrypted_file.write(encryptor.finalize())
    encrypted_file.write(encryptor.tag)  # Hozzáadjuk a tag-ot is

    encrypted_file.seek(0)  # Visszaállítjuk a fájlmutatót, hogy olvasható legyen
    #print("enc")
    return encrypted_file

# AES fájl visszafejtése
def aes_decrypt_file(encrypted_file: BytesIO, key: bytes) -> BytesIO:
    iv = encrypted_file.read(12)
    content = encrypted_file.read()

    if len(content) < 16:
        raise ValueError("Encrypted data too short.")

    encrypted_data = content[:-16]
    tag = content[-16:]

    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_file = BytesIO()
    decrypted_file.write(decryptor.update(encrypted_data))
    decrypted_file.write(decryptor.finalize())
    decrypted_file.seek(0)

    #print(f"IV length: {len(iv)} | Encrypted data length: {len(encrypted_data)} | Tag length: {len(tag)}")
    return decrypted_file
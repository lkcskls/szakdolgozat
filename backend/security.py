#######
########## IMPORTS
####

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from itsdangerous import URLSafeTimedSerializer
from pydantic import EmailStr
from fastapi import Request, Response
from dotenv import load_dotenv
from io import BytesIO
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
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="Lax",
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
        httponly=True,
        secure=False,
        samesite="Lax",
        path="/"
    )



#######
########## BACKUP KEY FUNTIONS
####

def gen_backup_key(length: int = 16) -> str:
    return secrets.token_hex(length // 2) 



#######
########## ENCRYPTION-DECRYPTION
####

def generate_key():
    return os.urandom(32)

#AES titkosítás
def aes_encrypt_file(file: BytesIO, key: bytes):
    #random inicializációs vektor generálás
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_file = BytesIO()

    #inicializációs vektor hozzáadása
    encrypted_file.write(iv)

    #fájl titkosítása blokkokban
    while chunk := file.read(1024):
        encrypted_chunk = encryptor.update(chunk)
        encrypted_file.write(encrypted_chunk)
    encrypted_file.write(encryptor.finalize())
    
    #tag hozzáadása
    encrypted_file.write(encryptor.tag)

    #fájlmutatót visszaállítása
    encrypted_file.seek(0)
    
    #titkosított fájl visszaadása
    return encrypted_file

#AES visszafejtés
def aes_decrypt_file(encrypted_file: BytesIO, key: bytes) -> BytesIO:
    #inicializációs vektor kiolvasása
    iv = encrypted_file.read(12)

    #fájl tartalmának olvasása
    content = encrypted_file.read()

    #fájl méretének ellenőrzése
    if len(content) < 16:
        raise ValueError("Encrypted data too short.")

    #titkosított adat és tag meghatározása
    encrypted_data = content[:-16]
    tag = content[-16:]


    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()

    #visszafejtett fájl létrehozása
    decrypted_file = BytesIO()
    decrypted_file.write(decryptor.update(encrypted_data))
    decrypted_file.write(decryptor.finalize())
    decrypted_file.seek(0)

    #visszafejtett fájl visszaadása
    return decrypted_file

#ChaCha20 titkosítás
def chacha20_encrypt_file(file: BytesIO, key: bytes) -> BytesIO:
    #ChaCha20-Poly1305 96 bites nonce generálás
    nonce = os.urandom(12) 

    plaintext = file.read() #nem biztos, hogy kell
    aead_cipher = ChaCha20Poly1305(key)
    ciphertext = aead_cipher.encrypt(nonce, plaintext, None)

    #titkosított fájl létrehozása
    encrypted_file = BytesIO()
    encrypted_file.write(nonce)
    encrypted_file.write(ciphertext)
    encrypted_file.seek(0)

    #titkosított fájl visszaadása
    return encrypted_file

#ChaCha20 visszafejtés
def chacha20_decrypt_file(encrypted_file: BytesIO, key: bytes) -> BytesIO:
    #nonce és a titkosított adat kiolvasása
    nonce = encrypted_file.read(12)
    ciphertext = encrypted_file.read()

    aead_cipher = ChaCha20Poly1305(key)
    plaintext = aead_cipher.decrypt(nonce, ciphertext, None)

    #visszafejtett fájl létrehozása
    decrypted_file = BytesIO()
    decrypted_file.write(plaintext)
    decrypted_file.seek(0)

    #visszafejtett fájl visszaadása
    return decrypted_file
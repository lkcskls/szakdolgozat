from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path
from server import app
import pytest
import uuid
import os



client = TestClient(app)



@pytest.fixture
def unique_user():
    return {
        "name": "Test Alany",
        "email": f"user_{uuid.uuid4().hex}@test.com",
        "password": "12345678"
    }



def test_register_success(unique_user):
    response = client.post("/api/register", json=unique_user)
    assert response.status_code == 200

def test_register_taken_email(unique_user):
    #helyes adatokkal
    response = client.post("/api/register", json=unique_user)
    assert response.status_code == 200

    #foglalt email
    response = client.post("/api/register", json=unique_user)
    assert response.status_code == 400

def test_register_invalid_name(unique_user):
    unique_user["name"] = "abc"
    response = client.post("/api/register", json=unique_user)
    assert response.status_code == 400
    assert response.json()["detail"] == "Name must be at least 5 characters"

def test_register_invalid_password(unique_user):
    unique_user["password"] = "123"
    response = client.post("/api/register", json=unique_user)
    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be at least 8 characters"



def test_login_success(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    response = client.post("/api/login", json={"email": unique_user["email"], "password": unique_user["password"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

def test_login_invalid_email(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    response = client.post("/api/login", json={"email": "wrong_email@test.com", "password": unique_user["password"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_login_invalid_password(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    response = client.post("/api/login", json={"email": unique_user["email"], "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"



def test_get_user_success(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    login_response = client.post("/api/login", json={"email": unique_user["email"], "password": unique_user["password"]})
    assert login_response.status_code == 200
    session_token = login_response.cookies["session_token"]  # A token megszerzése a válaszból

    #session_token
    client.cookies.set("session_token", session_token)
    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Alany"
    assert response.json()["email"] == unique_user["email"]
    assert response.json()["algo"] == "AES-256"

def test_get_user_unauthenticated():
    client.cookies.set("session_token", "wrong-session-token")
    response = client.get("/api/user")
    assert response.status_code == 401



def test_edit_user_success(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    login_response = client.post("/api/login", json={"email": unique_user["email"], "password": unique_user["password"]})
    assert login_response.status_code == 200

    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    #edit user
    response = client.put("/api/user", params={
        "name": "Új Teszt",
        "email": f"new_{uuid.uuid4().hex}@test.com"
    })

    assert response.status_code == 200
    assert response.json() == {"message": "User updated successfully"}

def test_edit_user_unauthenticated():
    client.cookies.set("session_token", "wrong-session-token")

    #edit user
    response = client.put("/api/user", params={
        "name": "Új Teszt",
        "email": f"new_{uuid.uuid4().hex}@test.com"
    })

    assert response.status_code == 401



def test_get_files_success(unique_user):
    #regisztráció
    client.post("/api/register", json=unique_user)

    #login
    login_response = client.post("/api/login", json={"email": unique_user["email"], "password": unique_user["password"]})
    assert login_response.status_code == 200

    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    #get files
    response = client.get("/api/files")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_files_unauthenticated():
    client.cookies.set("session_token", "wrong-session-token")

    #get files
    response = client.get("/api/files")
    assert response.status_code == 401



def test_gen_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    #gen sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    assert len(response.json()) == 64 

    #gen sk újra
    response = client.get("/api/gen-sk")
    assert response.status_code == 400

def test_file_upload_download_delete_success(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"files": (test_filename, f, "text/plain")}
        )

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "uploaded"
    assert result[0]["file"] == test_filename

    user_id = login_response.json()["user_id"]
    uploads_path = Path("uploads") / str(user_id)
    uploaded_files = list(uploads_path.glob("*.txt"))
    assert len(uploaded_files) == 1

    os.remove(test_filename)

    #download
    response = client.get( "/api/download", params={"filename": test_filename} )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f'attachment; filename="{test_filename}"'
    assert response.content == test_content

    response = client.delete( "/api/files", params={"filename": test_filename} )
    assert response.status_code == 200

def test_encrypted_file_upload_download_delete_success(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    key_hex = response.json()
    

    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":key_hex},
            files={"files": (test_filename, f, "text/plain")}
        )

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "uploaded"
    assert result[0]["file"] == test_filename

    user_id = login_response.json()["user_id"]
    uploads_path = Path("uploads") / str(user_id)
    uploaded_files = list(uploads_path.glob("*.txt"))
    assert len(uploaded_files) == 1

    os.remove(test_filename)

    #download
    response = client.get( "/api/download", params={"filename": test_filename, "key_hex": key_hex} )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == f'attachment; filename="{test_filename}"'
    assert response.content == test_content

    #delete
    response = client.delete( "/api/files", params={"filename": test_filename, "key_hex": key_hex} )
    assert response.status_code == 200

def test_encrypted_file_upload_no_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    #upload
    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)


    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True"},
            files={"files": (test_filename, f, "text/plain")}
        )

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "failed"
    assert result[0]["file"] == test_filename
    assert result[0]["error"] == "401: You don't have secret key"

def test_encrypted_file_upload_invalid_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    

    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":"wrong_key_hex"},
            files={"files": (test_filename, f, "text/plain")}
        )
    
    os.remove(test_filename)

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "failed"
    assert result[0]["file"] == test_filename
    assert result[0]["error"] == "401: Invalid secret key"

def test_encrypted_download_invalid_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    key_hex = response.json()
    
    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":key_hex},
            files={"files": (test_filename, f, "text/plain")}
        )

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "uploaded"
    assert result[0]["file"] == test_filename

    user_id = login_response.json()["user_id"]
    uploads_path = Path("uploads") / str(user_id)
    uploaded_files = list(uploads_path.glob("*.txt"))
    assert len(uploaded_files) == 1

    os.remove(test_filename)

    #download
    response = client.get( "/api/download", params={"filename": test_filename, "key_hex": "wrong-key-hex"} )
    assert response.status_code == 401
    assert response.json()['detail'] == "Invalid secret key"

def test_encrypted_delete_invalid_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200
    
    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    key_hex = response.json()
    
    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":key_hex},
            files={"files": (test_filename, f, "text/plain")}
        )

    assert response.status_code == 200
    result = response.json()
    assert result[0]["status"] == "uploaded"
    assert result[0]["file"] == test_filename

    user_id = login_response.json()["user_id"]
    uploads_path = Path("uploads") / str(user_id)
    uploaded_files = list(uploads_path.glob("*.txt"))
    assert len(uploaded_files) == 1

    os.remove(test_filename)

    #delete
    response = client.delete( "/api/files", params={"filename": test_filename, "key_hex": "wrong-key-hex"} )
    assert response.status_code == 401
    assert response.json()['detail'] == "Invalid secret key"



def test_algos():
    response = client.get("/api/algos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("name" in algo for algo in data)
    assert {'name': 'AES-256'} in response.json()
    assert {'name': 'ChaCha20'} in response.json()

def test_switch_algo_with_encrypted_files_success(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200

    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    #upload
    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    key_hex = response.json()
    
    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":key_hex},
            files={"files": (test_filename, f, "text/plain")}
        )
    
    os.remove(test_filename)

    #switch algo
    response = client.post("/api/switch-algo", json={"algo": "ChaCha20", "key_hex": key_hex})
    assert response.status_code == 200
    assert response.json() == {"message": "Algorithm updated to ChaCha20"}

def test_switch_algo_with_encrypted_files_invalid_sk(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200

    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)

    #gen-sk
    response = client.get("/api/gen-sk")
    assert response.status_code == 200
    key_hex = response.json()
    
    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True", "key_hex":key_hex},
            files={"files": (test_filename, f, "text/plain")}
        )

    os.remove(test_filename)

    #switch algo
    response = client.post("/api/switch-algo", json={"algo": "ChaCha20", "key_hex": "worng-key-hex"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid secret key"}

def test_switch_algo_with_no_encrypted_files(unique_user):
    #regisztráció
    register_response = client.post("/api/register", json=unique_user)
    assert register_response.status_code == 200

    #login
    login_response = client.post("/api/login", json={
        "email": unique_user["email"],
        "password": unique_user["password"]
    })
    assert login_response.status_code == 200

    #session_token
    session_token = login_response.cookies["session_token"]
    client.cookies.set("session_token", session_token)

    test_filename = "test_upload.txt"
    test_content = b"Teszt."
    with open(test_filename, "wb") as f:
        f.write(test_content)
    
    #upload
    with open(test_filename, "rb") as f:
        response = client.post(
            "/api/upload", params={"encrypted":"True"},
            files={"files": (test_filename, f, "text/plain")}
        )

    os.remove(test_filename)
    

    #switch algo
    response = client.post("/api/switch-algo", json={"algo": "ChaCha20"})
    assert response.status_code == 200
    assert response.json() == {"message": "Algorithm updated to ChaCha20"}

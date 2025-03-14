## POST: /register
#### BODY: 
  - name: str
  - email: EmailStr
  - second_email: EmailStr
  - password: str
#### SET:
  - id: int
  - password_hash: str
  - backup_key_hash: str
  - algo: str
  - has_key: boolean
  - key_number: int
  - encrypted_files: list[str]
#### RESPONSE:
  - user, backup_key | error 
  
## POST: /login
## POST: /logout
## GET: /user/{user_id}
## PUT: /user
## GET: /files/{filter}
## DEL: /files/{filename}
## POST: /upload
## GET: /download/{filename} 
## GET: /algos
## POST: /switch-algo

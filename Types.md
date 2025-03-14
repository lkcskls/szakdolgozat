# fastAPI:
## User:
    id: int #key
    name: str
    email: EmailStr
    second_email: EmailStr
    password_hash: str
    # backup_key_hash: str ez ne legyen benne a típusban, csak az adatbázisban
    algo: str
    has_key: boolean
    key_number: int
    encrypted_files: list[str]

# Next.js
Automatikusan generálódik az openapi dokumentációból, amit a fastapi készít.
npm install -g openapi-typescript  # vagy: npx openapi-typescript
npx openapi-typescript http://localhost:8000/openapi.json -o types/api.ts

package.json-ben be kell állítani, és így egyszerűbben futtatható
"scripts": {
  "generate-types": "npx openapi-typescript http://localhost:8000/api/openapi.json -o types/api.ts"
}
npm run generate-types

### Használat:
import { components } from "../types/api";
type User = components["schemas"]["User"];

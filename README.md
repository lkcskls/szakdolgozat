# Szakdolgozat
### Poszt-kvantum kriptográfiával védett fájltároló webszerver
A szerver működése kisebb felhasználószámra van optimalizálva, nagyobb felhasználószámnál a session alapú autentikáció kevésbé hatékonyan skálázható, kisebb méretben azonban biztonsági előnyei vannak.
Ideális lehet kisebb cégeknek, szervezeteknek saját fájlok biztonságos tárolására, esetleg családi felhasználásra.

## Követelmények a témabejelentő alapján:
-• Felhasználói fiók
  - Regisztáció
  -- Bejelentkezés
  -- Kijelentkezés
  - Adatok módosítása
-- Fájlkezelés
  -- Feltöltés
  -- Letöltés
  -- Titkosított tárolás
- Szerver
  - Poszt-kvantum kulcscsere (nem kell, hogy módosítható legyen)
  -- Titkosító algoritmus választható (csak a felhasználó fájljaira vonatkozik)
- TESZTELÉS

## Használt technológiák:
- Backend: fastAPI
- Frontend: Next.js
- Database: ? Supabase PostgerSQL (felhasználók tárolására)
- Fájltárolás: ? Supabase Storage
- (Gyorsítótár: Redis)

## Poszt-kvantum kulcscsere:
Open Quantum Safe OpenSSL provider-én keresztül.
[https://openquantumsafe.org/applications/tls.html#oqs-openssl-provider]
[https://github.com/open-quantum-safe/oqs-provider]

## Szükséges szerveroldali végpontok:
- POST: /register
- POST: /login
- POST: /logout
- GET: /user/{user_id}
- PUT: /user
- GET: /files/{filter}
- DEL: /files/{filename}
- POST: /upload
- GET: /download/{filename} 
- GET: /algos
- POST: /switch-algo

## Szerveroldali végpontok feladatai:
### POST: /register
- Felhasználói adatok hozzáadása az adatbázishoz.
- Megadott adatok ellenőrzése, type-check
- Megadható egy biztonsági email is
- Generálódik egy backup kulcs, amit a felhasználó szintén elmenthet vagy letölthet, ennek csak a hashelt változata tárolódik a USER.backup_key_hash mezőben. Elfelejtett jelszó esetén
- Regisztráció után:
  - Auto login
  - Default algoritmussal generál egy kulcsot, amit a felhasználó elmenthet egy jelszókezelőbe, vagy letöltheti egy autentikációs fájlként*.
    - *autentikációs fájl: a szerver a saját kulcsával titkosítja a felhasználó kulcsát, és ezt egy .txt fájlként letöltheti a felhasználó. Amikor ki akarja titkosítani a fájljait, akkor elég csak feltöltenie ezt a fájlt.
    - a felhasználó által generált/cserélt kulcsok száma az adatbázisban tárolódik, és az autentikációs fájl neve is attól függ, hogy hányadik generált kulcs, pl.: key_6.txt. És a felhasználói felület is valahogy utalna rá, hogy a 6-nak generált kulcsot kell, hogy megadja a felhasználó. Ezáltal tudni lehet, hogy melyik kulcs elavult, melyik nem, a fájl nevéből. 
- Response: user, backup_key | error
### POST: /login
- Megadott adatok ellenőrzése, type-check
- Megadott adatok összevetése az adatbázissal
- Siker esetén jwt token generálás
- Egy rövid timer
- Response: token, user | error
### POST: /logout
- AUTENTIKÁCIÓ
- token érvénytelenítése
- Response: message | error
### GET: /user/{user_id}
- AUTENTIKÁCIÓ
- Visszaadja a felhasználó adatait
- Response: user | error
### PUT: /user
- AUTENTIKÁCIÓ
- Felhasználói adatok felülírása a kapott adatokkal.
- Felülírható:
  - név
  - email
  - second_email
  - password
  - algo
- Visszaadja a felhasználót az új adatokkal
- Response: user | error
### GET: /files/{filter}
- AUTENTIKÁCIÓ
- Felhasználó fájljainak kilistázása a mappájából a szűrőfeltételeknek megfelelően
- Szűrő: - | kiterjesztés | fájlnév
- Response: message, [files] | error
### DEL: /files/{filename}
- AUTENTIKÁCIÓ
- Törli a fájlt, ha létezik.
- Ha a fájl titkosítva van, bekéri a kulcsot a felhasználótól.
- Választható soft-delete vagy hard delete, default: soft delete
  - soft: a felhasználó ".trash" mappájába kerül, x napon belül még visszaállítható, utána hard delete
  - hard: a fájl tárolási helye felülíródik 0 bitekkel, hogy ne lehessen visszaállítani
### POST: /upload
- AUTENTIKÁCIÓ
- Egy vagy több fájl is átadható
- Kapott fájlok ellenőrzése, pl.: létezik-e már ilyen nevű és kiterjesztésű fájl, fájlméret...
- Feltölti a fájlt a felhasználó mappájába, és csakis oda
- Választható a titkosított tárolás
  - A szerver végzi a titkosítást, ha már van generálva kulcs (adatbázisban tároljok, hogy igen/nem), akkor azt meg kell adnia a felhasználónak a body-ban.
  - Ha titkosított a tárolás, és még nincs kulcs, a generált kulcsot visszaadjuk
  - A fájl neve hozzáadódik a USER.encrypted_files mezőjéhez
  - Fontos, hogy a felhasználó összes titkosított fájlja egy kulccsal és algoritmussal legyen titkosítva   
- Force opció, ez fájlnév ütközés esetén újranevezi az új fájlt
- Response: message, skey | error
### GET: /download/{filename}
- AUTENTIKÁCIÓ
- Egy fájl visszaadására szolgál, (fastAPI.responses.FileResponse)
- Választható, hogy titkosítva vagy kititkosítva adja vissza a fájlt
- Ha több fájl kell, akkor kliens oldalon többször hívjuk ezt a végpontot
- Response: message, FileResponse | error
### GET: /algos
- AUTENTIKÁCIÓ
- Visszaadja a szerveroldalon engedélyezett algoritmusok listáját, kulcs-érték páronként
- A kulcs az algo neve, az érték pedig egy becsült relatív biztonság
- Response: list[key-value] | error
### POST: /switch-algo
- AUTENTIKÁCIÓ
- !Összetett művelet, kifejezetten figyelmesen kell megírni, hogy a fájlok ne sérülhessenek!
- Adatbázisban tárolódik a felhasználó által választott algoritmus
- Ha a felhasználó megváltoztatja, bekéri tőle a korábban (vagy default) generált kulcsot.
- A felhasználó kulcsával kititkosítja a titkosított fájlokat
- Generál egy új kulcsot a felhasználónak
- Letitkosítja a felhasználó korábban is titkosított fájljait
- Visszaadja a felhasználónak az új kulcsot, és az újratitkosított fájlok listáját.
- Response: message, skey, [files] | error

## Adatbázis
### USER tábla
A felhasználó által titkosított fájlok mindig egy algoritmussal, és egy kulccsal vannak titkosítva. Ellenkező esetben követhetetlen lenne, hogy melyik kulcs, melyik fájlhoz, és melyik algoritmushoz tartozik. Ezért kell a /switch-algo végponton algo cserénél újratitkosítani mindent
- id: int (key)
- name: str
- email: str
  - second_email: str | None
- password_hash: str
- backup_key_hash: str
- user_key_hash: str # a usernek adott kulcs hashe, amivel ellenőrizni lehet, hogy jó kulcsot adott-e meg
- algo: str
- has_key: boolean # nem biztos, hogy kell, lehet egyszerűbb, ha sokat van használva, de a key_numberből lehet tudni
- key_number: int = 0
- encrypted_files: list[str #file_names] | None #json-ként tárolva, feltöltés után a fájlnév nem módosítható!

## .env
- SUPABASE_URL=''
- SUPABASE_KEY=''
- SESSION_KEY=''

# Gondolkodtató:
- Mi legyen, ha a felhasználónak van kulcsa, de nincs titkosított fájlja? - Régi kulcs használata, hogy konzisztens legyen

## Fejelsztési potenciál
- mappaszerkezet létrehozása
- mappák megosztása
- felhasználói jogosultságkezelés
- autentikációs fájl
- feltöltés után módosítható fájlnevek
- választható soft vagy hard delete
- email ellenőrzése kóddal, authentikátorok használata
- már a felhasználói oldalon megtörténik a titkosítás, és így töltődik fel a szerverre, így nem kell bízni a szerverben sem
- minden meglévő fájl mentése egy zip-ként
- fiók törlése minden meglévő fájlal

## Jegyzetek:
felhasználó kulcsának tárolására txt helyett: one password


# Quickstart

## /:
        redis-cli shutdown
        redis-server

## /backend:
        python3 -m venv env
        source env/bin/activate
        pip install --no-cache-dir -r requirements.txt
        
        uvicorn server:app --host 0.0.0.0 --port 8000 --reload

## /frontend:
        npm i
        npm run generate-types
        npm run dev
        
        or

        npm run build
        npm start
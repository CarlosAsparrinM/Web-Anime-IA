import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import get_db
from models import ArticleModel
from agents.generator import generate_article
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(dotenv_path="../frontend/.env.local")

app = FastAPI(title="KenkoAnime AI Agents Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción cambiar por dominio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "KenkoAnime Backend Running"}

@app.get("/api/generate")
async def api_generate(secret: str = None, category: str = None, force: bool = False):
    expected_secret = os.getenv("CRON_SECRET")
    
    if secret != expected_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = get_db()
    articles_collection = db["articles"]

    if not force:
        # Simplistic check for today's article
        from datetime import datetime, timezone
        start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        existing = await articles_collection.find_one({"createdAt": {"$gte": start_of_day}})
        if existing:
            return JSONResponse(
                content={"message": "An article was already generated today. Use force=true to override."},
                status_code=200
            )

    try:
        generated_data = await generate_article(force_category=category)
        
        from datetime import datetime, timezone
        generated_data["createdAt"] = datetime.now(timezone.utc)
        generated_data["updatedAt"] = datetime.now(timezone.utc)
        
        # Validar con Pydantic antes de insertar
        validated_article = ArticleModel(**generated_data)
        insert_data = validated_article.model_dump()
        
        result = await articles_collection.insert_one(insert_data)
        insert_data["_id"] = str(result.inserted_id)
        
        # Remove datetime objects for JSON serialization
        insert_data["createdAt"] = insert_data["createdAt"].isoformat()
        insert_data["updatedAt"] = insert_data["updatedAt"].isoformat()

        return JSONResponse(
            content={"message": "Article generated and saved successfully.", "article": insert_data},
            status_code=201
        )
    except Exception as e:
        print(f"Error in /api/generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

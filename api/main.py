from fastapi import FastAPI
import json
from pathlib import Path

app = FastAPI(title="Wired Articles API")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "wired_articles.json"


@app.get("/")
def root():
    return {"message": "API aktif"}


@app.get("/articles")
def get_articles():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        articles = []

        if isinstance(payload, list) and len(payload) > 0:
            articles = payload[0].get("articles", [])
        elif isinstance(payload, dict):
            articles = payload.get("articles", [])

        return {
            "status": "success",
            "total": len(articles),
            "data": articles
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "File wired_articles.json tidak ditemukan"
        }

    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Format JSON tidak valid"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
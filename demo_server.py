"""
Demo server — shows the Slack bot flow in a browser without needing Slack.
Run: python3 demo_server.py
Then open: http://localhost:8080
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

from latam_client import get_modules, get_shows_from_module, update_module

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def serve_demo():
    with open(os.path.join(os.path.dirname(__file__), "demo.html")) as f:
        return f.read()


@app.get("/api/modules")
async def api_modules(language: str):
    try:
        modules = await get_modules(language)
        return {"modules": [
            {
                "module_id": m.get("module_id") or m.get("id"),
                "module_name": m.get("module_name") or m.get("name") or m.get("module_id"),
                "show_ids": get_shows_from_module([m], m.get("module_id") or str(m.get("id"))),
            }
            for m in modules
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateRequest(BaseModel):
    language: str
    module_id: str
    module_name: str
    show_ids: list[str]
    previous_show_ids: list[str]


@app.post("/api/update")
async def api_update(body: UpdateRequest):
    try:
        await update_module(body.language, body.module_id, body.show_ids)
        added   = [s for s in body.show_ids if s not in body.previous_show_ids]
        removed = [s for s in body.previous_show_ids if s not in body.show_ids]
        return {
            "ok": True,
            "added": added,
            "removed": removed,
            "total": len(body.show_ids),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

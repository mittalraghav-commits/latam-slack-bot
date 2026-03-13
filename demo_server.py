"""
Demo server — simulates the Slack bot flow in a browser.
Serves demo.html and proxies LATAM API calls.
Run: python demo_server.py
"""
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

BASE_URL = os.environ.get("LATAM_API_BASE_URL", "https://api.pocketfm.com/v3/content/internal")
HEADERS  = {"access-token": os.environ.get("LATAM_API_KEY", "")}
DEMO_HTML = HERE / "demo.html"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def serve_demo():
    return FileResponse(DEMO_HTML)


@app.get("/api/modules")
async def get_modules(language: str, locale: str = "MX"):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/latam_modules",
            params={"language": language, "locale": locale},
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.get("/api/module")
async def get_module(module_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/latam_module",
            params={"module_id": module_id},
            headers=HEADERS,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


class UpdateRequest(BaseModel):
    language: str
    module_id: str
    show_ids: list[str]


@app.put("/api/modules")
async def update_module(body: UpdateRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{BASE_URL}/latam_modules",
            params={
                "listOfEp": json.dumps(body.show_ids),
                "module_id": body.module_id,
                "language": body.language,
            },
            headers={**HEADERS, "content-type": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


if __name__ == "__main__":
    uvicorn.run("demo_server:app", host="0.0.0.0", port=8080, reload=True)

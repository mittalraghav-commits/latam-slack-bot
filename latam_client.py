import json
import httpx
from config import LATAM_API_BASE_URL, LATAM_API_KEY

BASE_URL = LATAM_API_BASE_URL or "https://api.pocketfm.com/v3/content/internal"
HEADERS = {"access-token": LATAM_API_KEY}


def _parse_entities(raw_entities) -> list[str]:
    """
    Parse the 'entities' field from a module object into an ordered list of show_ids.
    entities is a JSON string (or already a list) of [{show_id: rank}, ...] objects.
    Returns show_ids sorted by rank ascending (rank 1 = first).
    """
    if isinstance(raw_entities, str):
        parsed = json.loads(raw_entities)
    else:
        parsed = raw_entities or []
    sorted_items = sorted(parsed, key=lambda item: list(item.values())[0])
    return [list(item.keys())[0] for item in sorted_items]


async def get_modules(language: str, locale: str = "MX") -> list[dict]:
    """
    Fetch all modules for a language + locale.
    GET /latam_modules?language={language}&locale={locale}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/latam_modules",
            params={"language": language, "locale": locale},
            headers=HEADERS,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


def get_shows_from_module(modules: list[dict], module_id: str) -> list[str]:
    """
    Extract the current ordered show_ids for a module from the already-fetched
    modules list — no extra API call needed.
    """
    for m in modules:
        if m.get("module_id") == module_id:
            return _parse_entities(m.get("entities", "[]"))
    return []


async def get_module_shows(module_id: str) -> list[str]:
    """
    Fetch the current ordered show_ids for a module via a direct API call.
    Use get_shows_from_module() instead when you already have the modules list.
    GET /latam_module?module_id={module_id}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/latam_module",
            params={"module_id": module_id},
            headers=HEADERS,
        )
        resp.raise_for_status()
        module_data = resp.json().get("data", {})
        return _parse_entities(module_data.get("entities", "[]"))


async def update_module(language: str, module_id: str, show_ids: list[str]) -> dict:
    """
    Update the show list for a module.
    PUT /latam_modules?listOfEp=["id1","id2"]&module_id={id}&language={lang}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{BASE_URL}/latam_modules",
            params={
                "listOfEp": json.dumps(show_ids),
                "module_id": module_id,
                "language": language,
            },
            headers={**HEADERS, "content-type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

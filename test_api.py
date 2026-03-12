"""
Quick test script to verify the LATAM API client works correctly.
Run with: python3 test_api.py
Does NOT make any updates — read-only tests only.
"""
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

from latam_client import get_modules, get_module_shows

TEST_LANGUAGES = ["fr", "pt", "es"]


async def main():
    for lang in TEST_LANGUAGES:
        print(f"\n{'='*60}")
        print(f"  Language: {lang.upper()}")
        print(f"{'='*60}")

        # --- 1. Fetch modules ---
        print(f"\n[1] Fetching modules for '{lang}'...")
        try:
            modules = await get_modules(lang)
            print(f"    ✅ Got {len(modules)} modules")
            if not modules:
                print("    ⚠️  No modules returned — skipping")
                continue

            # Print first 3 modules as a preview
            for m in modules[:3]:
                print(f"       • {m}")
        except Exception as e:
            print(f"    ❌ Failed: {e}")
            continue

        # --- 2. Fetch shows for the first module ---
        first_module = modules[0]
        # The module ID field — check what key contains the ID
        module_id = (
            first_module.get("module_id")
            or first_module.get("id")
            or first_module.get("_id")
        )
        module_name = (
            first_module.get("name")
            or first_module.get("title")
            or module_id
        )

        print(f"\n[2] Fetching shows for module: '{module_name}' (id={module_id})...")
        try:
            shows = await get_module_shows(module_id)
            print(f"    ✅ Got {len(shows)} shows")
            for i, show_id in enumerate(shows[:5], 1):
                print(f"       {i}. {show_id}")
            if len(shows) > 5:
                print(f"       ... and {len(shows) - 5} more")
        except Exception as e:
            print(f"    ❌ Failed: {e}")

    print(f"\n{'='*60}")
    print("  Test complete — no updates were made.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

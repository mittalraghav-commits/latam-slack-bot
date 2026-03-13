import json
import asyncio
import logging
from typing import Optional

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from latam_client import get_modules, get_shows_from_module, get_module_shows, update_module
from modals import build_initial_modal, build_modal_with_modules, build_modal_with_shows, DEFAULT_LOCALE
from roles import get_allowed_languages, assert_authorized_for_language, invalidate_cache, UnauthorizedError
from audit import post_audit_log

logging.basicConfig(level=logging.INFO)

bolt_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
handler  = SlackRequestHandler(bolt_app)
api      = FastAPI()

loop = asyncio.new_event_loop()


# ── 1. Slash command — check roles, open modal with only allowed languages ─────

@bolt_app.command("/update-latam-module")
def open_modal(ack, command, client):
    ack()
    user_id    = command["user_id"]
    channel_id = command["channel_id"]

    try:
        allowed_languages = get_allowed_languages(client, user_id)
    except UnauthorizedError:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=(
                ":no_entry: *Access denied.*\n"
                "You don't have permission to update LATAM modules.\n"
                "Contact your team lead to be added to the relevant *LATAM Editors* group."
            ),
        )
        return

    metadata = json.dumps({"channel_id": channel_id, "allowed_languages": allowed_languages})
    client.views_open(
        trigger_id=command["trigger_id"],
        view=build_initial_modal(private_metadata=metadata, allowed_languages=allowed_languages),
    )


# ── 2. Language selected — load modules ────────────────────────────────────────

def _get_locale_from_state(view_state: dict) -> str:
    try:
        return view_state["locale_block"]["locale_select"]["selected_option"]["value"]
    except (KeyError, TypeError):
        return DEFAULT_LOCALE


def _get_language_from_state(view_state: dict) -> Optional[str]:
    try:
        return view_state["language_block"]["language_select"]["selected_option"]["value"]
    except (KeyError, TypeError):
        return None


@bolt_app.action("language_select")
def on_language_selected(ack, body, client):
    ack()
    language          = body["actions"][0]["selected_option"]["value"]
    view_id           = body["view"]["id"]
    hash_             = body["view"]["hash"]
    metadata          = json.loads(body["view"].get("private_metadata", "{}"))
    allowed_languages = metadata.get("allowed_languages")
    locale            = _get_locale_from_state(body["view"]["state"]["values"])

    modules = loop.run_until_complete(get_modules(language, locale))

    client.views_update(
        view_id=view_id,
        hash=hash_,
        view=build_modal_with_modules(
            modules,
            private_metadata=json.dumps(metadata),
            selected_language=language,
            selected_locale=locale,
            allowed_languages=allowed_languages,
        ),
    )


@bolt_app.action("locale_select")
def on_locale_selected(ack, body, client):
    ack()
    locale            = body["actions"][0]["selected_option"]["value"]
    view_id           = body["view"]["id"]
    hash_             = body["view"]["hash"]
    metadata          = json.loads(body["view"].get("private_metadata", "{}"))
    allowed_languages = metadata.get("allowed_languages")
    language          = _get_language_from_state(body["view"]["state"]["values"])

    if not language:
        return  # language not selected yet, wait

    modules = loop.run_until_complete(get_modules(language, locale))

    client.views_update(
        view_id=view_id,
        hash=hash_,
        view=build_modal_with_modules(
            modules,
            private_metadata=json.dumps(metadata),
            selected_language=language,
            selected_locale=locale,
            allowed_languages=allowed_languages,
        ),
    )


# ── 3. Module selected — show current shows + pre-fill input ──────────────────

@bolt_app.action("module_select")
def on_module_selected(ack, body, client):
    ack()
    view_id           = body["view"]["id"]
    hash_             = body["view"]["hash"]
    metadata          = json.loads(body["view"].get("private_metadata", "{}"))
    allowed_languages = metadata.get("allowed_languages")
    values            = body["view"]["state"]["values"]

    language      = values["language_block"]["language_select"]["selected_option"]["value"]
    locale        = _get_locale_from_state(values)
    module_option = body["actions"][0]["selected_option"]
    module_id     = module_option["value"]
    module_name   = module_option["text"]["text"]

    modules          = loop.run_until_complete(get_modules(language, locale))
    current_show_ids = loop.run_until_complete(get_module_shows(module_id))

    client.views_update(
        view_id=view_id,
        hash=hash_,
        view=build_modal_with_shows(
            modules,
            current_show_ids,
            private_metadata=json.dumps(metadata),
            selected_language=language,
            selected_locale=locale,
            selected_module_id=module_id,
            selected_module_name=module_name,
            allowed_languages=allowed_languages,
        ),
    )


# ── 4. Modal submitted — validate, update, post audit log ─────────────────────

@bolt_app.view("latam_module_update")
def on_submit(ack, body, client, view):
    values     = view["state"]["values"]
    metadata   = json.loads(view.get("private_metadata") or "{}")
    channel_id = metadata.get("channel_id")

    language    = values["language_block"]["language_select"]["selected_option"]["value"]
    module_id   = values["module_block"]["module_select"]["selected_option"]["value"]
    module_name = values["module_block"]["module_select"]["selected_option"]["text"]["text"]
    raw_input   = values["show_ids_block"]["show_ids_input"]["value"].strip()

    user_id   = body["user"]["id"]
    user_name = body["user"]["name"]

    # Re-check authorization for this specific language on submit (defence in depth)
    try:
        assert_authorized_for_language(client, user_id, language)
    except UnauthorizedError:
        ack(response_action="errors", errors={
            "show_ids_block": f"You don't have permission to update {language} modules."
        })
        return

    # Validate show_ids format
    try:
        new_show_ids = json.loads(raw_input)
        if not isinstance(new_show_ids, list) or not all(isinstance(s, str) for s in new_show_ids):
            raise ValueError
        if len(new_show_ids) == 0:
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        ack(response_action="errors", errors={
            "show_ids_block": (
                'Must be a non-empty JSON array of strings.\n'
                'Example: ["showId1", "showId2", "showId3"]'
            )
        })
        return

    ack()

    try:
        previous_show_ids = loop.run_until_complete(get_module_shows(module_id))
        loop.run_until_complete(update_module(language, module_id, new_show_ids))

        post_audit_log(
            client,
            channel=channel_id,
            slack_user_id=user_id,
            slack_user_name=user_name,
            language=language,
            module_id=module_id,
            module_name=module_name,
            previous_show_ids=previous_show_ids,
            new_show_ids=new_show_ids,
        )

    except Exception as e:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=(
                f":x: *Update failed*\n"
                f"> *Module:* {module_name} (`{module_id}`)\n"
                f"> *Error:* `{str(e)}`"
            ),
        )


# ── Admin endpoints ────────────────────────────────────────────────────────────

@api.post("/admin/invalidate-role-cache")
async def invalidate_role_cache():
    """Call this after updating Slack usergroup membership to refresh the cache."""
    invalidate_cache()
    return {"status": "ok", "message": "Role cache cleared."}


# ── FastAPI / Slack event routes ───────────────────────────────────────────────

@api.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@api.post("/slack/actions")
async def slack_actions(req: Request):
    return await handler.handle(req)

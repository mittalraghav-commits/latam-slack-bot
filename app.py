import json
import asyncio
import logging
from typing import Optional

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from latam_client import get_modules, get_module_shows, update_module
from modals import (
    build_initial_modal,
    build_modal_with_modules,
    build_modal_with_operation_select,
    build_modal_for_remove,
    build_modal_for_add,
    build_modal_for_rerank,
    DEFAULT_LOCALE,
    OPERATION_REMOVE,
    OPERATION_ADD,
    OPERATION_RERANK,
)
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


# ── 3. Module selected — show current shows + operation picker ─────────────────

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
        view=build_modal_with_operation_select(
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


# ── 4. Operation selected — show targeted input UI ─────────────────────────────

_OPERATION_BUILDERS = {
    OPERATION_REMOVE: build_modal_for_remove,
    OPERATION_ADD:    build_modal_for_add,
    OPERATION_RERANK: build_modal_for_rerank,
}


@bolt_app.action("operation_select")
def on_operation_selected(ack, body, client):
    ack()
    operation         = body["actions"][0]["selected_option"]["value"]
    view_id           = body["view"]["id"]
    hash_             = body["view"]["hash"]
    metadata          = json.loads(body["view"].get("private_metadata", "{}"))
    allowed_languages = metadata.get("allowed_languages")
    values            = body["view"]["state"]["values"]

    language      = values["language_block"]["language_select"]["selected_option"]["value"]
    locale        = _get_locale_from_state(values)
    module_option = values["module_block"]["module_select"]["selected_option"]
    module_id     = module_option["value"]
    module_name   = module_option["text"]["text"]

    build_fn = _OPERATION_BUILDERS.get(operation)
    if not build_fn:
        return

    modules          = loop.run_until_complete(get_modules(language, locale))
    current_show_ids = loop.run_until_complete(get_module_shows(module_id))

    client.views_update(
        view_id=view_id,
        hash=hash_,
        view=build_fn(
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


# ── 5. Modal submitted — validate, compute new list, update, post audit log ────

@bolt_app.view("latam_module_update")
def on_submit(ack, body, client, view):
    values     = view["state"]["values"]
    metadata   = json.loads(view.get("private_metadata") or "{}")
    channel_id = metadata.get("channel_id")

    language    = values["language_block"]["language_select"]["selected_option"]["value"]
    module_id   = values["module_block"]["module_select"]["selected_option"]["value"]
    module_name = values["module_block"]["module_select"]["selected_option"]["text"]["text"]

    user_id   = body["user"]["id"]
    user_name = body["user"]["name"]

    # Re-check authorization (defence in depth)
    try:
        assert_authorized_for_language(client, user_id, language)
    except UnauthorizedError:
        ack(response_action="errors", errors={
            "language_block": f"You don't have permission to update {language} modules."
        })
        return

    # Read operation
    operation_opt = (
        values.get("operation_block", {})
              .get("operation_select", {})
              .get("selected_option")
    )
    if not operation_opt:
        ack(response_action="errors", errors={
            "operation_block": "Please select what you want to do."
        })
        return
    operation = operation_opt["value"]

    # Read and parse entered show IDs (one per line)
    raw_input  = (values.get("show_ids_block", {}).get("show_ids_input", {}).get("value") or "").strip()
    entered_ids = [line.strip() for line in raw_input.splitlines() if line.strip()]

    if not entered_ids:
        ack(response_action="errors", errors={
            "show_ids_block": "Please enter at least one show ID."
        })
        return

    ack()

    try:
        previous_show_ids = loop.run_until_complete(get_module_shows(module_id))

        if operation == OPERATION_REMOVE:
            not_found = [s for s in entered_ids if s not in previous_show_ids]
            if not_found:
                client.chat_postEphemeral(
                    channel=channel_id, user=user_id,
                    text=(
                        ":x: *Update failed:* These show IDs are not in the module:\n"
                        + "\n".join(f"• `{s}`" for s in not_found)
                    ),
                )
                return
            new_show_ids = [s for s in previous_show_ids if s not in entered_ids]
            if not new_show_ids:
                client.chat_postEphemeral(
                    channel=channel_id, user=user_id,
                    text=":x: *Update cancelled:* Removing all shows from a module is not allowed.",
                )
                return

        elif operation == OPERATION_ADD:
            already_in = [s for s in entered_ids if s in previous_show_ids]
            if already_in:
                client.chat_postEphemeral(
                    channel=channel_id, user=user_id,
                    text=(
                        ":x: *Update failed:* These show IDs are already in the module:\n"
                        + "\n".join(f"• `{s}`" for s in already_in)
                    ),
                )
                return

            new_show_ids = previous_show_ids + entered_ids

        elif operation == OPERATION_RERANK:
            if set(entered_ids) != set(previous_show_ids):
                missing = set(previous_show_ids) - set(entered_ids)
                extra   = set(entered_ids) - set(previous_show_ids)
                lines   = []
                if missing:
                    lines.append("Missing: " + ", ".join(f"`{s}`" for s in sorted(missing)))
                if extra:
                    lines.append("Unknown: " + ", ".join(f"`{s}`" for s in sorted(extra)))
                client.chat_postEphemeral(
                    channel=channel_id, user=user_id,
                    text=":x: *Update failed:* Re-rank must contain exactly the same shows.\n" + "\n".join(lines),
                )
                return
            new_show_ids = entered_ids

        else:
            return  # unknown operation, do nothing

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

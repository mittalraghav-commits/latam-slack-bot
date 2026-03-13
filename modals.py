from typing import Optional

# Ordered list of all supported languages — (API key, display label)
ALL_LANGUAGES = [
    ("fr",         "French (FR)"),
    ("german",     "German (DE)"),
    ("spanish",    "Spanish (ES)"),
    ("portuguese", "Portuguese (BR)"),
]


def _language_options(allowed_languages: list[str]) -> list[dict]:
    """Build Slack option blocks for only the languages the user may access."""
    return [
        {"text": {"type": "plain_text", "text": label}, "value": key}
        for key, label in ALL_LANGUAGES
        if key in allowed_languages
    ]


def _language_initial_option(language: str) -> dict:
    label = next((label for key, label in ALL_LANGUAGES if key == language), language)
    return {"text": {"type": "plain_text", "text": label}, "value": language}


def build_initial_modal(
    private_metadata: str = "{}",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 1 — language picker. Only shows languages the user is allowed to edit."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type":        "static_select",
                    "action_id":   "language_select",
                    "placeholder": {"type": "plain_text", "text": "Select a language"},
                    "options":     _language_options(allowed_languages),
                },
            },
            {
                "type": "section",
                "block_id": "module_placeholder_block",
                "text": {"type": "mrkdwn", "text": "_Select a language above to load modules._"},
            },
        ],
    }


def build_modal_with_modules(
    modules: list[dict],
    private_metadata: str = "{}",
    selected_language: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 2 — language chosen, module dropdown populated."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    module_options = [
        {
            "text":  {"type": "plain_text", "text": m.get("module_name") or m.get("name") or m["module_id"]},
            "value": m["module_id"],
        }
        for m in modules
    ]

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type":           "static_select",
                    "action_id":      "language_select",
                    "placeholder":    {"type": "plain_text", "text": "Select a language"},
                    "initial_option": _language_initial_option(selected_language),
                    "options":        _language_options(allowed_languages),
                },
            },
            {
                "type": "input",
                "block_id": "module_block",
                "label": {"type": "plain_text", "text": "Module"},
                "element": {
                    "type":        "static_select",
                    "action_id":   "module_select",
                    "placeholder": {"type": "plain_text", "text": "Select a module"},
                    "options":     module_options,
                },
            },
            {
                "type": "section",
                "block_id": "current_shows_placeholder_block",
                "text": {"type": "mrkdwn", "text": "_Select a module above to preview its current shows._"},
            },
        ],
    }


def build_modal_with_shows(
    modules: list[dict],
    current_show_ids: list[str],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_module_id: str = "",
    selected_module_name: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 3 — module chosen. Shows current show list and the prefilled input."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    module_options = [
        {
            "text":  {"type": "plain_text", "text": m.get("module_name") or m.get("name") or m["module_id"]},
            "value": m["module_id"],
        }
        for m in modules
    ]

    if current_show_ids:
        shows_preview   = "\n".join(f"{i+1}. `{s}`" for i, s in enumerate(current_show_ids))
        prefilled_value = '[\n' + ',\n'.join(f'  "{s}"' for s in current_show_ids) + '\n]'
    else:
        shows_preview   = "_No shows currently assigned._"
        prefilled_value = ""

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type":           "static_select",
                    "action_id":      "language_select",
                    "initial_option": _language_initial_option(selected_language),
                    "options":        _language_options(allowed_languages),
                },
            },
            {
                "type": "input",
                "block_id": "module_block",
                "label": {"type": "plain_text", "text": "Module"},
                "element": {
                    "type":           "static_select",
                    "action_id":      "module_select",
                    "initial_option": {
                        "text":  {"type": "plain_text", "text": selected_module_name},
                        "value": selected_module_id,
                    },
                    "options": module_options,
                },
            },
            {
                "type": "section",
                "block_id": "current_shows_block",
                "text": {
                    "type": "mrkdwn",
                    "text": f":eyes: *Current shows in `{selected_module_name}` ({len(current_show_ids)} shows):*\n{shows_preview}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "block_id": "format_hint_block",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        ":pencil2: *Provide the new ordered list of show IDs as a JSON array:*\n"
                        "```[\n  \"showId1\",\n  \"showId2\",\n  \"showId3\"\n]```\n"
                        "_The list replaces the module entirely — include all shows you want to keep, in order._"
                    ),
                },
            },
            {
                "type": "input",
                "block_id": "show_ids_block",
                "label": {"type": "plain_text", "text": "New Show IDs"},
                "element": {
                    "type":          "plain_text_input",
                    "action_id":     "show_ids_input",
                    "multiline":     True,
                    "initial_value": prefilled_value,
                    "placeholder":   {"type": "plain_text", "text": '["showId1", "showId2", "showId3"]'},
                },
            },
        ],
    }

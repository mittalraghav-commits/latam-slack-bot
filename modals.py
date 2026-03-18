from typing import Optional

# Ordered list of all supported languages — (API key, display label)
ALL_LANGUAGES = [
    ("fr",         "French (FR)"),
    ("german",     "German (DE)"),
    ("spanish",    "Spanish (ES)"),
    ("portuguese", "Portuguese (BR)"),
]

# All supported locales — (locale code, display label)
ALL_LOCALES = [
    ("FR", "France (FR)"),
    ("DE", "Germany (DE)"),
    ("ES", "Spain (ES)"),
    ("PT", "Portugal (PT)"),
    ("BR", "Brazil (BR)"),
    ("MX", "Mexico (MX)"),
    ("AR", "Argentina (AR)"),
    ("CO", "Colombia (CO)"),
    ("CL", "Chile (CL)"),
    ("PE", "Peru (PE)"),
    ("EC", "Ecuador (EC)"),
    ("BO", "Bolivia (BO)"),
    ("PY", "Paraguay (PY)"),
    ("UY", "Uruguay (UY)"),
    ("VE", "Venezuela (VE)"),
]

DEFAULT_LOCALE = "MX"

# Operation types
OPERATION_REMOVE = "remove"
OPERATION_ADD    = "add"
OPERATION_RERANK = "rerank"

_OPERATION_OPTIONS = [
    (OPERATION_REMOVE, ":heavy_minus_sign:  Remove shows"),
    (OPERATION_ADD,    ":heavy_plus_sign:  Add shows"),
    (OPERATION_RERANK, ":1234:  Re-rank shows"),
]


# ── Private helpers ────────────────────────────────────────────────────────────

def _language_options(allowed_languages: list[str]) -> list[dict]:
    return [
        {"text": {"type": "plain_text", "text": label}, "value": key}
        for key, label in ALL_LANGUAGES
        if key in allowed_languages
    ]


def _language_initial_option(language: str) -> dict:
    label = next((label for key, label in ALL_LANGUAGES if key == language), language)
    return {"text": {"type": "plain_text", "text": label}, "value": language}


def _locale_options() -> list[dict]:
    return [
        {"text": {"type": "plain_text", "text": label}, "value": key}
        for key, label in ALL_LOCALES
    ]


def _locale_initial_option(locale: str) -> dict:
    label = next((label for key, label in ALL_LOCALES if key == locale), locale)
    return {"text": {"type": "plain_text", "text": label}, "value": locale}


def _module_options(modules: list[dict]) -> list[dict]:
    return [
        {
            "text":  {"type": "plain_text", "text": m.get("module_name") or m.get("name") or m["module_id"]},
            "value": m["module_id"],
        }
        for m in modules
    ]


def _module_initial_option(module_id: str, module_name: str) -> dict:
    return {"text": {"type": "plain_text", "text": module_name}, "value": module_id}


def _operation_options() -> list[dict]:
    return [
        {"text": {"type": "plain_text", "text": label}, "value": value}
        for value, label in _OPERATION_OPTIONS
    ]


def _operation_initial_option(operation: str) -> dict:
    label = next((label for value, label in _OPERATION_OPTIONS if value == operation), operation)
    return {"text": {"type": "plain_text", "text": label}, "value": operation}


def _shows_preview_text(module_name: str, show_ids: list[str]) -> str:
    if show_ids:
        lines = "\n".join(f"{i+1}. `{s}`" for i, s in enumerate(show_ids))
        return f":eyes: *Current shows in `{module_name}` ({len(show_ids)} shows):*\n{lines}"
    return f":eyes: *`{module_name}`* has no shows currently assigned."


def _language_block(selected_language: str, allowed_languages: list[str]) -> dict:
    return {
        "type":            "input",
        "block_id":        "language_block",
        "dispatch_action": True,
        "label":           {"type": "plain_text", "text": "Language"},
        "element": {
            "type":           "static_select",
            "action_id":      "language_select",
            "initial_option": _language_initial_option(selected_language),
            "options":        _language_options(allowed_languages),
        },
    }


def _locale_block(selected_locale: str) -> dict:
    return {
        "type":            "input",
        "block_id":        "locale_block",
        "dispatch_action": True,
        "label":           {"type": "plain_text", "text": "Country / Locale"},
        "element": {
            "type":           "static_select",
            "action_id":      "locale_select",
            "options":        _locale_options(),
            "initial_option": _locale_initial_option(selected_locale),
        },
    }


def _module_block(modules: list[dict], module_id: str, module_name: str) -> dict:
    return {
        "type":            "input",
        "block_id":        "module_block",
        "dispatch_action": True,
        "label":           {"type": "plain_text", "text": "Module"},
        "element": {
            "type":           "static_select",
            "action_id":      "module_select",
            "initial_option": _module_initial_option(module_id, module_name),
            "options":        _module_options(modules),
        },
    }


def _operation_block(selected_operation: Optional[str] = None) -> dict:
    element: dict = {
        "type":      "static_select",
        "action_id": "operation_select",
        "options":   _operation_options(),
    }
    if selected_operation:
        element["initial_option"] = _operation_initial_option(selected_operation)
    else:
        element["placeholder"] = {"type": "plain_text", "text": "Select an operation"}

    return {
        "type":            "input",
        "block_id":        "operation_block",
        "dispatch_action": True,
        "label":           {"type": "plain_text", "text": "What do you want to do?"},
        "element":         element,
    }


# ── Step 1 — language + locale picker ─────────────────────────────────────────

def build_initial_modal(
    private_metadata: str = "{}",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
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
                "type":            "input",
                "block_id":        "language_block",
                "dispatch_action": True,
                "label":           {"type": "plain_text", "text": "Language"},
                "element": {
                    "type":        "static_select",
                    "action_id":   "language_select",
                    "placeholder": {"type": "plain_text", "text": "Select a language"},
                    "options":     _language_options(allowed_languages),
                },
            },
            {
                "type":            "input",
                "block_id":        "locale_block",
                "dispatch_action": True,
                "label":           {"type": "plain_text", "text": "Country / Locale"},
                "element": {
                    "type":           "static_select",
                    "action_id":      "locale_select",
                    "placeholder":    {"type": "plain_text", "text": "Select a country"},
                    "options":        _locale_options(),
                    "initial_option": _locale_initial_option(DEFAULT_LOCALE),
                },
            },
            {
                "type": "section",
                "block_id": "module_placeholder_block",
                "text": {"type": "mrkdwn", "text": "_Select a language and country above to load modules._"},
            },
        ],
    }


# ── Step 2 — module picker ─────────────────────────────────────────────────────

def build_modal_with_modules(
    modules: list[dict],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_locale: str = DEFAULT_LOCALE,
    allowed_languages: Optional[list[str]] = None,
) -> dict:
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
            _language_block(selected_language, allowed_languages),
            _locale_block(selected_locale),
            {
                "type":            "input",
                "block_id":        "module_block",
                "dispatch_action": True,
                "label":           {"type": "plain_text", "text": "Module"},
                "element": {
                    "type":        "static_select",
                    "action_id":   "module_select",
                    "placeholder": {"type": "plain_text", "text": "Select a module"},
                    "options":     _module_options(modules),
                },
            },
            {
                "type": "section",
                "block_id": "current_shows_placeholder_block",
                "text": {"type": "mrkdwn", "text": "_Select a module above to continue._"},
            },
        ],
    }


# ── Step 3 — operation picker ──────────────────────────────────────────────────

def build_modal_with_operation_select(
    modules: list[dict],
    current_show_ids: list[str],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_locale: str = DEFAULT_LOCALE,
    selected_module_id: str = "",
    selected_module_name: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 3 — module chosen. Pick what you want to do."""
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
            _language_block(selected_language, allowed_languages),
            _locale_block(selected_locale),
            _module_block(modules, selected_module_id, selected_module_name),
            {
                "type": "section",
                "block_id": "current_shows_block",
                "text": {
                    "type": "mrkdwn",
                    "text": _shows_preview_text(selected_module_name, current_show_ids),
                },
            },
            {"type": "divider"},
            _operation_block(),
        ],
    }


# ── Step 4a — Remove ───────────────────────────────────────────────────────────

def build_modal_for_remove(
    modules: list[dict],
    current_show_ids: list[str],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_locale: str = DEFAULT_LOCALE,
    selected_module_id: str = "",
    selected_module_name: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 4a — enter show IDs to remove, one per line."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Remove & Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            _language_block(selected_language, allowed_languages),
            _locale_block(selected_locale),
            _module_block(modules, selected_module_id, selected_module_name),
            {
                "type": "section",
                "block_id": "current_shows_block",
                "text": {
                    "type": "mrkdwn",
                    "text": _shows_preview_text(selected_module_name, current_show_ids),
                },
            },
            {"type": "divider"},
            _operation_block(OPERATION_REMOVE),
            {
                "type": "section",
                "block_id": "instruction_block",
                "text": {
                    "type": "mrkdwn",
                    "text": ":heavy_minus_sign: *Which shows do you want to remove?*\nEnter one show ID per line.",
                },
            },
            {
                "type": "input",
                "block_id": "show_ids_block",
                "label": {"type": "plain_text", "text": "Show IDs to remove"},
                "element": {
                    "type":        "plain_text_input",
                    "action_id":   "show_ids_input",
                    "multiline":   True,
                    "placeholder": {"type": "plain_text", "text": "showId1\nshowId2"},
                },
            },
        ],
    }


# ── Step 4b — Add ─────────────────────────────────────────────────────────────

def build_modal_for_add(
    modules: list[dict],
    current_show_ids: list[str],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_locale: str = DEFAULT_LOCALE,
    selected_module_id: str = "",
    selected_module_name: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 4b — enter show IDs to add (appended to end)."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Add & Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            _language_block(selected_language, allowed_languages),
            _locale_block(selected_locale),
            _module_block(modules, selected_module_id, selected_module_name),
            {
                "type": "section",
                "block_id": "current_shows_block",
                "text": {
                    "type": "mrkdwn",
                    "text": _shows_preview_text(selected_module_name, current_show_ids),
                },
            },
            {"type": "divider"},
            _operation_block(OPERATION_ADD),
            {
                "type": "section",
                "block_id": "instruction_block",
                "text": {
                    "type": "mrkdwn",
                    "text": ":heavy_plus_sign: *Which shows do you want to add?*\nEnter one show ID per line. They will be appended to the end of the module.",
                },
            },
            {
                "type": "input",
                "block_id": "show_ids_block",
                "label": {"type": "plain_text", "text": "Show IDs to add"},
                "element": {
                    "type":        "plain_text_input",
                    "action_id":   "show_ids_input",
                    "multiline":   True,
                    "placeholder": {"type": "plain_text", "text": "showId4\nshowId5"},
                },
            },
        ],
    }


# ── Step 4c — Re-rank ─────────────────────────────────────────────────────────

def build_modal_for_rerank(
    modules: list[dict],
    current_show_ids: list[str],
    private_metadata: str = "{}",
    selected_language: str = "",
    selected_locale: str = DEFAULT_LOCALE,
    selected_module_id: str = "",
    selected_module_name: str = "",
    allowed_languages: Optional[list[str]] = None,
) -> dict:
    """Step 4c — shows pre-filled one per line; user reorders them."""
    if allowed_languages is None:
        allowed_languages = [key for key, _ in ALL_LANGUAGES]

    prefilled = "\n".join(current_show_ids)

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Reorder & Update"},
        "close":  {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            _language_block(selected_language, allowed_languages),
            _locale_block(selected_locale),
            _module_block(modules, selected_module_id, selected_module_name),
            {"type": "divider"},
            _operation_block(OPERATION_RERANK),
            {
                "type": "section",
                "block_id": "instruction_block",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        ":1234: *Re-order the shows below.*\n"
                        "Edit the list — one show ID per line, in your desired order.\n"
                        "_Must contain exactly the same shows as the current list (no additions or removals)._"
                    ),
                },
            },
            {
                "type": "input",
                "block_id": "show_ids_block",
                "label": {"type": "plain_text", "text": "Shows in new order"},
                "element": {
                    "type":          "plain_text_input",
                    "action_id":     "show_ids_input",
                    "multiline":     True,
                    "initial_value": prefilled,
                    "placeholder":   {"type": "plain_text", "text": "showId1\nshowId2\nshowId3"},
                },
            },
        ],
    }

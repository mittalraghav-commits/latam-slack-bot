def build_initial_modal(private_metadata: str = "{}") -> dict:
    """Step 1 — language picker only. Module dropdown is disabled until language is chosen."""
    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type": "static_select",
                    "action_id": "language_select",
                    "placeholder": {"type": "plain_text", "text": "Select a language"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Spanish (es)"}, "value": "es"},
                        {"text": {"type": "plain_text", "text": "Portuguese (pt)"}, "value": "pt"},
                        {"text": {"type": "plain_text", "text": "German (de)"},    "value": "de"},
                        {"text": {"type": "plain_text", "text": "French (fr)"},    "value": "fr"},
                    ],
                },
            },
            {
                "type": "section",
                "block_id": "module_placeholder_block",
                "text": {
                    "type": "mrkdwn",
                    "text": "_Select a language above to load modules._",
                },
            },
        ],
    }


def build_modal_with_modules(
    modules: list[dict],
    private_metadata: str = "{}",
    selected_language: str = "",
) -> dict:
    """Step 2 — language chosen, module dropdown populated. No current shows shown yet."""
    module_options = [
        {
            "text": {"type": "plain_text", "text": m.get("name", m["module_id"])},
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
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type": "static_select",
                    "action_id": "language_select",
                    "placeholder": {"type": "plain_text", "text": "Select a language"},
                    "initial_option": _language_option(selected_language),
                    "options": [
                        {"text": {"type": "plain_text", "text": "Spanish (es)"}, "value": "es"},
                        {"text": {"type": "plain_text", "text": "Portuguese (pt)"}, "value": "pt"},
                        {"text": {"type": "plain_text", "text": "German (de)"},    "value": "de"},
                        {"text": {"type": "plain_text", "text": "French (fr)"},    "value": "fr"},
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "module_block",
                "label": {"type": "plain_text", "text": "Module"},
                "element": {
                    "type": "static_select",
                    "action_id": "module_select",
                    "placeholder": {"type": "plain_text", "text": "Select a module"},
                    "options": module_options,
                },
            },
            {
                "type": "section",
                "block_id": "current_shows_placeholder_block",
                "text": {
                    "type": "mrkdwn",
                    "text": "_Select a module above to preview its current shows._",
                },
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
) -> dict:
    """
    Step 3 — module chosen. Shows current show list and the input field.
    This is the fully populated modal ready for the user to submit.
    """
    module_options = [
        {
            "text": {"type": "plain_text", "text": m.get("name", m["module_id"])},
            "value": m["module_id"],
        }
        for m in modules
    ]

    # Build a numbered preview of current shows
    if current_show_ids:
        shows_preview = "\n".join(f"{i+1}. `{s}`" for i, s in enumerate(current_show_ids))
        # Pre-fill the input with the current list so the user can edit in-place
        prefilled_value = '[\n' + ',\n'.join(f'  "{s}"' for s in current_show_ids) + '\n]'
    else:
        shows_preview = "_No shows currently assigned._"
        prefilled_value = ""

    return {
        "type": "modal",
        "callback_id": "latam_module_update",
        "private_metadata": private_metadata,
        "title": {"type": "plain_text", "text": "Update LATAM Module"},
        "submit": {"type": "plain_text", "text": "Update"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "language_block",
                "label": {"type": "plain_text", "text": "Language"},
                "element": {
                    "type": "static_select",
                    "action_id": "language_select",
                    "initial_option": _language_option(selected_language),
                    "options": [
                        {"text": {"type": "plain_text", "text": "Spanish (es)"}, "value": "es"},
                        {"text": {"type": "plain_text", "text": "Portuguese (pt)"}, "value": "pt"},
                        {"text": {"type": "plain_text", "text": "German (de)"},    "value": "de"},
                        {"text": {"type": "plain_text", "text": "French (fr)"},    "value": "fr"},
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "module_block",
                "label": {"type": "plain_text", "text": "Module"},
                "element": {
                    "type": "static_select",
                    "action_id": "module_select",
                    "initial_option": {
                        "text": {"type": "plain_text", "text": selected_module_name},
                        "value": selected_module_id,
                    },
                    "options": module_options,
                },
            },
            # Current shows preview
            {
                "type": "section",
                "block_id": "current_shows_block",
                "text": {
                    "type": "mrkdwn",
                    "text": f":eyes: *Current shows in `{selected_module_name}` ({len(current_show_ids)} shows):*\n{shows_preview}",
                },
            },
            {"type": "divider"},
            # Format hint
            {
                "type": "section",
                "block_id": "format_hint_block",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        ":pencil2: *Provide the new ordered list of show IDs as a JSON array:*\n"
                        "```[\n"
                        '  "showId1",\n'
                        '  "showId2",\n'
                        '  "showId3"\n'
                        "]```\n"
                        "_The list replaces the module entirely — include all shows you want to keep, in order._"
                    ),
                },
            },
            # Input pre-filled with current list
            {
                "type": "input",
                "block_id": "show_ids_block",
                "label": {"type": "plain_text", "text": "New Show IDs"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "show_ids_input",
                    "multiline": True,
                    "initial_value": prefilled_value,
                    "placeholder": {
                        "type": "plain_text",
                        "text": '["showId1", "showId2", "showId3"]',
                    },
                },
            },
        ],
    }


def _language_option(language: str) -> dict:
    labels = {"es": "Spanish (es)", "pt": "Portuguese (pt)", "de": "German (de)", "fr": "French (fr)"}
    return {"text": {"type": "plain_text", "text": labels.get(language, language)}, "value": language}

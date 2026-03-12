import time
from slack_sdk import WebClient

LANGUAGE_LABELS = {
    "fr":         "French (FR)",
    "german":     "German (DE)",
    "spanish":    "Spanish (ES)",
    "portuguese": "Portuguese (BR)",
}


def post_audit_log(
    client: WebClient,
    *,
    channel: str,
    slack_user_id: str,
    slack_user_name: str,
    language: str,
    module_id: str,
    module_name: str,
    previous_show_ids: list,
    new_show_ids: list,
):
    added     = [s for s in new_show_ids if s not in previous_show_ids]
    removed   = [s for s in previous_show_ids if s not in new_show_ids]
    reordered = (
        set(new_show_ids) == set(previous_show_ids)
        and new_show_ids != previous_show_ids
    )

    change_lines = []
    if added:
        change_lines.append(
            f":heavy_plus_sign: *Added ({len(added)}):*\n"
            + "\n".join(f"  • `{s}`" for s in added)
        )
    if removed:
        change_lines.append(
            f":heavy_minus_sign: *Removed ({len(removed)}):*\n"
            + "\n".join(f"  • `{s}`" for s in removed)
        )
    if reordered:
        change_lines.append(":arrows_counterclockwise: *Order changed* (same shows, new sequence)")
    if not change_lines:
        change_lines.append(":twisted_rightwards_arrows: *No net change* (identical list resubmitted)")

    def numbered_list(shows: list) -> str:
        return "```" + "\n".join(f"{i+1:>2}. {s}" for i, s in enumerate(shows)) + "```"

    ts = int(time.time())

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "\u270f\ufe0f  LATAM Module Updated"},
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*POC / Updated by:*\n<@{slack_user_id}> (`{slack_user_name}`)",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Language:*\n{LANGUAGE_LABELS.get(language, language)}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Module:*\n{module_name}\n`{module_id}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Shows after update:*\n{len(previous_show_ids)} \u2192 {len(new_show_ids)}",
                },
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*What changed:*\n\n" + "\n\n".join(change_lines),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Previous list ({len(previous_show_ids)} shows):*\n{numbered_list(previous_show_ids)}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*New list ({len(new_show_ids)} shows):*\n{numbered_list(new_show_ids)}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<!date^{ts}^{{date_short_pretty}} at {{time}}|{ts}>",
                }
            ],
        },
    ]

    client.chat_postMessage(
        channel=channel,
        text=f"LATAM module `{module_id}` ({module_name}) updated by {slack_user_name}",
        blocks=blocks,
    )

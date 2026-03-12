import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN      = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
LATAM_API_BASE_URL   = os.environ["LATAM_API_BASE_URL"]
LATAM_API_KEY        = os.environ["LATAM_API_KEY"]

# ── Language-based role config ─────────────────────────────────────────────────
# Each env var holds the Slack usergroup ID for editors of that language.
# Members of LATAM_USERGROUP_ALL can update every language.
# Leave a var empty to disable access for that language entirely.
#
# How to find a usergroup ID:
#   Slack → People & user groups → open group → ··· → Copy link
#   The ID starts with "S" (e.g. S012AB3CD)

LATAM_USERGROUP_ALL = os.environ.get("LATAM_USERGROUP_ALL", "")
LATAM_USERGROUP_FR  = os.environ.get("LATAM_USERGROUP_FR", "")
LATAM_USERGROUP_DE  = os.environ.get("LATAM_USERGROUP_DE", "")
LATAM_USERGROUP_ES  = os.environ.get("LATAM_USERGROUP_ES", "")
LATAM_USERGROUP_PT  = os.environ.get("LATAM_USERGROUP_PT", "")

# Maps API language keys → their usergroup ID
LANGUAGE_USERGROUPS: dict[str, str] = {
    "fr":         LATAM_USERGROUP_FR,
    "german":     LATAM_USERGROUP_DE,
    "spanish":    LATAM_USERGROUP_ES,
    "portuguese": LATAM_USERGROUP_PT,
}

import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN       = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET  = os.environ["SLACK_SIGNING_SECRET"]
LATAM_API_BASE_URL    = os.environ["LATAM_API_BASE_URL"]
LATAM_API_KEY         = os.environ["LATAM_API_KEY"]

# Comma-separated Slack usergroup IDs whose members may run /update-latam-module
# e.g. "S012AB3CD,S045EF6GH"
# Find a group's ID: open the usergroup in Slack → copy link → ID is in the URL
ALLOWED_USERGROUP_IDS = [
    gid.strip()
    for gid in os.environ.get("LATAM_ALLOWED_USERGROUPS", "").split(",")
    if gid.strip()
]

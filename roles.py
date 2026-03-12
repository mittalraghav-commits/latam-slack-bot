from functools import lru_cache
from slack_sdk import WebClient
from config import LANGUAGE_USERGROUPS, LATAM_USERGROUP_ALL


class UnauthorizedError(Exception):
    pass


@lru_cache(maxsize=50)
def _get_group_members(client_token: str, group_id: str) -> frozenset:
    """
    Fetch and cache members of a single usergroup.
    Cached per (token, group_id) — call invalidate_cache() after membership changes.
    """
    client = WebClient(token=client_token)
    resp = client.usergroups_users_list(usergroup=group_id)
    return frozenset(resp["users"])


def get_allowed_languages(client: WebClient, user_id: str) -> list[str]:
    """
    Return the list of language keys the user is allowed to edit.

    Rules:
    - Member of LATAM_USERGROUP_ALL → can edit all languages
    - Member of LATAM_USERGROUP_FR  → can edit French only
    - Member of multiple per-language groups → can edit those languages
    - Member of no group → raises UnauthorizedError

    If no usergroups are configured at all (dev mode), all languages are allowed.
    """
    configured = [gid for gid in [LATAM_USERGROUP_ALL] + list(LANGUAGE_USERGROUPS.values()) if gid]

    # Dev mode — no groups configured, open access
    if not configured:
        return list(LANGUAGE_USERGROUPS.keys())

    # Check the ALL (super-admin) group first
    if LATAM_USERGROUP_ALL:
        if user_id in _get_group_members(client.token, LATAM_USERGROUP_ALL):
            return list(LANGUAGE_USERGROUPS.keys())

    # Check per-language groups
    allowed = [
        lang
        for lang, group_id in LANGUAGE_USERGROUPS.items()
        if group_id and user_id in _get_group_members(client.token, group_id)
    ]

    if not allowed:
        raise UnauthorizedError(user_id)

    return allowed


def assert_authorized_for_language(client: WebClient, user_id: str, language: str):
    """
    Raise UnauthorizedError if the user cannot edit the given language.
    Used as a defence-in-depth check on modal submit.
    """
    allowed = get_allowed_languages(client, user_id)
    if language not in allowed:
        raise UnauthorizedError(f"{user_id} not allowed for language '{language}'")


def invalidate_cache():
    """Clear cached usergroup membership. Call after membership changes."""
    _get_group_members.cache_clear()

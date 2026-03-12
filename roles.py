from functools import lru_cache
from slack_sdk import WebClient
from config import ALLOWED_USERGROUP_IDS


class UnauthorizedError(Exception):
    pass


@lru_cache(maxsize=1)
def _get_allowed_users(client_token: str) -> frozenset:
    """
    Fetch all users across all allowed usergroups and cache the result.
    The cache is keyed on the token so it survives across calls.
    Call invalidate_cache() after usergroup membership changes (or hit /admin/invalidate-role-cache).
    """
    client = WebClient(token=client_token)
    allowed = set()
    for group_id in ALLOWED_USERGROUP_IDS:
        resp = client.usergroups_users_list(usergroup=group_id)
        allowed.update(resp["users"])
    return frozenset(allowed)


def invalidate_cache():
    """Clear the cached usergroup membership. Call after membership changes."""
    _get_allowed_users.cache_clear()


def assert_authorized(client: WebClient, user_id: str):
    """
    Raise UnauthorizedError if the user is not in any allowed usergroup.
    If ALLOWED_USERGROUP_IDS is empty (not configured), all users are allowed — useful for dev.
    """
    if not ALLOWED_USERGROUP_IDS:
        return  # open access — no groups configured

    allowed_users = _get_allowed_users(client.token)
    if user_id not in allowed_users:
        raise UnauthorizedError(user_id)

from database.operations import get_allowed_users


def is_user_allowed(user_id: str) -> bool:
    return user_id in get_allowed_users()
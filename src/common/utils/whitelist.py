from src import WHITELIST


def get_whitelist() -> list[int]:
    return [
        int(user_id.strip())
        for user_id in WHITELIST.read_text('utf-8').splitlines()
        if user_id.isdigit()
    ]


def is_whitelisted(user_id: int) -> bool:
    return user_id in get_whitelist()


def add_user(user_id: int) -> None:
    users = get_whitelist()
    if user_id not in users:
        users.append(user_id)
        WHITELIST.write_text('\n'.join(map(str, users)))


def remove_user(user_id: int) -> None:
    users = get_whitelist()
    if user_id in users:
        users.remove(user_id)
        WHITELIST.write_text('\n'.join(map(str, users)))

import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote

import orjson

logger = logging.getLogger(__name__)


def validate_mini_app_init_data(init_data: str, bot_token: str) -> tuple[bool, dict]:
    """
    Validates the initData string received from a Telegram Mini App.

    Args:
        init_data: The raw initData string from `window.Telegram.WebApp.initData`.
        bot_token: Your Telegram bot's token.

    Returns:
        A tuple containing a boolean indicating if the data is valid,
        and a dictionary with the parsed user data if valid.
    """
    try:
        parsed_data = {
            key: unquote(value)
            for key, value in (item.split('=', 1) for item in init_data.split('&'))
        }
    except ValueError:
        logger.error('Error parsing initData.')
        return False, {}

    if 'hash' not in parsed_data:
        logger.error('Hash not found in initData.')
        return False, {}

    # auth_date must not be older than 1 day
    if datetime.now(tz=UTC) - datetime.fromtimestamp(
        float(parsed_data.get('auth_date', 0)), tz=UTC
    ) > timedelta(days=1):
        logger.error('Auth date is older than 1 day.')
        return False, {}

    # The hash from Telegram is the one we need to compare against.
    received_hash = parsed_data.pop('hash')

    # Per the documentation, the data-check-string is all other fields
    # sorted alphabetically, in the format key=<value> joined by '\n'.
    data_check_string = '\n'.join(f'{key}={parsed_data[key]}' for key in sorted(parsed_data.keys()))

    # The secret key is an HMAC-SHA256 signature of the bot token
    # with "WebAppData" as the key.
    secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()

    # The calculated hash is the HMAC-SHA256 signature of the data-check-string
    # using the secret key. Its hexadecimal representation is what we compare.
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # If the hashes match, the data is authentic.
    if calculated_hash == received_hash:
        user_data_str = parsed_data.get('user', '{}')
        try:
            user_data = orjson.loads(user_data_str)
            return True, user_data
        except orjson.JSONDecodeError:
            logger.error('Error decoding user JSON.')
            return False, {}

    logger.warning('Hash mismatch. Data validation failed.')
    return False, {}

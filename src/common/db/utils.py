from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from sqlalchemy.orm import Session

F = TypeVar('F', bound=Callable[..., Any])


def db_exceptions_handler(function: F) -> F:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> F:
        try:
            return cast(F, function(*args, **kwargs))
        except Exception as err:
            if isinstance(args[0], Session):
                args[0].rollback()
            else:
                from src.builder.db.session import session

                session.rollback()
            raise err

    return cast(F, wrapper)

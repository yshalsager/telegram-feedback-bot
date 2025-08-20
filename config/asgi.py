"""
ASGI config for bot project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from os import environ

from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, Scope
from django_asgi_lifespan.asgi import get_asgi_application

environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


django_application = get_asgi_application()


async def application(scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
    if scope['type'] in {'http', 'lifespan'}:
        await django_application(scope, receive, send)
    else:
        raise NotImplementedError(f'Unknown scope type {scope["type"]}')

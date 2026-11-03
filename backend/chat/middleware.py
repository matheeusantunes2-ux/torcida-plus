from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import close_old_connections


@sync_to_async
def consumir_ticket(ticket):
    close_old_connections()
    key = f"chat:ws-ticket:{ticket}"
    user_id = cache.get(key)
    if user_id is None:
        return None
    cache.delete(key)
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return None


class TicketAuthMiddleware:
    """Autentica WebSockets com ticket opaco de uso único e validade curta."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        values = query.get("ticket", [])
        user = await consumir_ticket(values[0]) if len(values) == 1 else None
        if user is None:
            await send({"type": "websocket.close", "code": 4401})
            return
        scope = dict(scope)
        scope["user"] = user
        return await self.app(scope, receive, send)

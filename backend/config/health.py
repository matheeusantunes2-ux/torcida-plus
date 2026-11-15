import os
import uuid

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Diagnóstico mínimo de dependências, sem revelar credenciais."""
    redis_ok = False
    probe_key = f"health:probe:{uuid.uuid4().hex}"
    try:
        cache.set(probe_key, "ok", timeout=10)
        redis_ok = cache.get(probe_key) == "ok"
    except Exception:
        redis_ok = False
    finally:
        try:
            cache.delete(probe_key)
        except Exception:
            pass

    livekit_ok = all(os.getenv(key) for key in (
        "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"
    ))
    cloudinary_ok = bool(os.getenv("CLOUDINARY_URL") or (
        os.getenv("CLOUDINARY_CLOUD_NAME")
        and os.getenv("CLOUDINARY_API_KEY")
        and os.getenv("CLOUDINARY_API_SECRET")
    ))

    payload = {
        "status": "ok" if redis_ok else "degraded",
        "dependencies": {
            "redis": "ok" if redis_ok else "unavailable",
            "livekit_configured": livekit_ok,
            "cloudinary_configured": cloudinary_ok,
        },
    }
    return JsonResponse(payload, status=200 if redis_ok else 503)

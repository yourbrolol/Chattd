"""
ASGI config for messenger project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import json
import time
import logging
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.settings')

# region agent log
def _agent_log(hypothesisId: str, location: str, message: str, data: dict):
    try:
        with open(r"c:\Users\andri\OneDrive\Документи\Projects\Misc\messenger\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": hypothesisId,
                        "location": location,
                        "message": message,
                        "data": data,
                        "timestamp": int(time.time() * 1000),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass


def _logger_snapshot(name: str):
    lg = logging.getLogger(name)
    out = []
    for h in getattr(lg, "handlers", []) or []:
        fmt = getattr(getattr(h, "formatter", None), "_fmt", None)
        out.append(
            {
                "handler": type(h).__name__,
                "level": getattr(h, "level", None),
                "formatter": type(getattr(h, "formatter", None)).__name__ if getattr(h, "formatter", None) else None,
                "fmt": fmt,
            }
        )
    return {"level": getattr(lg, "level", None), "propagate": getattr(lg, "propagate", None), "handlers": out}


_agent_log(
    "H1",
    "messenger/asgi.py",
    "startup logging snapshot",
    {
        "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE"),
        "root": _logger_snapshot(""),
        "daphne": _logger_snapshot("daphne"),
        "daphne_server": _logger_snapshot("daphne.server"),
        "twisted": _logger_snapshot("twisted"),
        "django_server": _logger_snapshot("django.server"),
    },
)
# endregion agent log

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    )
})
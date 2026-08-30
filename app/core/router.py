from typing import Any, Callable

from fastapi import APIRouter as FastAPIRouter
from fastapi.types import DecoratedCallable
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["20/second"])


class APIRouter(FastAPIRouter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("dependencies", [])
        super().__init__(*args, **kwargs)

    def api_route(
        self,
        path: str,
        *,
        include_in_schema: bool = True,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        alternate_path = path + "/" if path != "/" else path

        original = super().api_route(
            path,
            include_in_schema=include_in_schema,
            **kwargs,
        )

        alternate = super().api_route(
            alternate_path,
            include_in_schema=False,
            **kwargs,
        )

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            alternate(func)
            return original(func)

        return decorator
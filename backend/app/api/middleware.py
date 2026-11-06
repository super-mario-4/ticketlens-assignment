from starlette.exceptions import HTTPException
from starlette.status import HTTP_413_CONTENT_TOO_LARGE
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class UploadSizeLimitMiddleware:
    """Stops an oversized upload while it arrives. The form is parsed before any dependency
    runs, so a later check would come after the file had already been spooled to disk."""

    def __init__(self, app: ASGIApp, path: str, max_bytes: int, detail: dict[str, object]) -> None:
        self._app = app
        self._path = path
        self._max_bytes = max_bytes
        self._detail = detail

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != self._path or scope["method"] != "POST":
            await self._app(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self._max_bytes:
                raise HTTPException(HTTP_413_CONTENT_TOO_LARGE, self._detail)
            return message

        await self._app(scope, limited_receive, send)

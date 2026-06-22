from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value
    return response

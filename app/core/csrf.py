import functools
import http.cookies
from typing import Optional

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette_csrf import CSRFMiddleware as BaseCSRFMiddleware
from starlette.types import Message, Receive, Scope, Send


class CSRFMiddleware(BaseCSRFMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        csrf_cookie = request.cookies.get(self.cookie_name)
        scope["csrf_token"] = csrf_cookie or self._generate_csrf_token()

        if self._url_is_required(request.url) or (
            request.method not in self.safe_methods
            and not self._url_is_exempt(request.url)
            and self._has_sensitive_cookies(request.cookies)
        ):
            submitted_csrf_token = await self._get_submitted_csrf_token(request)
            if (
                not csrf_cookie
                or not submitted_csrf_token
                or not self._csrf_tokens_match(csrf_cookie, submitted_csrf_token)
            ):
                response = self._get_error_response(request)
                await response(scope, receive, send)
                return

        send = functools.partial(self.send, send=send, scope=scope)
        await self.app(scope, receive, send)

    async def send(self, message: Message, send: Send, scope: Scope) -> None:
        request = Request(scope)
        csrf_cookie = request.cookies.get(self.cookie_name)

        if csrf_cookie is None:
            message.setdefault("headers", [])
            headers = MutableHeaders(scope=message)

            cookie: http.cookies.BaseCookie = http.cookies.SimpleCookie()
            cookie[self.cookie_name] = scope.get("csrf_token") or self._generate_csrf_token()
            cookie[self.cookie_name]["path"] = self.cookie_path
            cookie[self.cookie_name]["secure"] = self.cookie_secure
            cookie[self.cookie_name]["httponly"] = self.cookie_httponly
            cookie[self.cookie_name]["samesite"] = self.cookie_samesite
            if self.cookie_domain is not None:
                cookie[self.cookie_name]["domain"] = self.cookie_domain
            headers.append("set-cookie", cookie.output(header="").strip())

        await send(message)

    async def _get_submitted_csrf_token(self, request: Request) -> Optional[str]:
        token = request.headers.get(self.header_name)
        if token:
            return token
        try:
            form = await request.form()
        except Exception:
            return None
        value = form.get("csrftoken")
        if value is None:
            return None
        return str(value)

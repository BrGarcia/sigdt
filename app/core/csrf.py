from typing import Optional

from starlette.requests import Request
from starlette_csrf import CSRFMiddleware as BaseCSRFMiddleware


class CSRFMiddleware(BaseCSRFMiddleware):
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

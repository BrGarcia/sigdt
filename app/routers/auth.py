from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import hmac
import time
from jose import jwt
from app.core.config import GATEKEEPER_PASSWORD, SECRET_KEY, ENVIRONMENT, is_rate_limited
from app.core.templates import templates

router = APIRouter(tags=["auth"])

@router.get("/gatekeeper", response_class=HTMLResponse)
async def gatekeeper_page(request: Request):
    return templates.TemplateResponse(request=request, name="gatekeeper.html", context={})

@router.post("/gatekeeper")
async def gatekeeper_verify(request: Request, password: str = Form(...)):
    client_ip = request.client.host
    if is_rate_limited(f"gatekeeper_{client_ip}"):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em 1 minuto.")

    if hmac.compare_digest(password, GATEKEEPER_PASSWORD):
        response = RedirectResponse(url="/", status_code=303)
        token = jwt.encode({"access": "granted", "exp": time.time() + 86400 * 7}, SECRET_KEY, algorithm="HS256")
        response.set_cookie(
            key="gatekeeper_access", 
            value=token, 
            max_age=86400 * 7,
            httponly=True,
            samesite="lax",
            secure=ENVIRONMENT == "production"
        )
        return response
    return RedirectResponse(url="/gatekeeper?error=1", status_code=303)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    from app.core.config import check_gatekeeper
    if not check_gatekeeper(request):
        return RedirectResponse(url="/gatekeeper")
    return templates.TemplateResponse(request=request, name="login.html", context={})

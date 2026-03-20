from fastapi import APIRouter, Depends, HTTPException, status, Form, Cookie, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.database import get_session
from . import actions, schemas, security, models
from typing import Optional, List
from datetime import timedelta

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_session)
):
    actual_token = token or access_token
    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = security.decode_token(actual_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = actions.get_user(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_session)
):
    actual_token = token or access_token
    if not actual_token:
        return None
    username = security.decode_token(actual_token)
    if not username:
        return None
    user = actions.get_user(db, username=username)
    return user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_inspector_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["inspector", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.post("/token")
async def login_for_access_token(request: Request, response: Response, db: Session = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()):
    from app.main import is_rate_limited
    client_ip = request.client.host
    if is_rate_limited(f"login_{client_ip}"):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Muitas tentativas de login. Tente novamente em 1 minuto.")

    user = actions.get_user(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 
        samesite="lax",
        secure=False # True in production
    )
    return {"status": "success"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}

@router.post("/", response_model=models.User, dependencies=[Depends(get_current_admin_user)])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_session)):
    db_user = actions.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return actions.create_user(db=db, user=user, role="inspector")

@router.get("/me", response_model=models.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/all", response_model=List[models.User], dependencies=[Depends(get_current_admin_user)])
def read_users(db: Session = Depends(get_session)):
    return db.exec(select(models.User)).all()

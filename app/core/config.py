import os
import time
import hmac
from collections import defaultdict
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

# Env Variables
GATEKEEPER_PASSWORD = os.getenv("GATEKEEPER_PASSWORD")
if not GATEKEEPER_PASSWORD:
    raise ValueError("Variável de ambiente GATEKEEPER_PASSWORD é obrigatória.")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Variável de ambiente SECRET_KEY é obrigatória para segurança.")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("Variável de ambiente ADMIN_PASSWORD é obrigatória no startup.")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# In-Memory Rate Limiter
login_attempts = defaultdict(list)

def is_rate_limited(key: str, max_attempts: int = 5, window: int = 60):
    now = time.time()
    # Clean old attempts
    login_attempts[key] = [t for t in login_attempts[key] if now - t < window]
    if len(login_attempts[key]) >= max_attempts:
        return True
    login_attempts[key].append(now)
    return False

def check_gatekeeper(request):
    token = request.cookies.get("gatekeeper_access")
    if not token:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("access") == "granted"
    except Exception:
        return False

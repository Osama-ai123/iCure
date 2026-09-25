import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in the environment")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 7
MAX_PASSWORD_BYTES = 72


# ----------  passwords  ----------

def hash_password(password):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def check_password(password, pass_hash):
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, pass_hash.encode("utf-8"))


# ---------- Access token (JWT) ----------

def create_access_token(user_id):
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token):
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])


# ---------- Refresh token ----------

def hash_refresh_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_refresh_token():
    token = secrets.token_urlsafe(32)
    return token, hash_refresh_token(token)


def refresh_token_expiry():
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
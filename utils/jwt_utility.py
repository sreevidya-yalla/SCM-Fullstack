from datetime import datetime, timedelta
from jose import jwt, JWTError

ACCESS_SECRET = "change_access_secret"
REFRESH_SECRET = "change_refresh_secret"
ALGORITHM = "HS256"

ACCESS_EXPIRE_MIN = 10      # short-lived
REFRESH_EXPIRE_DAYS = 3     # long-lived

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MIN)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, ACCESS_SECRET, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, REFRESH_SECRET, algorithm=ALGORITHM)

def verify_access_token(token: str):
    try:
        return jwt.decode(token, ACCESS_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None

def verify_refresh_token(token: str):
    try:
        return jwt.decode(token, REFRESH_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None

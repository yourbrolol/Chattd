from decouple import config

# Security
SECRET_KEY = config("SECRET_KEY", default="hyper_secret_key", cast=str)
SECURE = config("SECURE", default=False, cast=bool)
CSRF_MAX_AGE = config("CSRF_MAX_AGE", default=60*60*24*30, cast=int)
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440, cast=int)

# Database
DATABASE_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///./app/db.sqlite3", cast=str)

# WebSocket rate limiting
WS_CONNECT_MAX_EVENTS = config("WS_CONNECT_MAX_EVENTS", default=3, cast=int)
WS_CONNECT_PER_SECONDS = config("WS_CONNECT_PER_SECONDS", default=3, cast=int)
WS_MESSAGE_MAX_EVENTS = config("WS_MESSAGE_MAX_EVENTS", default=1, cast=int)
WS_MESSAGE_PER_SECONDS = config("WS_MESSAGE_PER_SECONDS", default=1, cast=int)

# Logging
LOG_LEVEL_MAIN = config("LOG_LEVEL_MAIN", default="INFO", cast=str)
LOG_LEVEL_SEC = config("LOG_LEVEL_SEC", default="WARNING", cast=str)

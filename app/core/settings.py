from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Input-validation limits shared by Pydantic schemas and WTForms.

    Deliberately contains NO secrets or infrastructure config (those live in
    app.core.config). These values are env-overridable and subclassable so a
    deploy can tune behavior (e.g. a stricter "profile") without forking.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Username
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 20

    # Password (schema previously allowed min_length=1 - this is the corrected floor)
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 72

    # Room name (create + edit share one limit; the old edit limit of 50 was a bug)
    ROOM_NAME_MIN_LENGTH: int = 1
    ROOM_NAME_MAX_LENGTH: int = 20
    ROOM_NAME_PATTERN: str = r"^[a-zA-Z0-9._-]+$"

    # Chat message content (service enforces this; model column is wider)
    MESSAGE_MAX_LENGTH: int = 200


settings = Settings()

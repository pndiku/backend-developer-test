from typing import Any, Dict, Optional

from pydantic import BaseSettings, RedisDsn, validator


class Settings(BaseSettings):
    APPLICATION_NAME: str = "backend-developer-test"
    APPLICATION_VERSION: str = "1.0"

    API_V1_STR: str = "/v1"
    SECRET_KEY: str = "ife1f905fbf223243cc7d2ec2a3d4a6dd4889d2c5dce51fb9219e9659bbe1becd"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_TYPE: str = "redis"
    REDIS_URL: Optional[RedisDsn] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme=values.get("REDIS_TYPE"),
            port=str(values.get("REDIS_PORT")),
            host=values.get("REDIS_HOST"),
        )

    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://backend:backend@127.0.0.1/backend_db"

    # fastapi-jwt-auth settings
    authjwt_secret_key: str = "625671078792f8404a812fb389b7fd3da008eaabc1f6a66c257de2c2acbc39efcc319be212e6ba5d42c1428c20322e3847b12f722bfe856a6bb5f992f45afd7a"
    authjwt_token_location: set = {"headers"}

    class Config:
        case_sensitive = True


settings = Settings()

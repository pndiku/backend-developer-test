from typing import Union

import fastapi_plugins
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.api.v1.api import api_router
from app.core.config import Settings, settings
from app.core.logger import log  # noqa


class AppSettings(
    fastapi_plugins.RedisSettings,
):
    api_name: str = str(__name__)
    redis_url: str = settings.REDIS_URL


app = FastAPI(title="Backend Developer DB")
config = AppSettings()


@app.exception_handler(RequestValidationError)
async def http422_error_handler(
    _: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    r = JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]),
        },
    )
    try:
        log.debug(f"ERROR: 422, {r.body.decode()}")
    except Exception:
        pass

    return r


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    message = "Authorization Header Error: Invalid/Missing Bearer Token"
    try:
        message = f"Authorization Header Error: {message}"
    except Exception:
        pass

    return JSONResponse(
        status_code=exc.status_code,
        content={"msg": message},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc) -> JSONResponse:
    log.error(exc, exc_info=True)
    r = JSONResponse(status_code=500, content={"success": False, "message": "System Error"})

    return r


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc) -> JSONResponse:
    r = JSONResponse(status_code=exc.status_code, content={"success": False, "message": exc.detail})
    try:
        log.debug(f"ERROR: {exc.status_code}, {r.body.decode()}")
    except Exception:
        pass

    return r


@app.on_event("startup")
async def on_startup() -> None:
    await fastapi_plugins.redis_plugin.init_app(app, config=config)
    await fastapi_plugins.redis_plugin.init()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await fastapi_plugins.redis_plugin.terminate()


@AuthJWT.load_config
def get_config():
    return Settings()


app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
    responses={422: {"description": "Validation Error"}},
)

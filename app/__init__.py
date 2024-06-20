import inspect
import re
from typing import Union

import fastapi_plugins
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
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


# The function below allows fastapi-jwt-auth to show lock icons for restricted endpoints
# See https://github.com/IndominusByte/fastapi-jwt-auth/issues/34#issuecomment-769234395
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APPLICATION_NAME,
        version=settings.APPLICATION_VERSION,
        routes=app.routes,
        servers=app.servers,
        description="""Backend Development Server
## Authentication

This API uses token authentication (Bearer in HTTP Header). First you retrieve a new Bearer token using login/password authentication. After that you can use it to access other resources.

**Bearer token example**

`eYFuat5lz1y5v0LrCt7LfqJpo1AkdLgm7LbY6eRibN4NYw9Srf6aMIRJM8KbTwM6`
    )""",
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": (
                "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the access token"
            ),
        }
    }

    api_routes = [route for route in app.routes if isinstance(route, APIRoute)]

    for route in api_routes:
        path = getattr(route, "path")
        endpoint = getattr(route, "endpoint")
        methods = [method.lower() for method in getattr(route, "methods")]

        for method in methods:
            # access_token
            if (
                re.search("jwt_required", inspect.getsource(endpoint))
                or re.search("fresh_jwt_required", inspect.getsource(endpoint))
                or re.search("jwt_optional", inspect.getsource(endpoint))
            ):
                try:
                    openapi_schema["paths"][path][method]["security"] = [{"Bearer Auth": []}]
                except Exception:
                    pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
    responses={422: {"description": "Validation Error"}},
)

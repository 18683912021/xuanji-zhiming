import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, TimeoutError

logger = logging.getLogger(__name__)
SAFE_INPUT_MESSAGES = {
    "invalid_lunar_birth": "所选农历日期或闰月无效。",
    "skipped_birth_time": "所选出生时间落在夏令时跳过的区间。",
    "repeated_birth_time": "所选出生时间出现两次，请选择第一次或第二次。",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


def error_response(request: Request, status: int, code: str, message: str, **fields):
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
                **fields,
            }
        },
    )


def install_error_handling(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ApiError)
    async def handle_error(request: Request, error: ApiError):
        return error_response(request, error.status, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        # Validation input can contain credentials, birth data or private messages.
        issues = [{"field": issue["loc"], "type": issue["type"]} for issue in error.errors()]
        for issue in issues:
            if (message := SAFE_INPUT_MESSAGES.get(issue["type"])) is not None:
                return error_response(request, 422, issue["type"], message, issues=issues)
        return error_response(request, 422, "invalid_input", "请检查输入参数。", issues=issues)

    async def database_unavailable(request: Request, error: Exception):
        logger.warning("Database unavailable, request=%s", request.state.request_id)
        return error_response(request, 503, "database_unavailable", "数据库暂时不可用。")

    app.add_exception_handler(OperationalError, database_unavailable)
    app.add_exception_handler(TimeoutError, database_unavailable)

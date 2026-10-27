from typing import TYPE_CHECKING, ClassVar, cast

from starlette import status
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from starlette.requests import Request


class AppError(Exception):
    """Base class. `detail` is what the client sees; `status_code` is per subclass."""

    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str, *, headers: dict[str, str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.headers = headers


class NotFoundError(AppError):
    """No such row."""

    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT


async def handle_app_error(_request: Request, exc: Exception) -> JSONResponse:
    """Registered for `AppError`, so that is what arrives; typed as Starlette asks."""
    error = cast("AppError", exc)
    return JSONResponse(
        {"detail": error.detail}, status_code=error.status_code, headers=error.headers
    )

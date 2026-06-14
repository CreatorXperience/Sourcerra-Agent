from datetime import datetime

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IDMixin(BaseModel):
    id: int


class TimestampSchema(BaseSchema):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

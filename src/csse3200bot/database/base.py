"""Base DB Model."""

from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
)
from sqlalchemy.orm import DeclarativeBase


# Base database model/table
class BaseDBModel(DeclarativeBase, AsyncAttrs):
    """Base model for db tables."""

    def to_dict(self) -> dict[Any, Any]:
        """Return dict representation of a model."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

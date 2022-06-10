"""Pydantic model definitions."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Generator

from pydantic import BaseModel, validator

validation_context: ContextVar[Path] = ContextVar("validation_context")


@contextmanager
def set_context(comic_path: Path) -> Generator[None, None, None]:
    """Sets up a validation context with the given comic path."""
    token = validation_context.set(comic_path)
    yield
    validation_context.reset(token)


def validate_path_exists(path: Path) -> None:
    """Raises a ValueError if the given path does not exist."""
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")


def validate_path_is_file(path: Path) -> None:
    """Raises a ValueError if the given path is not a file."""
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")


def validate_asset_exists(path: Path) -> None:
    """Raises a ValueError if the given path does not exist in the assets."""
    relative_path = str(path).strip("/")
    path = validation_context.get() / "assets" / relative_path
    validate_path_exists(path)
    validate_path_is_file(path)


class Comic(BaseModel):
    """Schema for a comic."""

    name: str
    placeholder: Path
    volumes: list[str]

    @validator("placeholder")
    @classmethod
    def validate_placeholder(cls, v: Path) -> Path:
        """Ensure the placeholder path exists."""
        validate_asset_exists(v)
        return v


class Volume(BaseModel):
    """Schema for a volume."""

    title: str
    image: Path
    pages: list[str]

    @validator("image")
    @classmethod
    def validate_image(cls, v: Path) -> Path:
        """Ensure the image path exists."""
        validate_asset_exists(v)
        return v


class Page(BaseModel):
    """Schema for a page."""

    title: str
    image: Path

    @validator("image")
    @classmethod
    def validate_image(cls, v: Path) -> Path:
        """Ensure the image path exists."""
        validate_asset_exists(v)
        return v

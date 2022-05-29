# pylint: disable=no-self-use
"""Marshmallow schema definitions."""
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from marshmallow import Schema, ValidationError, post_load, validates_schema
from marshmallow.fields import Field, List, String

from scuzzie import resources


class PathField(Field):
    """Custom field type for marshmallow to handle Path objects."""

    def _serialize(
        self, value: Optional[Path], attr: str, obj: Any, **kwargs: Any
    ) -> str | None:
        if value is None:
            return None

        return str(value)

    def _deserialize(
        self,
        value: Union[Path, str],
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs: Any,
    ) -> Path:
        return Path(value)


def validate_path_exists(path: Path) -> None:
    """Raises a ValidationError if the given path does not exist."""
    if not path.exists():
        raise ValidationError(f"Path does not exist: {path}")


def validate_path_is_file(path: Path) -> None:
    """Raises a ValidationError if the given path is not a file."""
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")


class Comic(Schema):
    """Schema for a comic."""

    path = PathField(required=True, load_only=True)
    name = String(required=True)
    placeholder = PathField(required=True)
    volume_slugs = List(String, required=True, data_key="volumes")

    @validates_schema
    def validate_placeholder(self, data: Mapping[str, Any], **_kwargs: Any) -> None:
        """Ensure the placeholder path exists if it is provided."""
        if data["placeholder"] is None:
            return

        placeholder_path = str(data["placeholder"]).strip("/")
        path = self.context["comic_path"] / "assets" / placeholder_path
        validate_path_exists(path)
        validate_path_is_file(path)

    @post_load
    def make_comic(self, fields: dict, **_kwargs: Any) -> resources.Comic:
        """Turns the loaded fields into a Comic object."""
        return resources.Comic(**fields)


class Volume(Schema):
    """Schema for a volume."""

    path = PathField(required=True, load_only=True)
    title = String(required=True)
    page_slugs = List(String, required=True, data_key="pages")

    @post_load
    def make_volume(self, fields: dict, **_kwargs: Any) -> resources.Volume:
        """Turns the loaded fields into a Volume object."""
        return resources.Volume(**fields)


class Page(Schema):
    """Schema for a page."""

    path = PathField(required=True, load_only=True)
    title = String(required=True)
    image = PathField(required=True)

    @validates_schema
    def validate_image(self, data: Mapping[str, Any], **_kwargs: Any) -> None:
        """Ensure the image path exists if it is provided."""
        if data["image"] is None:
            return

        image_path = str(data["image"]).strip("/")
        path = self.context["comic_path"] / "assets" / image_path
        validate_path_exists(path)
        validate_path_is_file(path)

    @post_load
    def make_page(self, fields: dict, **_kwargs: Any) -> resources.Page:
        """Turns the loaded fields into a Page object."""
        return resources.Page(**fields)

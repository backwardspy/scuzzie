from typing import Any, Optional, Union, Mapping
from pathlib import Path

from marshmallow import (
    Schema,
    fields,
    ValidationError,
    post_load,
    validates_schema,
)

from scuzzie import resources


class PathField(fields.Field):
    def _serialize(self, value: Optional[Path], attr: str, obj: Any, **kwargs):
        if value is None:
            return None
        return str(value)

    def _deserialize(
        self,
        value: Union[Path, str],
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs,
    ):
        return Path(value)


def validate_path_exists(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"Path does not exist: {path}")


def validate_path_is_file(path: Path) -> None:
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")


class Comic(Schema):
    path = PathField(required=True, load_only=True)
    name = fields.String(required=True)
    placeholder = PathField(required=True)
    volume_slugs = fields.List(fields.String, required=True, data_key="volumes")

    @validates_schema
    def validate_placeholder(self, data: Mapping[str, Any], **kwargs) -> None:
        if data["placeholder"] is None:
            return
        placeholder_path = str(data["placeholder"]).strip("/")
        path = self.context["comic_path"] / "assets" / placeholder_path
        validate_path_exists(path)
        validate_path_is_file(path)

    @post_load
    def make_comic(self, fields: dict, **kwargs) -> resources.Comic:
        return resources.Comic(**fields)


class Volume(Schema):
    path = PathField(required=True, load_only=True)
    title = fields.String(required=True)
    page_slugs = fields.List(fields.String, required=True, data_key="pages")

    @post_load
    def make_volume(self, fields: dict, **kwargs) -> resources.Volume:
        return resources.Volume(**fields)


class Page(Schema):
    path = PathField(required=True, load_only=True)
    title = fields.String(required=True)
    image = PathField(required=True)

    @validates_schema
    def validate_image(self, data: Mapping[str, Any], **kwargs) -> None:
        if data["image"] is None:
            return
        image_path = str(data["image"]).strip("/")
        path = self.context["comic_path"] / "assets" / image_path
        validate_path_exists(path)
        validate_path_is_file(path)

    @post_load
    def make_page(self, fields: dict, **kwargs) -> resources.Page:
        return resources.Page(**fields)

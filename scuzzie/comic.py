"""Defines comic resource serializers & deserializers."""
from pathlib import Path
from typing import Optional, Type

import toml

from . import schemas
from .exc import (
    ScuzzieComicConfigError,
    ScuzzieConfigError,
    ScuzzieError,
    ScuzziePageConfigError,
    ScuzzieVolumeConfigError,
)
from .resources import Comic, Page, Volume


def _ensure_path(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _try_read_toml(path: Path, error_type: Type[ScuzzieConfigError]) -> dict:
    try:
        data = toml.load(path)
    except FileNotFoundError as ex:
        raise error_type(
            reason=f"Failed to load file from {path}; it may not exist."
        ) from ex
    return dict(data)


def _try_write_toml(path: Path, data: dict) -> None:
    _ensure_path(path.parent)
    with path.open("w") as file:
        toml.dump(data, file)


def read_comic(path: Path) -> Comic:
    """Deserializes a set of resource configuration files into a Comic object."""
    config = _read_comic_config(path)
    comic = _comic_from_config(config, path=path)
    if not comic.path:
        raise ScuzzieError("Attempted to read virtual comic.")

    _read_volumes(into=comic, comic_path=comic.path)
    return comic


def _read_volumes(*, into: Comic, comic_path: Path) -> None:
    if into.path is None:
        raise ScuzzieError(
            "Attempted to read volumes into a virtual comic. "
            "This should never happen."
        )

    volumes_path = _ensure_path(into.path / "volumes")
    for volume_path in volumes_path.iterdir():
        config = _read_volume_config(volume_path)
        volume = _volume_from_config(config, path=volume_path, comic_path=comic_path)
        _read_pages(into=volume, comic_path=comic_path)
        into.add_volume(volume)


def _read_pages(*, into: Volume, comic_path: Path) -> None:
    if into.path is None:
        raise ScuzzieError(
            "Attempted to read pages into a virtual volume. "
            "This should never happen."
        )

    pages_path = _ensure_path(into.path / "pages")
    for page_path in pages_path.iterdir():
        config = _read_page_config(page_path)
        page = _page_from_config(config, path=page_path, comic_path=comic_path)
        into.add_page(page)

    missing_pages = [slug for slug in into.page_slugs if slug not in into.pages]
    if missing_pages:
        raise ScuzzieVolumeConfigError(
            f'Volume "{into.title}" lists the following pages '
            "that don't seem to exist: "
            f"{', '.join(missing_pages)}"
        )


def _read_comic_config(path: Path) -> dict:
    config_path = path / "comic.toml"
    return _try_read_toml(config_path, ScuzzieComicConfigError)


def _read_volume_config(path: Path) -> dict:
    config_path = path / "volume.toml"
    return _try_read_toml(config_path, ScuzzieVolumeConfigError)


def _read_page_config(path: Path) -> dict:
    config_path = path / "page.toml"
    return _try_read_toml(config_path, ScuzziePageConfigError)


def _comic_from_config(config: dict, *, path: Path) -> Comic:
    schema = schemas.Comic()
    schema.context["comic_path"] = path
    try:
        return schema.load({"path": path, **config})
    except schemas.ValidationError as ex:
        raise ScuzzieComicConfigError(str(ex)) from ex


def _volume_from_config(config: dict, *, path: Path, comic_path: Path) -> Volume:
    schema = schemas.Volume()
    schema.context["comic_path"] = comic_path
    try:
        return schema.load({"path": path, **config})
    except schemas.ValidationError as ex:
        raise ScuzzieVolumeConfigError(str(ex)) from ex


def _page_from_config(config: dict, *, path: Path, comic_path: Path) -> Page:
    schema = schemas.Page()
    schema.context["comic_path"] = comic_path
    try:
        return schema.load({"path": path, **config})
    except schemas.ValidationError as ex:
        raise ScuzzieVolumeConfigError(str(ex)) from ex


def _ensure_comic_has_path(comic: Comic, path: Optional[Path] = None) -> Path:
    if comic.path and not path:
        return comic.path

    if path and not comic.path:
        comic.path = path
        return path

    raise ScuzzieError(
        "One (and only one) of `comic.path` and `path` must contain a value."
    )


def write_comic(comic: Comic, *, path: Path | None = None) -> None:
    """Turns the Comic object into a set of resource configuration files."""
    path = _ensure_comic_has_path(comic, path)
    _write_comic_config(comic, path=path)
    _write_volumes(comic=comic, path=path)


def _write_comic_config(comic: Comic, *, path: Path) -> None:
    config_path = path / "comic.toml"
    schema = schemas.Comic()
    schema.context["comic_path"] = comic.path
    config = schema.dump(comic)
    _try_write_toml(config_path, config)


def _write_volumes(*, comic: Comic, path: Path) -> None:
    for volume in comic.each_volume():
        _write_volume(volume, comic=comic, path=path)


def _write_volume(volume: Volume, *, comic: Comic, path: Path) -> None:
    _write_volume_config(volume, comic=comic, path=path)
    for page in volume.each_page():
        _write_page(page, comic=comic)


def _write_volume_config(volume: Volume, *, comic: Comic, path: Path) -> None:
    path = path / "volumes" / volume.slug / "volume.toml"
    schema = schemas.Volume()
    schema.context["comic_path"] = comic.path
    config = schema.dump(volume)
    _try_write_toml(path, config)


def _write_page(page: Page, *, comic: Comic) -> None:
    _write_page_config(page, comic=comic)


def _write_page_config(page: Page, *, comic: Comic) -> None:
    if page.volume and page.volume.path:
        path = page.volume.path / "pages" / page.slug / "page.toml"
        schema = schemas.Page()
        schema.context["comic_path"] = comic.path
        config = schema.dump(page)
        _try_write_toml(path, config)
    else:
        raise ScuzzieVolumeConfigError(
            "Tried to save page into null volume or volume with a null path."
        )

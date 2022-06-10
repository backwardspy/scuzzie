"""Defines comic resource serializers & deserializers."""
from pathlib import Path
from typing import Any, Mapping, Optional, Type

import tomli
import tomli_w

from . import models
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
        with path.open("rb") as file:
            return tomli.load(file)
    except FileNotFoundError as ex:
        raise error_type(
            reason=f"Failed to load file from {path}; it may not exist."
        ) from ex


def _try_write_toml(path: Path, data: Mapping[str, Any]) -> None:
    _ensure_path(path.parent)

    data = {**data}
    for key, value in data.items():
        if isinstance(value, Path):
            data[key] = str(value)

    toml = tomli_w.dumps(data)
    with path.open("w") as file:
        print(toml, file=file)


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
    try:
        with models.set_context(path):
            data = models.Comic(**config)
    except ValueError as ex:
        raise ScuzzieComicConfigError(str(ex)) from ex

    return Comic(
        path=path,
        name=data.name,
        placeholder=data.placeholder,
        volume_slugs=data.volumes,
    )


def _volume_from_config(config: dict, *, path: Path, comic_path: Path) -> Volume:
    try:
        with models.set_context(comic_path):
            data = models.Volume(**config)
    except ValueError as ex:
        raise ScuzzieVolumeConfigError(str(ex)) from ex

    return Volume(path=path, title=data.title, image=data.image, page_slugs=data.pages)


def _page_from_config(config: dict, *, path: Path, comic_path: Path) -> Page:
    try:
        with models.set_context(comic_path):
            data = models.Page(**config)
    except ValueError as ex:
        raise ScuzzieVolumeConfigError(str(ex)) from ex

    return Page(path=path, title=data.title, image=data.image)


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

    if not comic.path:
        raise ScuzzieError(
            "Attempted to write virtual comic. This should never happen."
        )

    with models.set_context(comic.path):
        config = models.Comic(
            path=comic.path,
            name=comic.name,
            placeholder=comic.placeholder,
            volumes=comic.volume_slugs,
        )

    _try_write_toml(config_path, config.dict())


def _write_volumes(*, comic: Comic, path: Path) -> None:
    for volume in comic.each_volume():
        _write_volume(volume, comic=comic, path=path)


def _write_volume(volume: Volume, *, comic: Comic, path: Path) -> None:
    _write_volume_config(volume, comic=comic, path=path)
    for page in volume.each_page():
        _write_page(page, comic=comic)


def _write_volume_config(volume: Volume, *, comic: Comic, path: Path) -> None:
    if not comic.path:
        raise ScuzzieError(
            "Attempted to write volume with a virtual comic. This should never happen."
        )

    with models.set_context(comic.path):
        config = models.Volume(
            title=volume.title,
            image=volume.image,
            pages=volume.page_slugs,
        )
    path = path / "volumes" / volume.slug / "volume.toml"
    _try_write_toml(path, config.dict())


def _write_page(page: Page, *, comic: Comic) -> None:
    if not comic.path:
        raise ScuzzieError(
            "Attempted to write page with a virtual comic. This should never happen."
        )

    if page.volume and page.volume.path:
        with models.set_context(comic.path):
            config = models.Page(
                title=page.title,
                image=page.image,
            )

        path = page.volume.path / "pages" / page.slug / "page.toml"
        _try_write_toml(path, config.dict())
    else:
        raise ScuzzieVolumeConfigError(
            "Tried to save page into null volume or volume with a null path."
        )

from typing import Optional, Type
from pathlib import Path

import toml

from . import schemas
from .resources import Comic, Volume, Page
from .exc import (
    ScuzzieError,
    ScuzzieConfigError,
    ScuzzieComicConfigError,
    ScuzzieVolumeConfigError,
    ScuzziePageConfigError,
)


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
    with path.open("w") as f:
        toml.dump(data, f)


class ComicDeserializer:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.comic: Optional[Comic] = None

    def read_comic(self) -> Comic:
        config = self._read_comic_config()
        self.comic = self._comic_from_config(config, path=self.path)
        self._read_volumes(into=self.comic)
        return self.comic

    def _read_volumes(self, *, into: Comic) -> None:
        if into.path is None:
            raise ScuzzieError(
                "Attempted to read volumes into a virtual comic. "
                "This should never happen."
            )

        volumes_path = _ensure_path(into.path / "volumes")
        for volume_path in volumes_path.iterdir():
            config = self._read_volume_config(volume_path)
            volume = self._volume_from_config(config, path=volume_path)

            self._read_pages(into=volume)

            into.add_volume(volume)

    def _read_pages(self, *, into: Volume) -> None:
        if into.path is None:
            raise ScuzzieError(
                "Attempted to read pages into a virtual volume. "
                "This should never happen."
            )

        pages_path = _ensure_path(into.path / "pages")
        for page_path in pages_path.iterdir():
            config = self._read_page_config(page_path)
            page = self._page_from_config(config, path=page_path)
            into.add_page(page)

        missing_pages = [slug for slug in into.page_slugs if slug not in into.pages]
        if missing_pages:
            raise ScuzzieVolumeConfigError(
                f'Volume "{into.title}" lists the following pages '
                "that don't seem to exist: "
                f"{', '.join(missing_pages)}"
            )

    def _read_comic_config(self) -> dict:
        config_path = self.path / "comic.toml"
        return _try_read_toml(config_path, ScuzzieComicConfigError)

    def _read_volume_config(self, path: Path) -> dict:
        config_path = path / "volume.toml"
        return _try_read_toml(config_path, ScuzzieVolumeConfigError)

    def _read_page_config(self, path: Path) -> dict:
        config_path = path / "page.toml"
        return _try_read_toml(config_path, ScuzziePageConfigError)

    def _comic_from_config(self, config: dict, *, path: Path) -> Comic:
        schema = schemas.Comic()
        schema.context["comic_path"] = self.path
        try:
            return schema.load({"path": path, **config})
        except schemas.ValidationError as ex:
            raise ScuzzieComicConfigError(str(ex)) from ex

    def _volume_from_config(self, config: dict, *, path: Path) -> Volume:
        schema = schemas.Volume()
        schema.context["comic_path"] = self.path
        try:
            return schema.load({"path": path, **config})
        except schemas.ValidationError as ex:
            raise ScuzzieVolumeConfigError(str(ex)) from ex

    def _page_from_config(self, config: dict, *, path: Path) -> Page:
        schema = schemas.Page()
        schema.context["comic_path"] = self.path
        try:
            return schema.load({"path": path, **config})
        except schemas.ValidationError as ex:
            raise ScuzzieVolumeConfigError(str(ex)) from ex


class ComicSerializer:
    def __init__(self, comic: Comic, path: Optional[Path] = None) -> None:
        if bool(comic.path) == bool(path):
            raise ScuzzieError(
                "One (and only one) of `comic.path` and `path` must contain a value."
            )

        if path:
            comic.path = path
            self.path = path
        elif comic.path:
            self.path = comic.path

        self.comic = comic

    def write_comic(self) -> None:
        self._write_comic_config()
        self._write_volumes()

    def _write_comic_config(self) -> None:
        config_path = self.path / "comic.toml"
        schema = schemas.Comic()
        schema.context["comic_path"] = self.comic.path
        config = schema.dump(self.comic)
        _try_write_toml(config_path, config)

    def _write_volumes(self) -> None:
        for volume in self.comic.each_volume():
            self._write_volume(volume)

    def _write_volume(self, volume: Volume) -> None:
        self._write_volume_config(volume)
        for page in volume.each_page():
            self._write_page(page)

    def _write_volume_config(self, volume: Volume) -> None:
        path = self.path / "volumes" / volume.slug / "volume.toml"
        schema = schemas.Volume()
        schema.context["comic_path"] = self.comic.path
        config = schema.dump(volume)
        _try_write_toml(path, config)

    def _write_page(self, page: Page) -> None:
        self._write_page_config(page)

    def _write_page_config(self, page: Page) -> None:
        if page.volume and page.volume.path:
            path = page.volume.path / "pages" / page.slug / "page.toml"
            schema = schemas.Page()
            schema.context["comic_path"] = self.comic.path
            config = schema.dump(page)
            _try_write_toml(path, config)
        else:
            raise ScuzzieVolumeConfigError(
                "Tried to save page into null volume or volume with a null path."
            )

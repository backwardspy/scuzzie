"""Defines the comic, volume, and page resources that make up a comic."""
from pathlib import Path
from typing import Iterator, Optional

from slugify import slugify

from scuzzie.exc import ScuzzieError


class Page:
    """One page of a comic."""

    def __init__(self, *, path: Optional[Path], title: str, image: Path) -> None:
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.image = image
        self.volume: Optional[Volume] = None

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Page(path={self.path}, title={self.title}, image={self.image})"

    @property
    def url(self) -> str:
        """Returns the URL of the page."""
        if self.volume is None:
            raise ScuzzieError("Attempt to get path URL but path is not in a volume.")
        return f"/volumes/{self.volume.slug}/pages/{self.slug}.html"


class Volume:
    """A volume is a collection of pages."""

    def __init__(
        self, *, path: Optional[Path], title: str, image: Path, page_slugs: list[str]
    ) -> None:
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.image = image
        self.page_slugs = page_slugs
        self.pages: dict[str, Page] = {}

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return (
            f"Volume(path={self.path}, title={self.title}, image={self.image}, "
            f"page_slugs={self.page_slugs})"
        )

    @property
    def url(self) -> str:
        """Returns the URL of this volume."""
        if self.path is None:
            raise ScuzzieError("Attempt to get volume URL without a path.")
        return f"/volumes/{self.slug}.html"

    @property
    def latest_page(self) -> Page | None:
        """Returns the latest page in this volume, or none if the volume has no pages."""
        if not self.page_slugs:
            return None

        return self.pages[self.page_slugs[-1]]

    def each_page(self) -> Iterator[Page]:
        """Returns an iterator over all pages in this volume."""
        for page_slug in self.page_slugs:
            yield self.pages[page_slug]

    def add_page(self, page: Page) -> None:
        """Add a page to this volume."""
        if page.slug in self.pages:
            raise ScuzzieError(f"Page {page} already exists in {self}")

        page.volume = self

        if page.slug not in self.page_slugs:
            self.page_slugs.append(page.slug)
        self.pages[page.slug] = page


class Comic:
    """A comic is a collection of volumes."""

    def __init__(
        self,
        *,
        path: Optional[Path],
        name: str,
        placeholder: Path,
        volume_slugs: list[str],
    ) -> None:
        self.path = path
        self.name = name
        self.placeholder = placeholder
        self.volume_slugs = volume_slugs
        self.volumes: dict[str, Volume] = {}

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"Comic(path={self.path}, name={self.name}, "
            f"placeholder={self.placeholder}, volume_slugs={self.volume_slugs})"
        )

    @property
    def latest_volume(self) -> Volume | None:
        """Returns the latest volume in the comic, or none if the comic has no volumes."""
        if not self.volume_slugs:
            return None

        return self.volumes[self.volume_slugs[-1]]

    def each_volume(self) -> Iterator[Volume]:
        """Returns an iterator over all volumes in the comic."""
        for volume_slug in self.volume_slugs:
            yield self.volumes[volume_slug]

    def add_volume(self, volume: Volume) -> None:
        """Add a volume to the comic."""
        if volume.slug in self.volumes:
            raise ScuzzieError(f"Volume {volume} already exists in {self}")

        if volume.slug not in self.volume_slugs:
            self.volume_slugs.append(volume.slug)
        self.volumes[volume.slug] = volume

    def create_volume(self, title: str, image: Path) -> Volume:
        """Create and add a new volume to the comic."""
        volume = Volume(path=None, title=title, image=image, page_slugs=[])
        self.add_volume(volume)
        return volume

    def create_page(
        self, *, title: str, image: Optional[Path] = None, volume: Volume
    ) -> Page:
        """Create a new page in the given volume."""
        page = Page(
            path=None,
            title=title,
            image=image if image is not None else self.placeholder,
        )
        volume.add_page(page)
        return page

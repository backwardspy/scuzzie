from typing import Optional, Iterator
from pathlib import Path

from slugify import slugify

from scuzzie.exc import ScuzzieError


class Page:
    def __init__(self, *, path: Optional[Path], title: str, image: Path) -> None:
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.image = image
        self.volume: Optional[Volume] = None

    def __str__(self) -> str:
        return f"(Page) {self.title}"

    @property
    def url(self) -> str:
        if self.volume is None:
            raise ScuzzieError("Attempt to get path URL but path is not in a volume.")
        return f"/volumes/{self.volume.slug}/pages/{self.slug}.html"


class Volume:
    def __init__(
        self, *, path: Optional[Path], title: str, page_slugs: list[str]
    ) -> None:
        self.path = path
        self.title = title
        self.slug = slugify(title)
        self.page_slugs = page_slugs
        self.pages: dict[str, Page] = {}

    def __str__(self) -> str:
        return f"(Volume) {self.title}"

    @property
    def url(self) -> str:
        if self.path is None:
            raise ScuzzieError("Attempt to get volume URL without a path.")
        return f"/volumes/{self.slug}.html"

    def each_page(self) -> Iterator[Page]:
        for page_slug in self.page_slugs:
            yield self.pages[page_slug]

    def add_page(self, page: Page) -> None:
        if page.slug in self.pages:
            raise ScuzzieError(f"Attempt to add duplicate {page} to {self}")

        page.volume = self

        if page.slug not in self.page_slugs:
            self.page_slugs.append(page.slug)
        self.pages[page.slug] = page


class Comic:
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
        return f"(Comic) {self.name}"

    def each_volume(self) -> Iterator[Volume]:
        for volume_slug in self.volume_slugs:
            yield self.volumes[volume_slug]

    def add_volume(self, volume: Volume) -> None:
        if volume.slug in self.volumes:
            raise ScuzzieError(f"Attempt to add duplicate {volume} to {self}")

        if volume.slug not in self.volume_slugs:
            self.volume_slugs.append(volume.slug)
        self.volumes[volume.slug] = volume

    def create_volume(self, title: str) -> Volume:
        volume = Volume(path=None, title=title, page_slugs=[])
        self.add_volume(volume)
        return volume

    def create_page(
        self, *, title: str, image: Optional[Path] = None, volume: Volume
    ) -> Page:
        page = Page(
            path=None,
            title=title,
            image=image if image is not None else self.placeholder,
        )
        volume.add_page(page)
        return page

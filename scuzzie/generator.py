from pathlib import Path
import shutil

from mako.template import Template
from mako.lookup import TemplateLookup

from .resources import Comic, Volume, Page
from .templator import Templator
from .exc import (
    ScuzzieError,
    ScuzziePageTemplateError,
)


class SiteGenerator:
    class Reader:
        comic: Comic

        def create_page(self, title: str, *, volume: Volume) -> None:
            raise NotImplementedError

    class FileReader(Reader):
        def __init__(self, comic: Comic) -> None:
            self.comic = comic
            self.templator = self.load_templates()

        def load_templates(self) -> Templator:
            if self.comic.path is None:
                raise ScuzzieError(
                    "Attempted to load templates for a virtual comic. "
                    "This should never happen."
                )

            templates_path = self.comic.path / "templates"
            lookup = TemplateLookup(directories=[templates_path])

            def load_template(name: str) -> Template:
                template_path = templates_path / name
                with template_path.open("r") as f:
                    return Template(f.read(), lookup=lookup)

            return Templator(
                load_template("index.mako"),
                load_template("archive.mako"),
                load_template("volume.mako"),
                load_template("page.mako"),
            )

    class Writer:
        def __init__(self, templator: Templator):
            self.templator = templator

        def write_index(self, comic: Comic) -> None:
            raise NotImplementedError

        def write_archive(self, comic: Comic) -> None:
            raise NotImplementedError

        def write_volume(self, volume: Volume) -> None:
            raise NotImplementedError

        def write_page(self, page: Page) -> None:
            raise NotImplementedError

        def copy_assets(self, path: Path) -> None:
            raise NotImplementedError

    class FileWriter(Writer):
        def __init__(self, *, path: Path, templator: Templator) -> None:
            super().__init__(templator)
            self.path = path

        def write_index(self, comic: Comic) -> None:
            index_path = self.path / "index.html"
            content = self.templator.render_index(comic)
            self._write_content(index_path, content)

        def write_archive(self, comic: Comic) -> None:
            archive_path = self.path / "archive.html"
            content = self.templator.render_archive(comic)
            self._write_content(archive_path, content)

        def write_volume(self, volume: Volume) -> None:
            volume_path = self.path / "volumes" / f"{volume.slug}.html"
            content = self.templator.render_volume(volume)
            self._write_content(volume_path, content)

        def write_page(self, page: Page) -> None:
            if page.volume:
                page_path = (
                    self.path
                    / "volumes"
                    / page.volume.slug
                    / "pages"
                    / f"{page.slug}.html"
                )
            else:
                raise ScuzziePageTemplateError(
                    page, reason="Page has not been assigned to a volume."
                )
            content = self.templator.render_page(page)
            self._write_content(page_path, content)

        def copy_assets(self, path: Path) -> None:
            shutil.copytree(path, self.path, dirs_exist_ok=True)

        @staticmethod
        def _write_content(path: Path, content: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w") as f:
                f.write(content)

    def __init__(self, reader: Reader, writer: Writer) -> None:
        self.reader = reader
        self.writer = writer

    def run(self) -> None:
        comic = self.reader.comic

        if comic.path is None:
            raise ScuzzieError(
                "Attempted to generate a site for a virtual comic. "
                "This should never happen."
            )

        print(f"Building comic {comic.name}")

        print("Building index")
        self.writer.write_index(comic)

        print("Building archive")
        self.writer.write_archive(comic)

        for volume in comic.each_volume():
            print(f"Building volume {volume.title}")
            self.writer.write_volume(volume)

            for page in volume.each_page():
                print(f"  Building page {page.title}")
                self.writer.write_page(page)

        print("Copying static assets")
        self.writer.copy_assets(comic.path / "assets")

        print("Done!")

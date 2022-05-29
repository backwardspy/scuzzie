"""
The main generator module, provides tools for reading & writing site resources.
"""
import shutil
from pathlib import Path

from mako.lookup import TemplateLookup
from mako.template import Template

from .exc import ScuzzieError, ScuzziePageTemplateError
from .resources import Comic, Page, Volume
from .templator import Templator


class FileWriter:
    """
    Uses a templator to render comic pages and write them to the given path.
    """

    def __init__(self, *, path: Path, templator: Templator) -> None:
        self.path = path
        self.templator = templator

    def write_index_page(self, comic: Comic) -> None:
        """Renders & writes the index page."""
        index_page_path = self.path / "index.html"
        content = self.templator.render_index_page(comic)
        self._write_content(index_page_path, content)

    def write_about_page(self, comic: Comic) -> None:
        """Renders & writes the about page."""
        about_page_path = self.path / "about.html"
        content = self.templator.render_about(comic)
        self._write_content(about_page_path, content)

    def write_archive_page(self, comic: Comic) -> None:
        """Renders & writes the archive page."""
        archive_page_path = self.path / "archive.html"
        content = self.templator.render_archive_page(comic)
        self._write_content(archive_page_path, content)

    def write_volume(self, volume: Volume, *, comic: Comic) -> None:
        """Renders & writes a volume of pages."""
        volume_path = self.path / "volumes" / f"{volume.slug}.html"
        content = self.templator.render_volume(volume, comic=comic)
        self._write_content(volume_path, content)

    def write_page(self, page: Page, *, comic: Comic) -> None:
        """Renders & writes a comic page."""
        if page.volume:
            page_path = (
                self.path / "volumes" / page.volume.slug / "pages" / f"{page.slug}.html"
            )
        else:
            raise ScuzziePageTemplateError(
                page, reason="Page has not been assigned to a volume."
            )
        content = self.templator.render_page(page, comic=comic)
        self._write_content(page_path, content)

    def copy_assets(self, path: Path) -> None:
        """Copies static assets from the given path to the output path."""
        shutil.copytree(path, self.path, dirs_exist_ok=True)

    @staticmethod
    def _write_content(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as file:
            file.write(content)


def load_templates(comic: Comic) -> Templator:
    """Loads templates for the given comic."""
    if comic.path is None:
        raise ScuzzieError(
            "Attempted to load templates for a virtual comic. "
            "This should never happen."
        )

    templates_path = comic.path / "templates"
    lookup = TemplateLookup(directories=[templates_path])

    def load_template(name: str) -> Template:
        template_path = templates_path / name
        with template_path.open("r") as template_file:
            return Template(template_file.read(), lookup=lookup)

    return Templator(
        index_page_template=load_template("index.mako"),
        about_page_template=load_template("about.mako"),
        archive_page_template=load_template("archive.mako"),
        volume_template=load_template("volume.mako"),
        page_template=load_template("page.mako"),
    )


def generate_site(comic: Comic, writer: FileWriter) -> None:
    """
    Generates the site for the given comic and writes it using the given writer.
    """
    if comic.path is None:
        raise ScuzzieError(
            "Attempted to generate a site for a virtual comic. "
            "This should never happen."
        )

    print(f"Building comic {comic.name}")

    print("Building index page")
    writer.write_index_page(comic)

    print("Building about page")
    writer.write_about_page(comic)

    print("Building archive page")
    writer.write_archive_page(comic)

    for volume in comic.each_volume():
        print(f"Building volume {volume.title}")
        writer.write_volume(volume, comic=comic)

        for page in volume.each_page():
            print(f"  Building page {page.title}")
            writer.write_page(page, comic=comic)

    print("Copying static assets")
    writer.copy_assets(comic.path / "assets")

    print("Done!")

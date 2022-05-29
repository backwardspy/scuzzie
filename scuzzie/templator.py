"""Defines the templator class."""
from mako.template import Template

from scuzzie.exc import ScuzzieError

from .resources import Comic, Page, Volume


class Templator:
    """Creates comic pages from templates."""

    def __init__(
        self,
        index_template: Template,
        archive_template: Template,
        volume_template: Template,
        page_template: Template,
    ):
        self.index_template = index_template
        self.archive_template = archive_template
        self.volume_template = volume_template
        self.page_template = page_template

    def render_index(self, comic: Comic) -> str:
        """Renders the index page."""
        try:
            return self.index_template.render(comic=comic)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering index: {ex}") from ex

    def render_archive(self, comic: Comic) -> str:
        """Renders the archive page."""
        try:
            return self.archive_template.render(comic=comic)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering archive: {ex}") from ex

    def render_volume(self, volume: Volume) -> str:
        """Renders a volume of pages."""
        try:
            return self.volume_template.render(volume=volume)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering volume {volume}: {ex}") from ex

    def render_page(self, page: Page) -> str:
        """Renders a comic page."""
        try:
            return self.page_template.render(page=page)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering page {page}: {ex}") from ex

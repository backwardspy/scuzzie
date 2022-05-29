"""Defines the templator class."""
from mako.template import Template

from scuzzie.exc import ScuzzieError

from .resources import Comic, Page, Volume


class Templator:
    """Creates comic pages from templates."""

    def __init__(
        self,
        *,
        index_page_template: Template,
        about_page_template: Template,
        archive_page_template: Template,
        volume_template: Template,
        page_template: Template,
    ):
        self.index_template = index_page_template
        self.about_template = about_page_template
        self.archive_template = archive_page_template
        self.volume_template = volume_template
        self.page_template = page_template

    def render_index_page(self, comic: Comic) -> str:
        """Renders the index page."""
        try:
            return self.index_template.render(comic=comic)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering index page: {ex}") from ex

    def render_about(self, comic: Comic) -> str:
        """Renders the about page."""
        try:
            return self.about_template.render(comic=comic)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering about page: {ex}") from ex

    def render_archive_page(self, comic: Comic) -> str:
        """Renders the archive page."""
        try:
            return self.archive_template.render(comic=comic)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering archive page: {ex}") from ex

    def render_volume(self, volume: Volume, *, comic: Comic) -> str:
        """Renders a volume of pages."""
        try:
            return self.volume_template.render(comic=comic, volume=volume)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering volume {volume}: {ex}") from ex

    def render_page(self, page: Page, *, comic: Comic) -> str:
        """Renders a comic page."""
        try:
            return self.page_template.render(comic=comic, page=page)
        except Exception as ex:
            raise ScuzzieError(f"Error rendering page {page}: {ex}") from ex

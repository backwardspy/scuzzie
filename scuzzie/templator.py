from mako.template import Template

from .resources import Comic, Volume, Page


class Templator:
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
        return self.index_template.render(comic=comic)

    def render_archive(self, comic: Comic) -> str:
        return self.archive_template.render(comic=comic)

    def render_volume(self, volume: Volume) -> str:
        return self.volume_template.render(volume=volume)

    def render_page(self, page: Page) -> str:
        return self.page_template.render(page=page)

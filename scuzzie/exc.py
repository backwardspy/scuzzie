from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .resources import Page


class ScuzzieError(Exception):
    pass


class ScuzzieConfigError(ScuzzieError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            f"There is an issue with a {self.file_type} config file: {reason}"
        )

    @property
    def file_type(self) -> str:
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )


class ScuzzieComicConfigError(ScuzzieConfigError):
    @property
    def file_type(self) -> str:
        return "comic"


class ScuzzieVolumeConfigError(ScuzzieConfigError):
    @property
    def file_type(self) -> str:
        return "volume"


class ScuzziePageConfigError(ScuzzieConfigError):
    @property
    def file_type(self) -> str:
        return "page"


class ScuzzieTemplateError(ScuzzieError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            f"There is an issue with a {self.template_type} template "
            f"for resource {self.resource_name}: {reason}"
        )

    @property
    def template_type(self) -> str:
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )

    @property
    def resource_name(self) -> str:
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )


class ScuzziePageTemplateError(ScuzzieTemplateError):
    def __init__(self, page: "Page", *, reason: str) -> None:
        self.page = page
        super().__init__(reason)

    @property
    def template_type(self) -> str:
        return "page"

    @property
    def resource_name(self) -> str:
        return self.page.title

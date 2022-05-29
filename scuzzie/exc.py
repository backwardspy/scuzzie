"""Custom error type definitions."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .resources import Page


class ScuzzieError(Exception):
    """Base class for all Scuzzie errors."""


class ScuzzieConfigError(ScuzzieError):
    """Base class for errors related to config files."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"There is an issue with a {self.file_type} config file: {reason}"
        )

    @property
    def file_type(self) -> str:
        """Returns the type of file that caused the error."""
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )


class ScuzzieComicConfigError(ScuzzieConfigError):
    """Raised when there is an issue with the comic config file."""

    @property
    def file_type(self) -> str:
        return "comic"


class ScuzzieVolumeConfigError(ScuzzieConfigError):
    """Raised when there is an issue with a volume config file."""

    @property
    def file_type(self) -> str:
        return "volume"


class ScuzziePageConfigError(ScuzzieConfigError):
    """Raised when there is an issue with a page config file."""

    @property
    def file_type(self) -> str:
        return "page"


class ScuzzieTemplateError(ScuzzieError):
    """Base class for templating errors."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"There is an issue with a {self.template_type} template "
            f"for resource {self.resource_name}: {reason}"
        )

    @property
    def template_type(self) -> str:
        """Returns the type of template that caused the error."""
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )

    @property
    def resource_name(self) -> str:
        """Returns the name of the resource that caused the error."""
        raise NotImplementedError(
            "Don't raise this error type directly, use a subclass."
        )


class ScuzziePageTemplateError(ScuzzieTemplateError):
    """Raised when there is an issue with a page template."""

    def __init__(self, page: "Page", *, reason: str) -> None:
        self.page = page
        super().__init__(reason)

    @property
    def template_type(self) -> str:
        return "page"

    @property
    def resource_name(self) -> str:
        return self.page.title

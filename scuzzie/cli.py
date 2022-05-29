"""Defines the Scuzzie command line interface."""
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, NamedTuple

import click

from scuzzie.comic import read_comic, write_comic
from scuzzie.exc import ScuzzieError
from scuzzie.generator import FileWriter, generate_site, load_templates
from scuzzie.resources import Comic, Volume

DEFAULT_COMIC_PATH = "comic"
DEFAULT_OUTPUT_PATH = "site"


class Context(NamedTuple):
    """Defines a global context for use by CLI functions."""

    comic_path: Path
    output_path: Path


CONTEXT: Context


@contextmanager
def scuzzie_error_handler() -> Generator[None, None, None]:
    """Provides a context manager that handles ScuzzieErrors."""
    try:
        yield
    except ScuzzieError as ex:
        click.secho(str(ex), err=True, fg="red")
        raise click.Abort() from ex


def prompt_for_volume(volumes: list[Volume]) -> Volume:
    """Prompt the user to choose a volume from the list."""
    click.echo("Available Volumes:")
    for idx, volume in enumerate(volumes):
        click.echo(f"{idx + 1:2}: {volume.title}")
    click.echo()

    while True:
        idx = int(click.prompt("Select a volume", type=int, default=str(len(volumes))))
        if 1 <= idx <= len(volumes):
            break
        click.secho("Please select a valid volume number.", fg="red")

    return volumes[idx - 1]


def sanitise_image_path(image_path_str: str, *, comic_path: Path) -> Path:
    """Sanitise the given image path string."""
    image_path = Path(image_path_str.strip("\"'")).absolute()
    assets_path = (comic_path / "assets").absolute()

    if assets_path not in image_path.parents:
        click.secho(
            f"{image_path} is not in the assets directory.\n"
            "Please provide a path relative to the assets directory.",
            fg="red",
        )
        raise click.Abort

    # we treat the assets directory as the root of the comic
    return Path("/") / image_path.relative_to(assets_path)


def prompt_image_path(comic: Comic, *, resource_type: str) -> Path:
    """Prompt the user to enter an image path."""
    click.echo(
        "\n"
        f"You can provide an image for the {resource_type.lower()} now, "
        "or you can leave it blank to use the placeholder image. "
        "\n"
        "You can also drag the image onto this prompt rather than typing it manually."
        "\n"
    )

    image_path = click.prompt(f"{resource_type.title()} image", default="")
    if not image_path:
        image_path = str(
            CONTEXT.comic_path / "assets" / str(comic.placeholder).strip("/")
        )

    return sanitise_image_path(image_path, comic_path=CONTEXT.comic_path)


@click.group()
@click.option(
    "--comic",
    "-c",
    "comic_path_string",
    type=click.Path(exists=True, file_okay=False),
    default=DEFAULT_COMIC_PATH,
    show_default=True,
)
@click.option(
    "--output",
    "-o",
    "output_path_string",
    type=click.Path(exists=False, file_okay=False, writable=True),
    default=DEFAULT_OUTPUT_PATH,
    show_default=True,
)
@click.version_option()
def scuzzie(comic_path_string: str, output_path_string: str) -> None:
    """Click command group that sets up the global CLI context."""
    # not a huge fan of this global context, but click's pass_context doesn't
    # play too nicely with type annotations...
    global CONTEXT  # pylint: disable=global-statement
    CONTEXT = Context(
        comic_path=Path(comic_path_string), output_path=Path(output_path_string)
    )


@scuzzie.command()
def build() -> None:
    """Builds the site."""
    with scuzzie_error_handler():
        comic = read_comic(CONTEXT.comic_path)
        templator = load_templates(comic)
        writer = FileWriter(path=CONTEXT.output_path, templator=templator)
        generate_site(comic, writer)


@scuzzie.group()
def new() -> None:
    """CLI command group for making new comic resources."""


@new.command(name="page")
def _() -> None:
    """CLI command that makes a new page resource."""
    with scuzzie_error_handler():
        comic = read_comic(CONTEXT.comic_path)

        # realise the generator for easy indexing et cetera
        volumes = list(comic.each_volume())

        if not volumes:
            raise ScuzzieError(
                "No volumes found in comic, please run `scuzzie new volume` first!"
            )

        if len(volumes) == 1:
            volume = volumes[0]
        else:
            volume = prompt_for_volume(volumes)

        click.echo(f"Using volume: {volume}")

        click.echo(
            "\n"
            "Please provide some page details. "
            "These can all be changed later."
            "\n"
        )

        title = click.prompt("Provide a title for the new page")
        image_path = prompt_image_path(comic, resource_type="page")

        click.echo(
            "\n"
            "Page details:"
            "\n"
            f"  Volume: {volume.title}\n"
            f"  Title: {title}\n"
            f"  Image: {image_path}\n"
        )

        if not click.confirm("Are these details correct?", default=True):
            raise click.Abort

        comic.create_page(title=title, image=image_path, volume=volume)
        write_comic(comic)
        click.secho("Page created.", fg="green")


@new.command(name="volume")
def _() -> None:
    """CLI command that makes a new volume resource."""
    with scuzzie_error_handler():
        comic = read_comic(CONTEXT.comic_path)
        title = click.prompt("Provide a title for the new volume")
        image_path = prompt_image_path(comic, resource_type="volume")

        click.echo(f"\nVolume details:\n  Title: {title}\n  Image: {image_path}\n")

        if not click.confirm("Are these details correct?", default=True):
            raise click.Abort

        comic.create_volume(title=title, image=image_path)
        write_comic(comic)
        click.secho("Volume created.", fg="green")


if __name__ == "__main__":
    # pylint can't tell that click will fill out these parameters automatically.
    scuzzie()  # pylint: disable=no-value-for-parameter

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, NamedTuple

import click

from scuzzie import ComicDeserializer, ComicSerializer, SiteGenerator, Volume
from scuzzie.exc import ScuzzieError

DEFAULT_COMIC_PATH = "comic"
DEFAULT_OUTPUT_PATH = "site"


class Context(NamedTuple):
    comic_path: Path
    output_path: Path


context: Context


@contextmanager
def scuzzie_error_handler() -> Generator[None, None, None]:
    try:
        yield
    except ScuzzieError as ex:
        click.secho(str(ex), err=True, fg="red")
        raise click.Abort() from ex


def prompt_for_volume(volumes: list[Volume]) -> Volume:
    click.echo("Available Volumes:")
    for idx, volume in enumerate(volumes):
        click.echo(f"{idx + 1:2}: {volume.title}")
    click.echo()

    while True:
        idx = int(click.prompt("Select a volume", type=int, default=str(len(volumes))))
        if 1 <= idx <= len(volumes):
            break
        else:
            click.secho("Please select a valid volume number.", fg="red")

    return volumes[idx - 1]


def sanitise_image_path(image_path_str: str, *, comic_path: Path) -> Path:
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
def scuzzie(comic_path_string: str, output_path_string: str):
    # not a huge fan of this global context, but click's pass_context doesn't
    # play too nicely with type annotations...
    global context
    context = Context(
        comic_path=Path(comic_path_string), output_path=Path(output_path_string)
    )


@scuzzie.command()
def build():
    with scuzzie_error_handler():
        deserializer = ComicDeserializer(context.comic_path)
        comic = deserializer.read_comic()
        reader = SiteGenerator.FileReader(comic)
        writer = SiteGenerator.FileWriter(
            path=context.output_path, templator=reader.templator
        )
        SiteGenerator(reader, writer).run()


@scuzzie.group()
def new():
    pass


@new.command()
def page():
    with scuzzie_error_handler():
        deserializer = ComicDeserializer(context.comic_path)
        comic = deserializer.read_comic()

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

        click.echo(
            "\n"
            "You can provide an image for the new page now, "
            "or you can leave it blank to use the placeholder image. "
            "\n"
            "You can also drag the image onto this prompt rather than typing it manually."
            "\n"
        )

        image_path = sanitise_image_path(
            click.prompt("Page image", default=""), comic_path=context.comic_path
        )

        comic.create_page(title=title, image=image_path, volume=volume)

        click.echo(
            "\n"
            "Page details:"
            "\n"
            f"  Volume: {volume.title}\n"
            f"  Title: {title}\n"
            f"  Image: {image_path}\n"
        )

        if click.confirm("Are these details correct?", default=True):
            serializer = ComicSerializer(comic)
            serializer.write_comic()
            click.secho("Page created.", fg="green")


@new.command()
def volume():
    with scuzzie_error_handler():
        deserializer = ComicDeserializer(context.comic_path)
        comic = deserializer.read_comic()

        title = click.prompt("Provide a title for the new volume")

        comic.create_volume(title=title)

        serializer = ComicSerializer(comic)
        serializer.write_comic()


if __name__ == "__main__":
    scuzzie()

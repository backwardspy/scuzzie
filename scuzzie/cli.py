from contextlib import contextmanager
from typing import NamedTuple, Generator
from pathlib import Path

import click

from scuzzie import ComicDeserializer, ComicSerializer, SiteGenerator
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

        print("Available Volumes:")
        # realise the generator for easy indexing et cetera
        volumes = list(comic.each_volume())
        for idx, volume in enumerate(volumes):
            print(f"{idx + 1:2}: {volume.title}")
        print()

        while True:
            idx = int(
                click.prompt("Select a volume", type=int, default=str(len(volumes)))
            )
            if 1 <= idx <= len(volumes):
                break
            else:
                click.secho("Please select a valid volume number.", fg="red")

        title = click.prompt("Provide a title for the new page")

        volume = volumes[idx - 1]
        comic.create_page(title=title, volume=volume)

        serializer = ComicSerializer(comic)
        serializer.write_comic()


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

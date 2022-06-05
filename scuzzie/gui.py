"""PySimpleGUI for scuzzie."""
import os
from importlib.metadata import version
from pathlib import Path

import PySimpleGUI as gui

from scuzzie.comic import read_comic, write_comic
from scuzzie.exc import ScuzzieError
from scuzzie.generator import FileWriter, generate_site, load_templates


def sanitise_image_path(image_path: Path, *, assets_path: Path) -> Path | None:
    """Sanitises the image path."""
    image_path = image_path.absolute()

    if assets_path.absolute() not in image_path.parents:
        gui.popup(
            "Image must be in the assets directory.",
            title="Error",
        )
        return None

    return Path("/") / image_path.relative_to(assets_path.absolute())


def build(*, comic_path: Path, site_path: Path) -> None:
    """Builds the site."""
    comic = read_comic(comic_path)
    templator = load_templates(comic)
    writer = FileWriter(path=site_path, templator=templator)
    generate_site(comic, writer)


def new_volume(comic_path: Path) -> None:
    """Make a new volume."""
    comic = read_comic(comic_path)
    if not comic.path:
        raise ScuzzieError(
            "read_comic returned a virtual comic. This should never happen!"
        )

    assets_path = comic.path / "assets"
    placeholder = Path(str(comic.placeholder).strip("/"))

    layout = [
        [gui.Text("Title", size=6), gui.Input(key="title")],
        [
            gui.Text("Image", size=6),
            gui.Input(assets_path / placeholder, key="image"),
            gui.FileBrowse(key="image", initial_folder=assets_path),
        ],
        [gui.Push(), gui.Button("Cancel"), gui.Button("OK")],
    ]
    window = gui.Window("New Volume", layout, modal=True)

    while True:
        event, values = window.read()

        if event in [gui.WIN_CLOSED, "Cancel"]:
            break

        errors = []
        if not values["title"]:
            errors.append("Please provide a title for the new volume")
        if not values["image"]:
            errors.append("Please provide an image for the new volume")
        if errors:
            gui.popup("\n".join(errors), title="Error")
            continue

        title = values["title"]
        image_path = sanitise_image_path(Path(values["image"]), assets_path=assets_path)
        if not image_path:
            continue

        comic.create_volume(title, image_path)
        write_comic(comic)
        break

    window.close()


def new_page(comic_path: Path) -> None:
    """Make a new page in a volume."""
    comic = read_comic(comic_path)
    if not comic.path:
        raise ScuzzieError(
            "read_comic returned a virtual comic. This should never happen!"
        )

    volumes = list(comic.each_volume())
    if not volumes:
        gui.popup("No volumes found, please make one first!", title="Error")
        return

    assets_path = comic.path / "assets"
    placeholder = Path(str(comic.placeholder).strip("/"))

    layout = [
        [
            gui.Text("Volume", size=6),
            gui.Combo(volumes, default_value=volumes[-1], key="volume"),
        ],
        [gui.Text("Title", size=6), gui.Input(key="title")],
        [
            gui.Text("Image", size=6),
            gui.Input(assets_path / placeholder, key="image"),
            gui.FileBrowse(key="image", initial_folder=assets_path),
        ],
        [gui.Push(), gui.Button("Cancel"), gui.Button("OK")],
    ]
    window = gui.Window("New Page", layout, modal=True)

    while True:
        event, values = window.read()

        if event in [gui.WIN_CLOSED, "Cancel"]:
            break

        errors = []
        if not values["title"]:
            errors.append("Please provide a title for the new volume")
        if not values["image"]:
            errors.append("Please provide an image for the new volume")
        if errors:
            gui.popup("\n".join(errors), title="Error")
            continue

        title = values["title"]
        volume = values["volume"]
        image_path = sanitise_image_path(Path(values["image"]), assets_path=assets_path)
        if not image_path:
            continue

        comic.create_page(title=title, image=image_path, volume=volume)
        write_comic(comic)
        break

    window.close()


def menu() -> None:
    """Menu window."""
    layout = [
        [
            gui.Text("Comic path", size=9),
            gui.Input("comic", key="comic_path"),
            gui.FolderBrowse(key="comic_path"),
        ],
        [
            gui.Text("Site path", size=9),
            gui.Input("site", key="site_path"),
            gui.FolderBrowse(key="site_path"),
        ],
        [
            gui.Push(),
            gui.Button("Build"),
            gui.Button("New Volume"),
            gui.Button("New Page"),
        ],
    ]

    window = gui.Window(f"scuzzie {version(__package__)}", layout)

    while True:
        event, values = window.read()

        match event:
            case gui.WINDOW_CLOSED:
                break

        comic_path = Path(os.path.relpath(values["comic_path"], Path.cwd()))
        site_path = Path(os.path.relpath(values["site_path"], Path.cwd()))

        match event:
            case "Build":
                build(comic_path=comic_path, site_path=site_path)

            case "New Volume":
                new_volume(comic_path)

            case "New Page":
                new_page(comic_path)

    window.close()


def scuzzie() -> None:
    """Runs the GUI."""
    gui.theme("Dark Blue 4")
    menu()


if __name__ == "__main__":
    scuzzie()

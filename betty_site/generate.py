from __future__ import annotations
import os
import shutil
from contextlib import suppress
from os import remove, walk
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from jinja2 import FileSystemLoader, Environment, StrictUndefined, select_autoescape

from betty_site import OUTPUT_DIRECTORY_PATH, OUTPUT_WWW_DIRECTORY_PATH, ASSETS_OUTPUT_DIRECTORY_PATH, \
    ASSETS_TEMPLATES_DIRECTORY_PATH
from betty_site.release import get_releases, get_stable_releases, get_unstable_releases, \
    get_unstable_release_for_stable_release, filter_by_download_type, DownloadType


def generate() -> None:
    # Keep the www directory so the Docker volumes stay intact.
    _empty_directory(OUTPUT_DIRECTORY_PATH, ('www',))
    _empty_directory(OUTPUT_WWW_DIRECTORY_PATH)
    os.makedirs(OUTPUT_DIRECTORY_PATH, exist_ok=True)
    shutil.copytree(ASSETS_OUTPUT_DIRECTORY_PATH, OUTPUT_DIRECTORY_PATH, dirs_exist_ok=True)
    shutil.copytree(Path('node_modules') / 'bootstrap-icons' / 'icons', OUTPUT_WWW_DIRECTORY_PATH / 'icons')
    renderer = Jinja2Renderer()
    renderer.render_directory(OUTPUT_DIRECTORY_PATH)
    _generate_releases(renderer)
    _set_output_directory_permissions()


def _generate_releases(renderer: Jinja2Renderer) -> None:
    for release in get_releases().values():
        release_output_www_directory_path = OUTPUT_WWW_DIRECTORY_PATH / 'release' / release.version
        os.makedirs(release_output_www_directory_path)
        shutil.copytree(ASSETS_TEMPLATES_DIRECTORY_PATH / 'release', release_output_www_directory_path, dirs_exist_ok=True)
        renderer.render_directory(release_output_www_directory_path, {
            'release': release,
        })


def _empty_directory(directory_path: Path, excludes: Optional[Tuple] = None) -> None:
    if excludes is None:
        excludes = ()
    with suppress(FileNotFoundError):
        for directory_path_str, subdirectory_names, file_names in os.walk(directory_path):
            for subdirectory_name in subdirectory_names:
                if subdirectory_name in excludes:
                    continue
                shutil.rmtree(directory_path / subdirectory_name)
            for file_name in file_names:
                if subdirectory_name in excludes:
                    continue
                os.remove(directory_path / file_name)


def _set_output_directory_permissions() -> None:
    os.chmod(OUTPUT_DIRECTORY_PATH, 0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(OUTPUT_DIRECTORY_PATH):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            os.chmod(directory_path / subdirectory_name, 0o755)
        for file_name in file_names:
            os.chmod(directory_path / file_name, 0o644)


class Jinja2Renderer:
    def __init__(self):
        loader = FileSystemLoader(ASSETS_TEMPLATES_DIRECTORY_PATH)
        self._environment = Environment(loader=loader,
                                        undefined=StrictUndefined,
                                        autoescape=select_autoescape(['html']),
                                        trim_blocks=True,
                                        )
        self._environment.globals['betty_release_download_type'] = DownloadType
        self._environment.globals['betty_releases'] = get_releases()
        self._environment.globals['betty_stable_releases'] = get_stable_releases()
        self._environment.globals['betty_unstable_releases'] = get_unstable_releases()
        self._environment.filters['betty_unstable_release_for_stable_release'] = get_unstable_release_for_stable_release
        self._environment.filters['betty_filter_release_by_download_type'] = filter_by_download_type

    def render_directory(self, directory_path: str, args: Dict[str, Any] = None) -> None:
        for walked_directory_path, _, filenames in walk(directory_path):
            for filename in filenames:
                file_path = Path(walked_directory_path) / filename
                self.render_file(file_path, args)

    def render_file(self, file_path: Path, args: Dict[str, Any] = None) -> None:
        if not file_path.name.endswith('.j2'):
            return
        if args is None:
            args = {}
        template_name = '/'.join(Path(file_path).parts)
        template = FileSystemLoader('/').load(self._environment, template_name, self._environment.globals)
        file_destination_path = str(file_path)[:-3]
        with open(file_destination_path, 'w') as f:
            f.write(template.render(args))
        remove(file_path)


if __name__ == '__main__':
    generate()

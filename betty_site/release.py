import json
from contextlib import suppress
from enum import Enum, unique
from typing import List, Optional, Dict, Iterator, Iterable

import semver

from betty_site import ASSETS_OUTPUT_WWW_DIRECTORY_PATH


@unique
class DownloadType(Enum):
    SOURCE_ZIP = 'source_zip'
    SOURCE_TAR = 'source_tar'
    EXECUTABLE_MAC_ZIP = 'executable_mac_zip'
    EXECUTABLE_WINDOWS_ZIP = 'executable_windows_zip'


class Download:
    def __init__(self, url: str, download_type: DownloadType):
        self.url = url
        self.type = download_type


class Release:
    def __init__(self, version: str, downloads: List[Download], stable: bool):
        self.version = version
        self.downloads = {download.type: download for download in downloads}
        self.stable = stable


_releases_data = None


def _get_releases_data():
    global _releases_data

    if _releases_data is None:
        with open(ASSETS_OUTPUT_WWW_DIRECTORY_PATH / 'release' / 'index.json') as f:
            _releases_data = json.load(f)
    return _releases_data


def get_releases() -> Dict[str, Release]:
    return {
        version: Release(
            version,
            [
                Download(url, DownloadType(download_type))
                for download_type, url
                in release_data['downloads'].items()
            ],
            release_data.get('stable', True)
        )
        for version, release_data
        in _get_releases_data().items()
    }


def get_stable_releases() -> List[Release]:
    return sorted(
        filter(
            lambda release: release.stable,
            get_releases().values(),
        ),
        key=lambda release: semver.VersionInfo.parse(release.version),
        reverse=True,
    )


def get_unstable_releases() -> List[Release]:
    return sorted(
        filter(
            lambda release: not release.stable,
            get_releases().values(),
        ),
        key=lambda release: release.version.split('.'),
        reverse=True,
    )


def get_unstable_release_for_stable_release(version: str) -> Optional[Release]:
    with suppress(KeyError):
        return get_releases()[version[:version.rindex('.')] + '.x']


def filter_by_download_type(releases: Iterator[Release], download_types: Iterable[DownloadType]) -> List[Release]:
    return [
        release
        for release
        in releases
        if set(download_types).union([
            download.type
            for download
            in release.downloads.values()
        ])
    ]

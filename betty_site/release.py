import re
from contextlib import suppress
from datetime import datetime
from enum import Enum, unique
from typing import List, Optional, Dict, Iterator, Iterable

import requests
import semver


@unique
class DownloadType(Enum):
    SOURCE_ZIP = 'source_zip'
    SOURCE_TAR = 'source_tar'
    EXECUTABLE_MAC_ZIP = 'executable_mac_zip'
    EXECUTABLE_WINDOWS_ZIP = 'executable_windows_zip'


_FILE_NAME_TO_DOWNLOAD_TYPE = {
    'betty.app.zip': DownloadType.EXECUTABLE_MAC_ZIP,
    'betty.exe.zip': DownloadType.EXECUTABLE_WINDOWS_ZIP,
}


class Download:
    def __init__(self, url: str, download_type: DownloadType):
        self.url = url
        self.type = download_type


class Release:
    def __init__(self, version: str, date: datetime, downloads: List[Download], stable: bool):
        self.version = version
        self.date = date
        self.downloads = {download.type: download for download in downloads}
        self.stable = stable


_releases = None


def get_releases() -> Dict[str, Release]:
    global _releases

    if _releases is None:
        _releases = {}
        for release_data in requests.get('https://api.github.com/repos/bartfeenstra/betty/releases?per_page=100').json():
            if release_data['draft']:
                continue

            is_release_tag = semver.VersionInfo.isvalid(release_data['tag_name'])
            is_dev_release = re.match(r'^\d+\.\d+\.x-dev$', release_data['tag_name'])

            if not (is_release_tag or is_dev_release):
                continue

            release = Release(
                release_data['tag_name'],
                release_data['created_at'],
                [
                    Download(
                        assets_data['browser_download_url'],
                        DownloadType(_FILE_NAME_TO_DOWNLOAD_TYPE[assets_data['name']]),
                    )
                    for assets_data
                    in release_data['assets']
                    if assets_data['name'] in _FILE_NAME_TO_DOWNLOAD_TYPE
                ],
                not (release_data.get('prerelease', True) or is_dev_release)
            )

            _releases[release.version] = release

    return _releases


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

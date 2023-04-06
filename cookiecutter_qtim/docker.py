"""Utilities for finding suitable docker images."""
import re
from textwrap import dedent, fill
from typing import Iterable, Optional

import requests


NVIDIA_TAG_RE = re.compile(
    r"(?P<cuda_major>\d+)\.(?P<cuda_minor>\d+)(?:\.(?P<cuda_patch>\d+))?"
    r"-cudnn(?P<cudnn>\d+)-runtime-"
    r"ubuntu(?P<ubuntu_major>\d+)\.(?P<ubuntu_minor>\d)+"
)


def get_image_tags(
    user: str,
    repository: str,
    max_pages: Optional[int] = None
) -> Iterable[str]:
    """Get available tags for a given docker image on dockerhub.

    This uses an undocumented API for dockerhub, so should not be relied upon.

    Parameters
    ----------
    user: str
        Username of the repository (first part of the image name).
    repository: str
        Repository name of the repository (second part of the image name).

    Returns
    -------
    Iterable[str]:
        Yields tags for the given image as strings.

    """
    url = f"https://hub.docker.com/v2/repositories/{user}/{repository}/tags"
    page_number = 1
    while True:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        info = response.json()
        for image in info["results"]:
            yield image["name"]
        if info["next"] is not None:
            if max_pages is None or page_number < max_pages:
                url = info["next"]
                page_number += 1
                continue
        break


def get_latest_nvidia_cuda_image():
    """Gets the latest nvidia/cuda image that meets our criteria.

    Criteria are that the image should be Ubuntu based, be a basic runtime
    image and include CUDNN.

    Note that Nvidia may change their tag format in the future and break this
    function, and dockerhub may change their API.

    """
    # Get a list of all available tags from dockerhub
    tags = get_image_tags(user='nvidia', repository='cuda', max_pages=10)

    # This regex both filters for the Ubuntu-based runtime image with CUDNN
    # and extracts the versions of the relevant pieces for sorted
    matches = []
    for t in tags:
        match = NVIDIA_TAG_RE.fullmatch(t)
        if match is not None:
            matches.append(match)

    def sort_fun(match):
        return (
            int(match.group('ubuntu_major')),
            int(match.group('ubuntu_minor')),
            int(match.group('cuda_major')),
            int(match.group('cuda_minor')),
            int(match.group('cuda_patch') or 0),
            int(match.group('cudnn')),
        )
    sorted_matches = sorted(matches, key=sort_fun)
    latest_tag = sorted_matches[-1].string

    return f'nvidia/cuda:{latest_tag}'


def find_docker_image_python_version(docker_image: str) -> Optional[str]:
    """Find Python version for a given Docker image name.

    This looks for an Ubuntu version tag in the image name and uses a hard
    coded lookup table to deduce the Python version.

    Parameters
    ----------
    docker_image: str
        Name of a docker image, with optional tag.

    Returns
    -------
    Optional[str]
       Python version string (e.g. '3.9') if it can be deduced, else None

    """
    exp = re.compile(r'ubuntu(\d\d\.\d\d)')
    match = exp.search(docker_image)
    if match is None:
        return None

    ubuntu_version = match.groups()[0]

    # Use https://packages.ubuntu.com to look this up
    lookup_table = {
        "18.04": "3.6",
        "20.04": "3.8",
        "22.04": "3.10",
    }

    try:
        python_version = lookup_table[ubuntu_version]
    except KeyError:
        msg = f"""\
            WARNING: Ubuntu version {ubuntu_version} not included in the
            Python version lookup table in source code of the
            cookiecutter-qtim package. The source code may need to be updated.
        """
        print(fill(dedent(msg)))
        return None
    return python_version

from typing import Dict, Sequence
import requests


PACKAGES_REQUIRED = [
    'click',
    'numpy',
    'pydicom',
    'python-gdcm',
    'importlib-resources',
    'pycrumbs',
]

PACKAGES_OPTIONAL = [
    'torch',
    'torchvision',
    'monai',
    'tensorflow',
    'SimpleITK',
    'opencv-python',
    'pandas',
    'scikit-image',
    'scikit-learn',
    'scipy',
]

PACKAGES_DEV_REQUIRED = [
    'Pygments',
    'black',
    'coverage',
    'darglint',
    'flake8',
    'flake8-docstrings',
    'importlib_resources',
    'ipython',
    'isort',
    'mypy',
    'nbstripout',
    'pep8-naming',
    'pre-commit',
    'pre-commit-hooks',
    'pytest',
    'typeguard',
]

PACKAGES_DEV_OPTIONAL = [
    'jupyterlab',
]

PYPI_URL = 'https://pypi.org/pypi/{package}/json'


def get_package_version(package: str) -> str:
    """Find latest versions of a package on PyPI.

    Uses the PyPI API to find the latest version tag of a package.

    Parameters
    ----------
    package: str
        Name of package as it appears listed on PyPI.

    Returns
    -------
    str:
        Version tag of most recent published version of the package.

    """
    response = requests.get(PYPI_URL.format(package=package))
    obj = response.json()
    if 'info' not in obj:
        raise RuntimeError(
            f"Error finding information for package: {package}."
        )
    return obj['info']['version']


def get_package_versions(packages: Sequence[str]) -> Dict[str, str]:
    """Find latest versions of listed packages on PyPI.

    Uses the PyPI API to find the latest version tag of listed packages.

    Parameters
    ----------
    packages: Sequence[str]
        List of packages as they appear listed on PyPI.

    Returns
    -------
    Dict[str, str]:
        Dictionary mapping package name to most recent version tag.

    """
    return {package: get_package_version(package) for package in packages}

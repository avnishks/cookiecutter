from argparse import ArgumentParser
from pathlib import Path
from pkg_resources import resource_filename
import re
from textwrap import dedent, fill

from cookiecutter.main import cookiecutter
from git import Repo
from pre_commit.commands.install_uninstall import install
from pre_commit.constants import HOOK_TYPES
from pre_commit.store import Store

from cookiecutter_qtim.dependencies import (
    get_package_version,
    get_package_versions,
    PACKAGES_REQUIRED,
    PACKAGES_DEV_REQUIRED,
    PACKAGES_OPTIONAL,
    PACKAGES_DEV_OPTIONAL,
)
from cookiecutter_qtim.docker import (
    find_docker_image_python_version,
    get_latest_nvidia_cuda_image
)


GIT_HOST = "github.com"
DOCKER_HOST = "DOCKER_HOST_PLACEHOLDER"
GIT_URL = "https://github.com"


START_MESSAGE = f"""\
Welcome to the QTIM ML Project Creation Tool.

Before continuing, make sure that you have completed the following
tasks:
1. Create an empty repository for the project on
 {GIT_URL} and make a note of the URL for the new
 repository.

"""

COMPLETE_MESSAGE = """\
Here are the next steps:

1. Change to the project directory as your working directory.

2. Create a virtualenv for the project using whatever tool you use to manage
   virtualenvs (pyenv with pyenv-virtualenv is recommended). This must match
   the Python version selected above ({selected_python_version}.x).

3. Activate the virtualenv that you created.

4. Run
       poetry lock
       git add poetry.lock
       poetry install

   to resolve dependencies and install them project along with all dependencies
   and tooling in the virtualenv.

5. The project skeleton files have already been added to your git repository,
   but they still need to be committed and pushed to the remote.

"""


FALLBACK_DOCKER_IMAGE = 'nvidia/cuda:11.7.1-cudnn8-runtime-ubuntu22.04'


def prompt_for_package(package: str) -> bool:
    """Prompt the user about whether they want to include a package.

    Parameters
    ----------
    package: str
        Name of the package.

    Returns
    -------
    bool:
        Whether the user requested that the package be included.

    """
    while True:
        in_str = input(f"Include {package}? y/[n]: ")
        if in_str.lower() == "y":
            return True
        elif in_str.lower() in ["", "n"]:
            return False


def format_text(msg: str) -> str:
    """Format string to print to terminal."""
    return fill(dedent(msg))


def get_mac_mountpoint(path: str):
    """Get the directory on a Mac where a Martinos path will be mounted."""
    return (
        path
        .replace("/autofs/cluster", "/Volumes")
        .replace("/autofs/vast", "/Volumes")
    )


def main():
    # Automatically find the location of the template directory, wherever it
    # was installed on the system
    template_dir = resource_filename(
        "cookiecutter_qtim",
        "cookiecutters/cookiecutter-ml-proj"
    )

    parser = ArgumentParser("Create a new project directory.")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path('.'),
        help="Parent of output project directory."
    )
    args = parser.parse_args()

    print(START_MESSAGE)
    print(
        "Enter a project name consisting of lower case letters, numbers "
        "and hyphens."
    )
    project_name_exp = re.compile(r"[a-z][a-z0-9\-]*[a-z0-9]")
    while True:
        project_name = input("Project Name: ")
        if project_name_exp.fullmatch(project_name) is not None:
            break
        else:
            print("Invalid name.")
    project_slug = project_name.replace('-', '_')
    print(
        f"The name of your project is {project_name} and the name of the "
        f"Python package is {project_slug}."
    )

    print()
    msg = f"""\
        Enter the full path of the directory on Martinos machines that contains
        the project dataset. For most qtim projects this should be within
        /autofs/cluster/qtim/datasets, e.g.
        /autofs/cluster/qtim/datasets/public/BraTS2020
    """
    print(format_text(msg))
    path_exp = re.compile(r"[a-zA-Z0-9_.\-/]+")
    while True:
        project_dataset_dir = input(f"Dataset directory: ")
        if path_exp.fullmatch(project_dataset_dir):
            if Path(project_dataset_dir).is_absolute():
                break
            print("Path must be an absolute path")
            continue
        print("Invalid characters found in path.")
    project_dataset_dir = str(Path(project_dataset_dir))
    mac_project_dataset_dir = get_mac_mountpoint(project_dataset_dir)

    print()
    msg = f"""\
        Enter the full path of the directory on Martinos machines that contains
        the other project files. For most qtim projects this should be within
        /autofs/cluster/qtim/projects, e.g.
        /autofs/cluster/qtim/projects/brainmets
    """
    print(format_text(msg))
    path_exp = re.compile(r"[a-zA-Z0-9_.\-/]+")
    while True:
        project_dir = input(f"Project directory: ")
        if path_exp.fullmatch(project_dir):
            if Path(project_dir).is_absolute():
                break
            print("Path must be an absolute path")
            continue
        print("Invalid characters found in path.")
    project_dir = str(Path(project_dir))
    mac_project_dir = get_mac_mountpoint(project_dir)

    container_path = str(Path(project_dir) / "containers")

    msg = f"""\
        You should now create the repository on {GIT_URL} to host the
        source code. Enter the full path to the repository you created. E.g.
        "{GIT_URL}/QTIM-Lab/project".
    """
    print()
    print(format_text(msg))
    git_url_exp = re.compile(r"[a-zA-Z0-9_.\-/]+")
    while True:
        github_path = input(f"Repository URL: {GIT_URL}/")
        if git_url_exp.fullmatch(github_path):
            git_url = f"{GIT_URL}/{github_path}"
            break
        else:
            print("Invalid URL.")
    if git_url.endswith('.git'):
        git_url = git_url[:-4]

    container_tag = project_name

    # Query the PyPI API to get most recent versions of listed packages
    msg = """\
        You will now be prompted for a list of common packages that you may
        want to use in the project. You can always change the selection
        afterwards by editing the pyproject.toml file.
    """
    print()
    print(format_text(msg))
    selected_packages = [p for p in PACKAGES_OPTIONAL if prompt_for_package(p)]
    selected_packages_dev = [
        p for p in PACKAGES_DEV_OPTIONAL if prompt_for_package(p)
    ]

    msg = """\
        You will now choose a base image to use for your project's docker
        image. Your selected image should ideally contain all the necessary
        CUDA libraries, but no Python packages pre-installed as this
        complicates the management of dependencies within the project.  It is
        recommended to use one from this page:
            https://hub.docker.com/r/nvidia/cuda/tags.
    """  # noqa: E501
    print()
    print(format_text(msg))
    try:
        recommended_docker_image = get_latest_nvidia_cuda_image()
    except Exception as e:
        print(e)
        msg = f"""\
            Failed to find a suitable image on Dockerhub automatically,
            a suitable fallback option is '{FALLBACK_DOCKER_IMAGE}'.
        """
        print()
        print(format_text(msg))
        recommended_docker_image = FALLBACK_DOCKER_IMAGE
    else:
        msg = f"""\
            Found the following latest container version on Dockerhub
            automatically: '{recommended_docker_image}'.
        """
        print()
        print(format_text(msg))

    docker_image_exp = re.compile(r'[a-zA-Z0-9-_:\./]+')
    while True:
        selected_docker_image = input(
            f"Select a Docker base image [{recommended_docker_image}]: "
        )
        if selected_docker_image == '':
            selected_docker_image = recommended_docker_image
            break
        if docker_image_exp.fullmatch(selected_docker_image) is None:
            msg = f"""
                '{selected_docker_image}' is not a valid docker image name.
            """
            print(format_text(msg))
            continue
        if (
            ':' in selected_docker_image and
            ':latest' not in selected_docker_image
        ):
            break
        else:
            msg = """"
                The selected docker image must include a full tag (not just
                ':latest').
            """
            print(format_text(msg))

    # Try to deduce the python version from the docker image
    msg = """\
        You will now choose a version of Python to use for your project.  It is
        important that this matches the version of Python in the project docker
        image.
    """
    print()
    print(format_text(msg))
    recommended_python_version = find_docker_image_python_version(
        selected_docker_image
    )
    if recommended_python_version is not None:
        msg = f"""\
            Automatically deduced Python version {recommended_python_version}
            using Ubuntu version in base container. It is strongly recommended
            to use this version.
        """
    else:
        msg = "Could not automatically deduce Python version."
    print()
    print(format_text(msg))
    python_version_exp = re.compile(r'3\.[1-9][0-9]*')
    while True:
        if recommended_python_version is not None:
            selected_python_version = input(
                f"Select a Python version [{recommended_python_version}]: "
            )
            if selected_python_version == '':
                selected_python_version = recommended_python_version
        else:
            selected_python_version = input(
                "Select a Python version: "
            )
        if python_version_exp.fullmatch(selected_python_version) is not None:
            break
        else:
            print(
                f"{selected_python_version} is not a valid Python 3 version."
            )

    extra_context = {
        "__project_name": project_name,
        "__project_slug": project_slug,
        "__repository_url": git_url,
        "__package_versions": get_package_versions(
            PACKAGES_REQUIRED + selected_packages
        ),
        "__package_versions_dev": get_package_versions(
            PACKAGES_DEV_REQUIRED + selected_packages_dev
        ),
        "__pip_version": get_package_version("pip"),
        "__setuptools_version": get_package_version("setuptools"),
        "__docker_base_image": selected_docker_image,
        "__python_version": selected_python_version,
        "__github_project_path": github_path,
        "__project_path": project_dir,
        "__data_path": project_dataset_dir,
        "__container_path": container_path,
        "__mac_project_path": mac_project_dir,
        "__mac_data_path": mac_project_dataset_dir,
        "__project_slug": project_slug,
        "__container_tag": container_tag,
    }

    print()
    print(
        "You will now be prompted for some basic information about the "
        "project."
    )
    repo_dir = cookiecutter(
        template_dir,
        output_dir=args.output_dir,
        extra_context=extra_context
    )

    print()
    print(
        "Your project repository was successfully created at "
        f"{repo_dir}!"
    )

    # Initialize git in repository and add all files
    repo = Repo.init(repo_dir, initial_branch="main")
    repo.create_remote("origin", git_url)
    repo.git.add(all=True)

    print(f"Git repository initialized in {repo_dir}.")
    print(f"Remote 'origin' added at {git_url}.")
    print("All files added to git repository, but not committed.")

    print()
    print("Installing pre-commit hooks...")
    install(
        config_file=Path(repo_dir) / ".pre-commit-config.yaml",
        store=Store(),
        hook_types=HOOK_TYPES,
        git_dir=Path(repo_dir) / '.git',
    )

    print()
    print(
        COMPLETE_MESSAGE.format(
            selected_python_version=selected_python_version
        )
    )

# `cookiecutter-qtim`

This package implements a command line tool for creating Python project
repositories for QTIM ML projects. The resulting repository has various
capabilities to help orgnaize and standardize the lab's projects.

## Installation

This is a Python package that supplies a command line tool when installed
inside your current Python environment or virtual environment.  To install this
package in your current environment, either clone the source code and run `pip
install .` from the root of the reposiory, or run this to install directly
from git:

```bash
pip install git+https://github.com/cookiecutter-qtim/cookiecutter-qtim
```

## Basic Usage

The basic usage is simply to run the `cookiecutter-qtim` command from the
command line. This will start the process to create a project repository in a
sub-directory of your current directory. To place the resulting output in
another directory, use the `-o` option, e.g.:

```bash
cookiecutter-qtim -o ~/repos/
```

Note that `-o` controls the directory within which the project sub-directory
will be created, not the path of the directory itself, which will be determined
by the name you give the project during the setup
(e.g. `~/repos/project-name`).

After running the command, you will be presented with instructions in your
command line and will be asked to enter further information that will be
used to construct your basic project files.

## The Project Directory

After completing the process, you will have a project codebase with the
following capabilities and characteristics:

#### Installable Python Package

The resulting project repository is a Python package that can be installed
within a Python environment. This is achieved with the modern
[`pyproject.toml` format](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).

As a results, you can install the project Python package using pip either
by specifying the path to the root of the cloned directory, e.g. from the root
of the cloned directory:

```bash
pip install .
```

or directly from GitHub:

```bash
pip install git+https://github.com/group/project
```

After installation, you can import the code in the Python package from anywhere
without having to manipulate your `PYTHONPATH` (which is generally confusing
and not repeatable).

When you are working on the project, it is recommended to install the package
in *editable* mode with the `-e` flag. This means that the installed version of
the code is a symlink to the original source code (rather than a copy) so the
installed version is updated as you edit the files. Furthermore, to install the
list of development time dependencies (used for the automated tests described
below) by appending `[dev]` to the installation target. Therefore to install a
local clone for development, run this from the repository root:

```bash
pip install -e ".[dev]"
```

The dependencies of the project are also controlled by the `pyproject.toml`
file. If you need to use a new library in your project, you must add it to
`pyproject.toml` in the project dependencies section (or the
optional-dependencies section if it is needed for development only). When
created, your project dependencies will include some common packages that you
selected during the creation process.

It is recommended that when using the repository, you install it within a
project-specific virtual environment, or within the docker image (see below).
It is also strongly recommended that the version of python used for the local
repository matches that used within your project docker image, or you will
likely encounter many strange issues.

#### Repository Structure

The following directories are created within the new repository:

- Python package. The python package itself, i.e. the directory containing
  the python source code, will be given the same same as the project. Note
  that following conventions, the project name should use `-` to separate words
  but the python package will change this to `_`. For example a project called
  `project-name` will have a package called `project_name`.
- `docs/` - This is where you should maintain instructions for yourself and
  other team members or future team members on how to use the code in this
  project repository. Markdown format is suggested to give easy to read
  documentation when viewed on github itself.
- `notebooks/` - This is where you should store any jupyter notebooks that you
  want to version control.
- `tests/` - This is used for storing regression tests to run with `pytest`.

#### Python Package Structure

The project package is initialized with a suggested standardized structure,
with separate sub-packages (sub-directories) for `preprocess`, `train`,
`inference`, `analysis`, `visualization`, and `commands`. You may change this
structure if you feel that it is not appropriate for your project.

There are also three special files in the package:

- `locations.py` - This should be used to store all relevant file path
  locations for project files in one standardized place.
- `enums.py` - This is a place to store enumerations related to the project.
  These are used for variables that may take one of a fixed list of values.
  Good use cases for enums include classification class names, and dataset
  partitions.
- `constants.py` - This is a place to store constants for the project that are
  not file locations or enums.

#### Command Line Interface

Each "critical" task within a project should be implemented within the python
codebase (not a notebook) with a command line interface (CLI) that allows you
to control the behavior (such as input and output directories). Critical tasks
are any tasks whose output is required to complete the project, or that is
input to another critical task. This includes tasks such as training,
preprocessing, post-processing, and inference to produce results, but may not
include tasks such as analysis or visualization.

The initialized repository is configured with a command line interface that
is installed along with the project's Python package. If your project name
is `proj-name` then you will be able to run:

```bash
proj-name <sub-command> <arguments>
```

from the command line from any directory to execute project tasks (e.g.
`proj-name train`). Sub-commands are any module (i.e. Python file_ of the
`commands` sub-package (i.e. in the `commands` directory) that defines a
function whose name matches the module and is decorated with the
`@click.command()` decorator. This makes it easy to add new sub-commands to the
project for each task. The project is initialized with an example `train`
command to demonstrate how this works.

This setup makes it very straightforward for other scientists to understand
what tasks they need to run to be able to work with the project, and how they
should run them. They can run

```bash
proj-name --help
```

for a list of sub-commands and

```bash
proj-name <sub-command> --help
```

to find options and arguments for a given sub-command.

For tutorials on writing command line interfaces using the recommended `click`
package, see its [documentation](https://palletsprojects.com/p/click/).

#### Example Train Command

The initialized repository contains an example train command that demonstrates
a few recommended/required patterns that you should follow:

- How to set up a command for the CLI using `click`.
- How to use the
  [`pycrumbs`](https://github.com/CPBridge/pycrumbs) package
  and the `@tracked()` decorator to automatically create job records for
  tasks.
- How to read training parameters from a configuration file stored within the
  repository itself.

You can find the command in the `commands/train.py` file of the Python
package. You can run it using

```bash
<project-name> train example <name_for_model>
```


#### Tests with Pytest

[`pytest`](https://docs.pytest.org/) is a package used for writing and running
regression tests for Python. Regression tests are pieces of code that are run
automatically when changes are made to the code that check that the code
still runs as expected. They are used to prevent you from introducing errors
when editing your code.

Tests can be time consuming to write in the short term but save considerable
time in the long term. Therefore it is up to you to determine what tests to
write for your project codebase. Any tests you write in the `tests/` directory
in files beginning named `test_*.py` will be run automatically whenever you use
the `pytest` command from the project root, or run the pre-commit hooks (see
below).

#### Pre-Commit Checks

[Pre-commit](https://pre-commit.com) is a tool for automating tests and fixes
on your code before every commit is made. The new project repository comes
pre-configured to run a number of different processes outlined below when
commits are made:

- Black: This tool automatically fixes many style errors to bring the code in
  line with the [PEP8 code guidelines](https://pep8.org/) to make it neat,
  readable and in-line with Python best practices.
- Flake8: The `flake8` tool performs various checks on Python code. It will
  spot obvious errors such as undefined variables or missing imports. It will
  also spot PEP8 style errors (that could not be fixed by `black`
  automatically). Furthermore, it will enforce correct use of docstrings using
  the numpy convention using the `flake8-docstrings` plugin. It is rarely
  recommended, but in some situations you may need to [ignore specific
  errors](https://flake8.pycqa.org/en/3.1.1/user/ignoring-errors.html) from
  `flake8`. You can configure its behavior from the project's `setup.cfg` file.
- Pytest: this runs all tests in the `tests/` directory using `pytest` as
  described above.
- General code tidiness: there are several further small hooks that perform
  tasks such as removing trailing whitespace from files, normalizing line
  endings, removing cell contents from Jupyter notebooks, and checking JSON,
  TOML and YAML files have valid syntax.

When you first create the repository, pre-commit will have been installed and
enabled for you. However, if you later move to a new machine you will have to
manually enable it by running this from the project root:

```bash
# First install the project with development dependencies
# Make sure you do this in the correct virtualenv
pip install -e ".[dev]"

# Now enable pre-commit
pre-commit init
```

When pre-commit is enabled, it will run automatically on all changed files
before the commit is made. If any of the tests fail or result in changes to the
files, the commit you were trying to make will not complete. You will then need
to `git add` the resulting changes again and attempt the commit again. This
should help ensure that files are kept organized throughout a project.

You can run the checks on all files without making a commit using:

```bash
pre-commit run --all-files
```

Refer to the pre-commit [documentation](https://pre-commit.com) for more
information on using configuring and running pre-commit hooks including
skipping tests if necessary.

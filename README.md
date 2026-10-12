# py-wwpdb_utils_wf
OneDep WF status DB access utilities

### Installation

Download the library source software from the project repository. The test suite needs the mock data
submodule, so clone with `--recurse-submodules`:

```bash
git clone --recurse-submodules https://github.com/wwpdb/py-wwpdb_utils_wf.git
cd py-wwpdb_utils_wf
```

If you already cloned without it, fetch the submodule with `git submodule update --init`.

The package is built with [hatchling](https://hatch.pypa.io/latest/) from `pyproject.toml`; there is no
`setup.py`. Install it with pip:

```bash
pip install .
```

### Testing

Run the test suite and checks (flake8, pylint, mypy, black, unit tests and coverage) with
[tox](https://tox.wiki/):

```bash
tox
```

or a single environment, for example the unit tests only:

```bash
tox -e py310
```

If you use [hatch](https://hatch.pypa.io/latest/), `hatch test` runs tox, `hatch run check` runs ruff and mypy,
and `hatch run format` applies ruff formatting and fixes.

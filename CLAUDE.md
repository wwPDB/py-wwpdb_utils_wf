# CLAUDE.md

This file guides Claude Code (claude.ai/code) when it works in this repository.

@AGENTS.md

## Overview

`wwpdb.utils.wf` is part of the wwPDB OneDep system. It holds the workflow (WF) side of the deposition and annotation pipeline:

- **Action dispatch**: named actions are defined in an XML registry and run by `ProcessRunner`. Each action maps to a method in a plugin class.
- **Plugins**: thin wrappers that call out to other OneDep packages (`wwpdb.utils.dp`, `wwpdb.apps.*`, `wwpdb.utils.nmr`, and others).
- **Status DB access**: MySQL access to the WF status database through the `MySQLdb` module from `mysqlclient`.

Most of the code is older and untyped: Python 2-era style, `%` formatting, and logging to `sys.stderr` through a `log=` file handle. Type annotations are being added one package at a time. The whole package (`dbapi/`, `plugins/`, `process/`, `schema/` and the top-level modules) is fully annotated, and a strict mypy override in `pyproject.toml` enforces this. Plugin action methods are `xxxOp(self, **kwArgs: Unpack[PluginKwargs]) -> bool`, where `PluginKwargs` (a TypedDict in `plugins/UtilsBase.py`) declares the four keyword arguments `ProcessRunner.run()` passes: `inputObjectD`, `outputObjectD`, `userParameterD` and `internalParameterD`. `UtilsBase._getArgs()` takes a `PluginKwargs` and returns the `PluginArgs` tuple, and plugin `log` arguments are `TextIO`, which is what `RcsbDpUtility` and the other typed libraries expect. The action registry uses the TypedDicts in `process/ActionRegistryTypes.py`. Table definitions use the `SchemaTableDef` TypedDict (from `typing_extensions`) defined in `schema/SchemaMapTypes.py`. `EmptySchemaTableDef` and `MaybeSchemaTableDef` in the same module cover the `{}` that `WfDbApi` returns when no table matches. Import these instead of redefining them. Where accurate types expose a known bug, the line carries a narrow `# type: ignore[code]` with a comment pointing to ERRORS.md. Leave those bugs in place unless you are fixing them on purpose.

## Commands

```bash
# Full tox suite: pep8 (flake8), pylint, mypy, black, unit tests, coverage
tox
tox -e py310                 # unit tests only
tox -e mypy-py310            # mypy -p wwpdb -p tests
tox -e lint_pylint-py310
tox -e format_black-py310    # black --check --line-length 180

# Run one test file or test case directly (from the repo root)
python -m unittest tests/ProcessRunnerTests.py
python -m unittest tests.WfTrackingTests.WfTrackingTests.testName

# Hatch helpers (pyproject.toml)
hatch run format             # ruff format plus ruff check --fix-only
hatch run check              # ruff check plus mypy
hatch run check-ruff
```

CI runs on Azure Pipelines (`azure-pipelines.yml`) with Python 3.11 on Linux. It runs the tox environments `format_pep8`, `lint_pylint`, `test_coverage`, `mypy` and `py311`. The coverage threshold is 15%.

Line length is 180 for ruff and black, and 189 for flake8.

## Testing notes

- **Mock data is required.** `wwpdb/mock-data` is a git submodule (`py-onedep_mock_data`). Clone with `--recurse-submodules`, or run `git submodule update --init`.
- `tests/commonsetup.py` must be imported **before** anything that touches `ConfigInfo`. It copies the mock `site-config`, `actiondata` and `archive/D_000001` into `tests/test-output/<pyver>/` and sets up the site environment through `wwpdb.utils.testing`. Each test module begins with the same `if __package__ is None ...` import block; copy that pattern in new tests.
- tox only discovers files that match `*Tests.py`. Name new test files to match.
- When running tests outside tox, put the tox venv first on `PATH` (`export PATH=$PWD/.tox/py310/bin:$PATH`). `SiteConfigSetup` shells out to `python`; if that resolves to a different interpreter, the site config ends up empty and the tests fail with `None` paths.
- Tests that need a live database (`WfDbApiDbTests.py`, `WfTrackingTests.py`) are gated with `@unittest.skipUnless(Features().haveMySqlTestServer(), ...)`. Everything else mocks `MySQLdb`, `RcsbDpUtility` and the other collaborators. Patch them as module-level names in the module under test, for example `patch("wwpdb.utils.wf.plugins.FileUtils.RcsbDpUtility")`.
- Optional packages (`wwpdb.apps.*`, `wwpdb.utils.nmr.*`) are imported at module load inside try/suppress, so they are missing in the test environment. Patch them with `patch("<module>.<Name>", create=True)`.
- Test files are fully type-annotated. The `tests.*` mypy override in `pyproject.toml` enforces this.
- Library bugs found by tests are marked `@unittest.expectedFailure`, with a comment describing the bug. When a library bug is fixed, remove the decorator.

## Architecture

```
wwpdb/utils/wf/
  WfDataObject.py        WfDataObject = DataSelector + DataValueContainer + DataFileReference (wwpdb.io)
  DataSelector.py        category/attribute/condition selection (selector type)
  DataValueContainer.py  typed value or container (value type, container type)
  process/
    ActionRegistryIo.py  parses the action XML registry into a dict
    ActionRegistry.py    query API over the registry; path comes from ConfigInfo "SITE_REGISTRY_FILE_PATH"
    ProcessRunner.py     setAction -> setInput/setOutput -> setParameterDict -> preCheck -> run
  plugins/               action implementations (subclasses of UtilsBase)
  dbapi/                 MySQL status/WF database access
  schema/                WfSchemaMap (logical name to table/column mapping), SQL DDL, ERD docs
```

### Action execution flow

1. `ProcessRunner.setAction(actionId)` checks that the action exists in the registry and loads its default user parameters.
2. `setInput(name, WfDataObject)` and `setOutput(...)` bind data objects by name. The names must match the `<wfDataObject name=...>` entries in the registry.
3. `preCheck()` checks the input and output counts. It also checks each object's reference type, container type, value type, selector type, content type and file format against the registry.
4. `run()` imports the module named in `<moduleName>`. It then creates the class whose name matches the last dotted component, passing `verbose=` and `log=`. Finally it calls `<methodName>` with the keyword arguments `inputObjectD`, `outputObjectD`, `userParameterD` and `internalParameterD`.

### Plugin conventions (`plugins/`)

- Each plugin subclasses `UtilsBase` and has the constructor `(verbose=False, log=sys.stderr)`.
- Action methods are named `xxxOp(self, **kwArgs)`. They unpack their arguments with `self._getArgs(kwArgs)` and **return True or False**. Each method wraps its whole body in `try/except Exception` and prints the traceback to `self._lfh` when verbose. Do not let exceptions escape.
- Inputs are usually file references. Use `inpObjD["src"].getFilePathReference()` and `.getDepositionDataSetId()` from `DataFileReference`.
- Many plugins import heavy optional OneDep packages (`wwpdb.apps.*`, `wwpdb.utils.nmr`) that are not declared dependencies. mypy ignores missing imports for those modules (see `[[tool.mypy.overrides]]`).

### Database layer (`dbapi/`)

- `DbConnection` creates the MySQL connection. Any argument left as `None` falls back to the `MYSQL_DB_NAME`, `MYSQL_DB_USER`, `MYSQL_DB_PW`, `MYSQL_DB_HOST`, `MYSQL_DB_PORT` and `MYSQL_DB_SOCKET` environment variables.
- `DbCommand` and `DbApiUtil` are the low-level query builders and executors.
- `WfDbApi` (the largest module) is the API for the workflow engine and the WF manager. It uses `WfSchemaMap` to translate logical table and attribute names into SQL.
- `WfTracking` records instance status. `dbAPI` is a thin wrapper over `WfDbApi`.
- `StatusDbApi` connects through `ConfigInfo` site settings (`SITE_DB_*`). `LocalDbApi` reads from a local database.
- `WFEtime` handles WF timestamps, measured as offsets from 2000-01-01.

## Conventions and gotchas

- The version lives in `wwpdb/utils/wf/__init__.py` as `__version__` and is read by hatch. Releases are commits titled `vX.Y.Z`.
- The ruff config allows camelCase names (`N802`, `N803`, `N806` and others are ignored) and `%` formatting. Keep the camelCase style used in the surrounding code.
- Existing broad excepts carry the marker `# noqa: F841,BLE001`. Keep it when you edit those blocks.
- `requires-python` in `pyproject.toml` says `>=3.7`, but ruff targets py38 and AGENTS.md requires Python 3.8+ compatibility. When adding annotations, use `typing.Optional`, `List` and `Dict` rather than `X | None` or `list[...]`, unless the module already has `from __future__ import annotations`.
- The wheel and sdist exclude `wwpdb/mock-data`, `*.doc` and `schema/da_table_schema.sql`.
- Pushes to `develop` and `master` trigger the GitHub auto-deploy workflow (`.github/workflows/trigger_autodeploy.yml`).

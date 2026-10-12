# Known errors and concerns

These issues turned up in October 2026 while adding unit tests to `tests/` and type annotations to the whole `wwpdb.utils.wf` package. The library code is unchanged apart from those annotations and a few bug fixes. Fixed items are removed from this file, and the open bugs are renumbered to stay consecutive.

Each confirmed bug has a test that asserts the correct behaviour. Those tests are marked `@unittest.expectedFailure`. When you fix a bug, remove the decorator from its test. If the test then passes, the fix is confirmed.

Line numbers refer to commit `e66c19b`, except #3, #4 and #10–#14, which use line numbers from the current, annotated code.

## Confirmed bugs

### Core data and process

| # | Location | Problem | Test |
|---|---|---|---|
| 1 | `DataValueContainer.py:121` | `setValueTypeName()` maps `"float"` and `"double"` to `int`. Float values never pass `isValueValid()`. | `DataContainerTests.testFloatValueIsValid` |
| 2 | `schema/WfSchemaMap.py:198` | `CONTACT_AUTHOR` has `TABLE_NAME` set to `"release_request"`. It should be `"contact_author"`, matching `da_table_schema.sql`. This looks like a copy-paste from the `RELEASE_REQUEST` entry at line 176. | `WfSchemaMapTests.testContactAuthorTableName` |

### Database layer (`dbapi/`)

| # | Location | Problem | Test |
|---|---|---|---|
| 3 | `DbConnection.py:78-84, 117, 126` | A missing port is passed to `MySQLdb.connect()` as `port=None`, and a non-numeric port such as `"abc"` is passed through unchanged. mysqlclient raises a plain `TypeError` for both (checked against the installed driver). That is not a `MySQLdb.Error`, so it escapes `connect()` instead of reaching the clean `sys.exit(1)`. The port should be left out, or rejected with a clear message. When fixing this, also update `DbConnectionTests.testNonNumericPortIsKept` and `testDefaultHostIsLocalhostAndMissingEnvGivesNone`, which assert the current behaviour. | `DbConnectionTests.testMissingPortIsNotPassedToDriver`, `testNonNumericPortIsNotPassedToDriver` |
| 4 | `DbConnection.py:114-118, 123-128` | `connect()` formats `db`, `user`, `passwd` and `host` with `"%s" % value`. Any value that is unset (not passed and no `MYSQL_DB_*` variable) reaches the driver as the literal string `"None"`, for example password `"None"` or database `"None"`. Unset values should be left out so the driver's defaults apply. `testDefaultHostIsLocalhostAndMissingEnvGivesNone` asserts the current behaviour and must be updated with the fix. | `DbConnectionTests.testUnsetCredentialsAreNotStringNone` |
| 5 | `DbApiUtil.py:139, 157` | The private select returns `()` on error, never `None`. The `if ret is None:` reconnect-and-retry loop in `runSelectSQL` therefore never runs, and select errors are silently swallowed. | `DbApiUtilTests.testRunSelectSQLRetriesAfterLostConnection` |
| 6 | `DbApiUtil.py:205-209` | `runUpdate(table, data=...)` without `where` takes the insert branch, which iterates `where.items()` on `None` and crashes. The insert branch probably meant to use `data`. | `DbApiUtilTests.testRunUpdateDataOnlyInserts` |
| 7 | `WfDbApi.py:873` | `doQuery()` level 1 tests `if otherOpt is None:` where it should test `is not None`. A plain level-1 query with no `otherOpt` always ends in `sys.exit(1)`. | `WfDbApiMockTests.testDoQueryLevel1WithoutOtherOption` |
| 8 | `WfTracking.py:73` | `if ok < 1:` raises `TypeError` when `runUpdateSQL` returns `None` after a database error. It should return False. | `WfTrackingMockTests.testUpdateDbErrorFails` |

### Plugins

| # | Location | Problem | Test |
|---|---|---|---|
| 9 | `plugins/PdbxUtils.py:150, 418` | `selectOp` and `statusOp` call `ISTable.Search(values, names)` with the old two-argument signature. The current `mmcif` binding requires `(res, targets, colNames, fromRowIndex, searchDir, searchType[, indexName])` and raises `TypeError`. So `selectOp` fails whenever conditions are given, and `statusOp` fails on any file that contains `database_2`. | `PdbxUtilsTests.testSelectMatch`, `testSelectMultipleConditions`, `testStatusDictionary` |

### Found while adding type annotations to `dbapi/`

No test covers these yet. Each one is marked in the source with a narrow `# type: ignore[...]` and a comment. Line numbers refer to the annotated code.

| # | Location | Problem |
|---|---|---|
| 10 | `dbapi/DbCommand.py:452` | `selectCrossTables()` defaults `constraintDef` to `None`, then passes it to `makeConstraintCross()`, which calls `.items()` on it and crashes. Every caller has to supply a value. |
| 11 | `dbapi/StatusDbApi.py:95` | `getEntryIdList()` loops over the result of `selectData()`, which returns `None` after a database error. The loop then raises `TypeError` instead of returning an empty list. |
| 12 | `dbapi/WfTracking.py:60` | `setInstanceStatus()` defaults `depId`, `instId` and `classId` to `None` but concatenates them into SQL with `+`. Leaving any of them as `None` raises a `TypeError` that nothing catches. |
| 13 | `dbapi/WfDbApi.py:1103-1106` | `getNextWfInstId()` calls `len()` on, and then indexes, the result of `getLastObjectOfState()`, which returns `None` after a database error. That raises `TypeError`. |

### Found while adding type annotations to `process/`

| # | Location | Problem | Test |
|---|---|---|---|
| 14 | `process/ProcessRunner.py` `preCheck()` | `preCheck()` checks that the number of inputs and outputs matches the registry, but never that their names do. If a type constraint is declared, an object set under a name the registry doesn't expect makes `preCheck()` raise an uncaught `KeyError` instead of returning False. If no constraint is declared, `preCheck()` returns True, and `run()` then passes the plugin an `inputObjectD`/`outputObjectD` without the name it looks up. Both cases were confirmed by running them. | `ProcessRunnerUnitTests.testPreCheckWrongInputNameReturnsFalse`, `testPreCheckWrongInputNameWithoutConstraints` |

## Concerns (not marked as test failures)

### Possible library bugs worth checking

- **`schema/WfSchemaMap.py:282-284`**: some `_usefulItems` entries, such as `RELATIONSHIP`, `ASSOCIATED_IDS` and `ASSESSION_CODE`, are not attributes of any table. `ASSESSION_CODE` also looks like a misspelling of "accession". `WfDbApi` uses `_usefulItems[7]` (`RELATIONSHIP`) together with `DATABASE_RELATED`, which may be a hidden bug.
- **`plugins/PdbxUtils.py` `statusOp`**: it returns the `pdbx_database_status` values as utf-8 `bytes` rather than `str`, which looks like leftover Python 2 behaviour. The tests currently accept `bytes`.
- **`plugins/ValidationUtils.py` `validationReportAllOpV3`**: it relies on its `TemporaryDirectory` being cleaned up implicitly, which triggers a `ResourceWarning`. A `with` block would make the cleanup explicit.
- **Dead code**: in `ChemCompUtils`, `PrdSearchUtils` and `SeqdbUtils`, the private `__cleanUp` flag is hard-coded to `False`, so `dp.cleanup()` never runs and temporary working directories may be left behind. In the `ChemCompUtils` NL ops, `ccLinkFilePath` is set to `None` right before it is checked with `is not None`.
- **`DbApiUtil`**: it calls `MySQLdb.cursors.DictCursor`, but never imports `MySQLdb.cursors` itself. It only works because a real `MySQLdb.connect()` imports that module as a side effect. `DbApiUtilTests` and `StatusDbApiTests` import `MySQLdb.cursors` explicitly so they work with the connection mocked.
- **`WfDbApi.referenceExist`** (`WfDbApi.py:1157`) passes dicts as the `orderList` and `selectList` arguments of `DbCommand.selectRows()`, which are typed `List[str]`. It works only because `selectRows` takes their length and iterates over them, which gives the keys.
- **Loose return types**: `WfDbApi.getObject()` and `getReference()` are typed `Any`, because `selectRows()` returns a single dict for one row but a list of dicts for several. Callers check the type at runtime. A consistent return shape would let them be typed precisely.
- **Errors swallowed as `False`**: in `dbAPI` (`:157`, `:218-219`, `:250`) and `WfDbApi.py:464`, passing `None` or hitting a database error leads to an `AttributeError` or `TypeError` that a broad `except` turns into `False` or `None`. The tests depend on that behaviour, but it hides the real error.
- **`DbConnection` writes the password to the log**: the connect-failure message (`DbConnection.py:134-145`) includes `pw %s`, so a failed connection puts the database password in whatever log file the caller passed in. It should be masked or left out.
- **`DbConnection.commit()` / `rollback()` without a connection silently do nothing**: before `connect()`, or after `close()`, both methods now return without doing anything. A commit made at the wrong time is lost without any warning. Nothing in the repository calls these two methods (callers commit on the raw connection), but a log message or an exception would make misuse visible.
- **`DbConnection.close()` ignores which connection it is given**: `close(dbcon)` clears the stored connection even when `dbcon` is a different connection. This is harmless with the current callers, which close the old connection before opening a new one.
- **`DbConnection.connect()` error handler assumes two arguments**: it logs `e.args[0]` and `e.args[1]` (`DbConnection.py:133`). A `MySQLdb.Error` built with a single argument, for example `MySQLdb.InterfaceError("message")`, makes the handler itself raise `IndexError` before it reaches `sys.exit(1)`. Errors from a failed connection in the driver always carry an error number and a message, so this is unlikely to happen in practice.
- **`DbConnection(dbServer=None)` exits**: `None` is treated as an unsupported server and the process exits (`DbConnection.py:100-102`). `DbApiUtil` defaults its own `dbServer` to `None` and passes it straight through, so `DbApiUtil()` built with its defaults always exits. `StatusDbApi` and `WfDbApi` avoid this only because the site config supplies `SITE_DB_SERVER`. Either `DbConnection` should treat `None` as `"mysql"`, or `DbApiUtil` should default to `"mysql"`.
- **`MYSQL_DB_HOST` is rarely used**: `dbHost` defaults to `"localhost"`, not `None`, so the `MYSQL_DB_HOST` fallback only applies when a caller explicitly passes `dbHost=None`. Every other connection setting falls back to its environment variable when it isn't passed.
- **Exiting from library code**: `DbConnection`, `LocalDbApi`, `WfDbApi` and `DepositUtils.syncToDepositOp` call `sys.exit()` on errors instead of raising or returning False, so the process calling them gets killed.

### Found while adding type annotations to the top-level modules

Typing `DataSelector.py`, `DataValueContainer.py` and `WfDataObject.py` turned up no new hard errors; the only confirmed bug in these modules is still #1. Each point below was checked by running the code.

- **`DataValueContainer.isValueValid()` accepts `bool` as an integer**: with value type `"integer"` (or `"int"`), `setValue(True)` is reported as valid, because `bool` is a subclass of `int` in Python.
- **`DataValueContainer.isValueValid()` ignores the value type for dicts**: a `"dict"` container only checks that the value is a dict. With value type `"integer"`, `{"a": "x"}` is reported as valid. List containers, by contrast, check every element.
- **`DataValueContainer.isValueValid()` with nothing configured**: when no value type has been set, the expected type is `NoneType`. A container with no type and no value therefore reports itself as valid, while setting any value makes it invalid.
- **Dead branches in `DataValueContainer.setValueTypeName()`** (`DataValueContainer.py:118-133`): the inner code handles `"bool"`, but the outer check only accepts `"boolean"`, so `"bool"` is rejected before it gets there. The final `else: return False` can never run. Related to #1.
- **Exception handlers that can never fire in `DataSelector`**: `setSelectCategoryName()`, `addSelectAttributeName()` and `addSelectCondition()` wrap a single assignment or `list.append()` in a bare `except:` that returns False. Those operations can't raise, so the methods always return True. The bare `except:` would also swallow `KeyboardInterrupt` if anything ever did go wrong there.
- **`WfDataObject.__repr__()` returns the multi-line `printMe()` report** rather than a short, unambiguous representation, and it is identical to `__str__()`. Debuggers and logging that call `repr()` get the full report.
- **Python 2 leftovers**: `WfDataObject.py` tries `import cStringIO as StringIO` before falling back to `io`, and `DataValueContainer.py` does `from builtins import str`. Neither does anything on Python 3. The `cStringIO` fallback also leaves `StringIO` typed `Any`, so `__str__()` and `__repr__()` annotate a local as `str` to keep mypy's return-type check.

### Found while adding type annotations to `process/`

Each point below was checked by running the code.

- **A missing registry path empties the registry silently**: `ActionRegistry.__init__()` passes `ConfigInfo().get("SITE_REGISTRY_FILE_PATH")` straight to `ActionRegistryIo`. If the setting is missing, the path is `None`, parsing fails, a traceback is logged, and the registry is empty. Every `ProcessRunner.setAction()` then returns False with no hint why. `ActionRegistryIo` is typed to require a `str` path.
- **One malformed element discards the whole registry**: an `<action>`, `<wfDataObject>` or `<parameter>` element without a `name` attribute makes `getAttributeNode("name")` return `None`, and the `.nodeValue` that follows raises `AttributeError`. That aborts the entire parse, so the registry ends up empty rather than skipping the bad entry. These lines carry a `# type: ignore[union-attr]` that points here.
- **Empty `<wfDataObject>` elements are dropped**: an input or output declared as `<wfDataObject name="x"/>`, with no requirements, has no child nodes and is skipped. The action then expects one object fewer than it declares, so `preCheck()` fails on the count.
- **`ActionRegistryIo` defaults to a path that doesn't exist**: `filePath` defaults to `"./examples/resources/actionData.xml"`, which is not part of this repository.
- **`ActionRegistry.getActions()` returns a keys view**: the docstring promises a list, but it returns `dict_keys` (or `[]` on error). It is typed `Collection[str]`. Callers that index into it or append to it would fail.
- **`ProcessRunner.getParameterDict()` returns its internal dict**: changes a caller makes to the result change the parameters the next `run()` uses.
- **`if` that should be `elif`** (`ActionRegistryIo.py`, `__getActionDictionary()`): `methodName` is tested with `if` straight after the `moduleName` test, so a `moduleName` element also falls through the rest of the chain to `else: pass`. It has no effect today.

### Found while adding type annotations to `plugins/`

The only open confirmed plugin bug is #9. Line numbers below refer to the current, annotated code. Points marked *(confirmed)* were checked by running the code; the rest come from reading it.

- **Unresolved paths are never checked**: `WfDataObject.getFilePathReference()` and `getDirPathReference()` return `None` when a reference can't be resolved, and no plugin checks for that. Usually the next `os.path.join()`, `open()` or `os.access()` raises `TypeError` *(confirmed)*, the method's broad `except` catches it, and the op returns False with a traceback in the log. The typed code marks each of these spots with a commented `cast(str, ...)`. Exceptions to this pattern follow.
- **Optional `NmrUtils` config files fail the whole op**: the ops that read an optional `src0` config file guard it with `if os.path.exists(cnfInpPath)`. If that reference doesn't resolve, `os.path.exists(None)` raises `TypeError` *(confirmed)*, so the whole op returns False instead of carrying on without the config.
- **`NmrUtils.uploadChemicalShiftOp()` / `atomNameCheckCsXyzOp()` report success on a missing report path** (`NmrUtils.py:120, 231`): if the `dst2` reference doesn't resolve, `PdbxChemShiftReport(inputPath=None)` quietly returns an empty status and empty lists *(confirmed for the library call)*, and the op returns True. Both methods are marked deprecated. Both lines carry a `# type: ignore[arg-type]`.
- **`NmrUtils.str2nefReleaseOp()` ignores a failed consistency check** (`NmrUtils.py:1071, 1082`): the result of the first `dp.op("nmr-str-consistency-check")` is overwritten by the second `op()` call before it is checked.
- **`NmrUtils.mrgConsistencyCheckOp()` looks copy-pasted**: it runs `"nmr-str-consistency-check"` and logs under the name `strConsistencyCheckOp`. That may be intended.
- **Importing `NmrUtils` redirects standard output** (`NmrUtils.py:46`): the module sets `sys.stdout = sys.stderr` at import time, which affects the whole process, including anything that imports the plugin module only to list or test it.
- **A missing storage type gives a `None` output path** (`ChemCompUtils.py:435, 443`, `EmUtils.py:332-359`, `AnnotationUtils.py:805-867`): `getStorageType()` returns `None` for an external file reference *(confirmed)*. That value is passed to `PathInfo.getFilePath(fileSource=...)`, which logs a traceback and returns `None` *(confirmed)*. The op then carries on with a `None` output path instead of failing. In `AnnotationUtils.metalCoordinationOp()` and `metalCoordinationWithLargeTimeoutOp()` this means the FindGeo and MetalCoord output paths are `None`, the status update still runs, and the op returns True. These lines carry a `# type: ignore[arg-type]`.
- **`EmUtils` turns a `None` option into the string `"None"`** (`EmUtils.py:79, 114, 150, 407`): `options = str(uD["options"])` is followed by `if (options is not None) and len(options) > 0`. The `None` check can never be False, and a parameter whose value is `None` reaches the external tool as the literal option `"None"` *(confirmed for the expression)*.
- **Tool exit statuses are ignored**: most plugin ops run an external tool with `RcsbDpUtility.op()` and return True whenever no exception is raised, without looking at the exit status `op()` returns. `EmUtils.fsc_check_options()` and `imageMagickOp()` now behave the same way: a tool that runs but fails, returning a non-zero status, is reported as success. Checking the status would catch these failures, but it would change behaviour across many plugins.
- **`SeqdbUtils.matchEntityOp()` may return a non-boolean**: it returns the second element of `DataImporter.loadSeqDataAssemble()`, from the optional `wwpdb.apps.seqmodule` package, which isn't installed here. Its return type couldn't be checked; it is assumed to be a `bool`. A non-boolean result would reach `ProcessRunner.run()`, and its caller, unchanged.
- **`AnnotationUtils.xmlCheckOp()` can succeed without writing a report** (`AnnotationUtils.py:355`): if the output object has no file reference, `__checkXMLFile()` calls `open(None, "a")`. Its bare `except` swallows the error, so `xmlCheckOp()` returns True without writing the report. The line carries a `# type: ignore[arg-type]`.
- **`AnnotationUtils.emdXmlHeaderCheckOp()` can leave its work directory behind** (`AnnotationUtils.py:1576`): it creates a directory with `tempfile.mkdtemp()` and removes it at the end of the `try` block, with no `finally`. Any exception in between, such as a `None` deposition id or a failure in `EmHeaderUtils`, leaves an `rcsb-*` directory in the temporary area.
- **`wwpdb.io` returns a file path as the directory for external references**: for a `WfDataObject` set up with `setExternalFilePath()`, `getDirPathReference()` returns the same value as `getFilePathReference()`, the file path itself *(confirmed)*. Plugin ops that build `os.path.join(dirPath, "x.log")`, or pass `tmpPath=dirPath`, from such an object treat that file path as a directory. The behaviour is in the upstream `wwpdb.io` package, not here.
- **`str()` on paths in `PdbxUtils`**: `__templateSelection()`, `__templateFetchAttribute()`, `__templateFetchAnnAuto()` and `__getCategoryRowCount()` wrap the input path in `str()`, so an unresolved path becomes the file name `"None"`. Parsing then fails and the op returns False, which is safe.

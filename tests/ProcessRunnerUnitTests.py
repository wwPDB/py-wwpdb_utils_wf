##
# File: ProcessRunnerUnitTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for ProcessRunner using a small temporary action registry and a fake plugin module"""

import io
import os
import sys
import tempfile
import types
import unittest
from typing import Any, ClassVar, Dict, List, Optional
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.process.ActionRegistry import ActionRegistry
from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner
from wwpdb.utils.wf.WfDataObject import WfDataObject

FAKE_PKG = "fakewfpkg"
FAKE_MODULE = FAKE_PKG + ".FakeWfUtils"

_OBJ = """
      <wfDataObject name="%s">
        <dataReferenceType>file</dataReferenceType>
        <contentType>model</contentType>
        <fileFormat>pdbx</fileFormat>
        <containerType>value</containerType>
        <valueType>integer</valueType>
        <selectorType>attribute</selectorType>
      </wfDataObject>"""

TEST_REGISTRY = """<?xml version='1.0' encoding='utf-8'?>
<actionList version="0.01">
  <action name="check-op">
    <inputList>%s</inputList>
    <outputList>%s</outputList>
    <userParameters>
      <parameter name="mode">r</parameter>
      <parameter name="level">1</parameter>
    </userParameters>
    <internalParameters>
      <parameter name="force">-f</parameter>
    </internalParameters>
    <moduleName>%s</moduleName>
    <methodName>recordOp</methodName>
  </action>
  <action name="no-io">
    <moduleName>%s</moduleName>
    <methodName>recordOp</methodName>
  </action>
  <action name="missing-method">
    <moduleName>%s</moduleName>
    <methodName>notThereOp</methodName>
  </action>
  <action name="raise-op">
    <moduleName>%s</moduleName>
    <methodName>raiseOp</methodName>
  </action>
  <action name="bad-module">
    <moduleName>wwpdb_no_such_module_for_tests</moduleName>
    <methodName>recordOp</methodName>
  </action>
</actionList>
""" % (
    _OBJ % "src",
    _OBJ % "dst",
    FAKE_MODULE,
    FAKE_MODULE,
    FAKE_MODULE,
    FAKE_MODULE,
)

# Attributes compared by preCheck(): (WfDataObject getter, matching value, mismatching value, failure message fragment)
FEATURES = [
    ("getReferenceType", "file", "value", "reference type"),
    ("getContainerTypeName", "value", "list", "container type"),
    ("getValueTypeName", "integer", "string", "value type"),
    ("getSelectorType", "attribute", None, "selector type"),
    ("getContentType", "model", "model-annotate", "content type"),
    ("getFileFormat", "pdbx", "pdb", "file format"),
]


class FakeWfUtils:
    """Stand-in plugin class that records how it was constructed and called"""

    calls: ClassVar[List[Dict[str, Any]]] = []
    inits: ClassVar[List[Dict[str, Any]]] = []
    result: ClassVar[Any] = True

    def __init__(self, verbose: bool = False, log: Any = None) -> None:
        FakeWfUtils.inits.append({"verbose": verbose, "log": log})

    def recordOp(self, **kwArgs: Any) -> Any:
        FakeWfUtils.calls.append(kwArgs)
        return FakeWfUtils.result

    def raiseOp(self, **kwArgs: Any) -> bool:
        raise ValueError("boom %r" % sorted(kwArgs))


def _fakeModules() -> Dict[str, types.ModuleType]:
    pkg = types.ModuleType(FAKE_PKG)
    mod = types.ModuleType(FAKE_MODULE)
    setattr(mod, "FakeWfUtils", FakeWfUtils)  # noqa: B010
    setattr(pkg, "FakeWfUtils", mod)  # noqa: B010
    return {FAKE_PKG: pkg, FAKE_MODULE: mod}


def _dataObject(overrides: Optional[Dict[str, Any]] = None) -> MagicMock:
    """A WfDataObject stand-in whose type getters return values matching the test registry"""
    obj = MagicMock(spec=WfDataObject)
    for getter, good, _bad, _msg in FEATURES:
        getattr(obj, getter).return_value = good
    for getter, val in (overrides or {}).items():
        getattr(obj, getter).return_value = val
    return obj


class ProcessRunnerRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        regPath = os.path.join(self.__tmpDir.name, "actionData.xml")
        with open(regPath, "w", encoding="utf-8") as ofh:
            ofh.write(TEST_REGISTRY)
        self.__log = io.StringIO()
        with patch("wwpdb.utils.wf.process.ActionRegistry.ConfigInfo") as mockCi:
            mockCi.return_value.get.return_value = regPath
            self.__pR = ProcessRunner(verbose=True, log=self.__log)
            self.__quietPR = ProcessRunner(verbose=False, log=self.__log)
        FakeWfUtils.calls = []
        FakeWfUtils.inits = []
        FakeWfUtils.result = True

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _readyRunner(self, pR: Optional[ProcessRunner] = None) -> ProcessRunner:
        pR = pR if pR is not None else self.__pR
        self.assertTrue(pR.setAction("check-op"))
        self.assertTrue(pR.setInput("src", _dataObject()))
        self.assertTrue(pR.setOutput("dst", _dataObject()))
        return pR

    @unittest.expectedFailure
    def testPreCheckWrongInputNameReturnsFalse(self) -> None:
        # Library bug: preCheck() only compares input/output counts, not names.  With type constraints declared, an input
        # set under a name the registry does not expect raises KeyError out of preCheck() instead of returning False.
        # See ERRORS.md #14
        pR = self.__pR
        self.assertTrue(pR.setAction("check-op"))
        pR.setInput("wrong", _dataObject())
        pR.setOutput("dst", _dataObject())
        self.assertFalse(pR.preCheck())

    # --- setAction / parameters ---

    def testSetAction(self) -> None:
        self.assertTrue(self.__pR.setAction("check-op"))
        self.assertEqual(self.__pR.getParameterDict(), {"mode": "r", "level": "1"})
        self.assertFalse(self.__pR.setAction("no-such-action"))

    def testDefaultParametersAreACopy(self) -> None:
        self.__pR.setAction("check-op")
        self.__pR.getParameterDict()["mode"] = "changed"
        other = self.__quietPR
        other.setAction("check-op")
        self.assertEqual(other.getParameterDict()["mode"], "r")

    def testSetParameterDict(self) -> None:
        self.__pR.setAction("check-op")
        self.assertTrue(self.__pR.setParameterDict({"mode": "w", "unknown": 3}))
        # Only registered parameters are kept; missing ones fall back to registry defaults
        self.assertEqual(self.__pR.getParameterDict(), {"mode": "w", "level": "1"})
        text = self.__log.getvalue()
        self.assertIn("setting parameter mode to 'w'", text)
        self.assertIn("using default setting for parameter level = '1'", text)
        self.assertNotIn("unknown", text)

    def testSetParameterDictQuiet(self) -> None:
        self.__quietPR.setAction("check-op")
        self.assertTrue(self.__quietPR.setParameterDict({"level": "9"}))
        self.assertEqual(self.__quietPR.getParameterDict(), {"mode": "r", "level": "9"})
        self.assertEqual(self.__log.getvalue(), "")

    def testSetParameterDictFailure(self) -> None:
        self.__pR.setAction("check-op")
        with patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertFalse(self.__pR.setParameterDict(None))  # type: ignore[arg-type]  # deliberate misuse: checks the failure path
        self.assertIn("TypeError", err.getvalue())

    def testSetParameterDictNoAction(self) -> None:
        self.assertTrue(self.__pR.setParameterDict({"mode": "w"}))
        self.assertEqual(self.__pR.getParameterDict(), {})

    # --- preCheck ---

    def testPreCheckSuccess(self) -> None:
        self.assertTrue(self._readyRunner().preCheck())

    def testPreCheckNoInputsOrOutputs(self) -> None:
        self.assertTrue(self.__pR.setAction("no-io"))
        self.assertTrue(self.__pR.preCheck())

    def testPreCheckUndefinedAction(self) -> None:
        self.__pR.setAction("no-such-action")
        self.assertFalse(self.__pR.preCheck())
        self.assertIn("not a valid action  no-such-action", self.__log.getvalue())

    def testPreCheckInputCount(self) -> None:
        self.__pR.setAction("check-op")
        self.__pR.setOutput("dst", _dataObject())
        self.assertFalse(self.__pR.preCheck())
        self.assertIn("Failed input count", self.__log.getvalue())

    def testPreCheckOutputCount(self) -> None:
        self.__pR.setAction("check-op")
        self.__pR.setInput("src", _dataObject())
        self.assertFalse(self.__pR.preCheck())
        self.assertIn("Failed number of outputs", self.__log.getvalue())

    def testPreCheckInputMismatch(self) -> None:
        for getter, _good, bad, msg in FEATURES:
            for pR in (self.__pR, self.__quietPR):
                with self.subTest(getter=getter, verbose=pR is self.__pR):
                    self.__log.seek(0)
                    self.__log.truncate()
                    self._readyRunner(pR)
                    pR.setInput("src", _dataObject({getter: bad}))
                    self.assertFalse(pR.preCheck())
                    if pR is self.__pR:
                        self.assertIn("Failed input %s src" % msg, self.__log.getvalue())
                    else:
                        self.assertEqual(self.__log.getvalue(), "")

    def testPreCheckOutputMismatch(self) -> None:
        for getter, _good, bad, msg in FEATURES:
            for pR in (self.__pR, self.__quietPR):
                with self.subTest(getter=getter, verbose=pR is self.__pR):
                    self.__log.seek(0)
                    self.__log.truncate()
                    self._readyRunner(pR)
                    pR.setOutput("dst", _dataObject({getter: bad}))
                    self.assertFalse(pR.preCheck())
                    if pR is self.__pR:
                        self.assertIn("Failed output %s dst" % msg, self.__log.getvalue())
                    else:
                        self.assertEqual(self.__log.getvalue(), "")

    def testPreCheckRealWfDataObjects(self) -> None:
        # A real WfDataObject value container does not satisfy a file reference requirement
        pR = self._readyRunner()
        wfo = WfDataObject()
        wfo.setContainerTypeName("value")
        wfo.setValueTypeName("integer")
        pR.setOutput("dst", wfo)
        self.assertFalse(pR.preCheck())
        self.assertIn("Failed output reference type dst", self.__log.getvalue())

    # --- run ---

    def testRunDispatches(self) -> None:
        pR = self._readyRunner()
        pR.setParameterDict({"mode": "w"})
        FakeWfUtils.result = "status-value"
        with patch.dict(sys.modules, _fakeModules()):
            self.assertEqual(pR.run(), "status-value")
        self.assertEqual(FakeWfUtils.inits, [{"verbose": True, "log": self.__log}])
        self.assertEqual(len(FakeWfUtils.calls), 1)
        kw = FakeWfUtils.calls[0]
        self.assertEqual(sorted(kw.keys()), ["inputObjectD", "internalParameterD", "outputObjectD", "userParameterD"])
        self.assertEqual(sorted(kw["inputObjectD"].keys()), ["src"])
        self.assertEqual(sorted(kw["outputObjectD"].keys()), ["dst"])
        self.assertEqual(kw["userParameterD"], {"mode": "w", "level": "1"})
        self.assertEqual(kw["internalParameterD"], {"force": "-f"})

    def testRunReturnsMethodFalse(self) -> None:
        FakeWfUtils.result = False
        self.__quietPR.setAction("no-io")
        with patch.dict(sys.modules, _fakeModules()):
            self.assertFalse(self.__quietPR.run())
        self.assertEqual(FakeWfUtils.inits, [{"verbose": False, "log": self.__log}])
        self.assertEqual(FakeWfUtils.calls, [{"inputObjectD": {}, "outputObjectD": {}, "userParameterD": {}, "internalParameterD": {}}])

    def testRunMissingMethod(self) -> None:
        self.__pR.setAction("missing-method")
        with patch.dict(sys.modules, _fakeModules()):
            self.assertFalse(self.__pR.run())
        self.assertEqual(len(FakeWfUtils.inits), 1)
        self.assertEqual(FakeWfUtils.calls, [])

    def testRunMethodRaises(self) -> None:
        self.__pR.setAction("raise-op")
        with patch.dict(sys.modules, _fakeModules()):
            self.assertFalse(self.__pR.run())
        self.assertIn("ValueError: boom", self.__log.getvalue())

    def testRunImportFails(self) -> None:
        self.__pR.setAction("bad-module")
        with patch.dict(sys.modules, {}):
            self.assertFalse(self.__pR.run())
        self.assertIn("ModuleNotFoundError", self.__log.getvalue())
        self.__quietPR.setAction("bad-module")
        self.__log.seek(0)
        self.__log.truncate()
        self.assertFalse(self.__quietPR.run())
        self.assertEqual(self.__log.getvalue(), "")

    def testRunWithoutAction(self) -> None:
        self.assertFalse(self.__quietPR.run())


class ProcessRunnerMockRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch("wwpdb.utils.wf.process.ProcessRunner.ActionRegistry", autospec=True)
        self.__mockCls = patcher.start()
        self.addCleanup(patcher.stop)
        self.__aReg = self.__mockCls.return_value
        self.__log = io.StringIO()
        self.__pR = ProcessRunner(verbose=True, log=self.__log)

    def testRegistryCreated(self) -> None:
        self.__mockCls.assert_called_once_with()

    def testSetActionUndefined(self) -> None:
        self.__aReg.isDefinedAction.return_value = False
        self.assertFalse(self.__pR.setAction("x"))
        self.__aReg.isDefinedAction.assert_called_once_with("x")
        self.__aReg.getUserParameterDict.assert_not_called()

    def testSetActionDefined(self) -> None:
        self.__aReg.isDefinedAction.return_value = True
        self.__aReg.getUserParameterDict.return_value = {"a": "1"}
        self.assertTrue(self.__pR.setAction("x"))
        self.__aReg.getUserParameterDict.assert_called_once_with("x")
        self.assertEqual(self.__pR.getParameterDict(), {"a": "1"})

    def testSetActionDefaultParameterFailure(self) -> None:
        self.__aReg.isDefinedAction.return_value = True
        self.__aReg.getUserParameterDict.side_effect = RuntimeError("bad registry")
        with patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertTrue(self.__pR.setAction("x"))
        self.assertIn("bad registry", err.getvalue())
        self.assertEqual(self.__pR.getParameterDict(), {})

    def testPreCheckSkipsUnsetFeatures(self) -> None:
        aReg = self.__aReg
        aReg.isDefinedAction.return_value = True
        aReg.getUserParameterDict.return_value = {}
        aReg.getInputObjectCount.return_value = 1
        aReg.getInputObjectNames.return_value = ["in"]
        aReg.getOutputObjectCount.return_value = 0
        for name in dir(ActionRegistry):
            if name.startswith(("isSetInput", "isSetOutput")):
                getattr(aReg, name).return_value = False
        self.__pR.setAction("x")
        obj = MagicMock(spec=WfDataObject)
        self.__pR.setInput("in", obj)
        self.assertTrue(self.__pR.preCheck())
        aReg.getInputReferenceType.assert_not_called()
        obj.getReferenceType.assert_not_called()
        aReg.isSetInputFileFormat.assert_called_once_with("x", "in")

    @unittest.expectedFailure
    def testPreCheckWrongInputNameWithoutConstraints(self) -> None:
        # Library bug: with no type constraints, an input set under the wrong name passes preCheck(), and run() then hands
        # the plugin an inputObjectD without the name it expects.  See ERRORS.md #14
        aReg = self.__aReg
        aReg.isDefinedAction.return_value = True
        aReg.getUserParameterDict.return_value = {}
        aReg.getInputObjectCount.return_value = 1
        aReg.getInputObjectNames.return_value = ["in"]
        aReg.getOutputObjectCount.return_value = 0
        for name in dir(ActionRegistry):
            if name.startswith(("isSetInput", "isSetOutput")):
                getattr(aReg, name).return_value = False
        self.__pR.setAction("x")
        self.__pR.setInput("wrong", MagicMock(spec=WfDataObject))
        self.assertFalse(self.__pR.preCheck())

    def testSetInputOutputStringifiesNames(self) -> None:
        aReg = self.__aReg
        aReg.isDefinedAction.return_value = True
        aReg.getUserParameterDict.return_value = {}
        aReg.getInputObjectCount.return_value = 1
        aReg.getInputObjectNames.return_value = ["1"]
        aReg.getOutputObjectCount.return_value = 1
        aReg.getOutputObjectNames.return_value = ["2"]
        aReg.isSetInputReferenceType.return_value = True
        aReg.getInputReferenceType.return_value = "file"
        aReg.isSetOutputReferenceType.return_value = True
        aReg.getOutputReferenceType.return_value = "file"
        for name in ("Container", "Value", "Selector", "Content"):
            getattr(aReg, "isSetInput%sType" % name).return_value = False
            getattr(aReg, "isSetOutput%sType" % name).return_value = False
        aReg.isSetInputFileFormat.return_value = False
        aReg.isSetOutputFileFormat.return_value = False
        self.__pR.setAction("x")
        obj = MagicMock(spec=WfDataObject)
        obj.getReferenceType.return_value = "file"
        self.assertTrue(self.__pR.setInput(1, obj))
        self.assertTrue(self.__pR.setOutput(2, obj))
        self.assertTrue(self.__pR.preCheck())
        aReg.getInputReferenceType.assert_called_once_with("x", "1")
        aReg.getOutputReferenceType.assert_called_once_with("x", "2")


if __name__ == "__main__":
    unittest.main()

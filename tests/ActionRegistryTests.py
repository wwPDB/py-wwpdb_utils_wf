##
# File: ActionRegistryTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for ActionRegistryIo (XML parsing) and ActionRegistry (query API)"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.wf.process.ActionRegistry import ActionRegistry
from wwpdb.utils.wf.process.ActionRegistryIo import ActionRegistryIo

SAMPLE_REGISTRY = """<?xml version='1.0' encoding='utf-8'?>
<actionList version="0.01">
  <action name="alpha">
    <inputList>
      <wfDataObject name="second">
        <dataReferenceType>file</dataReferenceType>
        <contentType>model</contentType>
        <fileFormat>pdbx</fileFormat>
        <containerType></containerType>
        <selectorType>attribute</selectorType>
      </wfDataObject>
      <wfDataObject name="first">
        <dataReferenceType></dataReferenceType>
        <containerType>value</containerType>
        <valueType>integer</valueType>
      </wfDataObject>
      <wfDataObject name="skipped"/>
    </inputList>
    <outputList>
      <wfDataObject name="out">
        <containerType>list</containerType>
        <valueType>string</valueType>
      </wfDataObject>
    </outputList>
    <userParameters>
      <parameter name="mode">r</parameter>
      <parameter name="empty"></parameter>
    </userParameters>
    <internalParameters>
      <parameter name="force">-f</parameter>
    </internalParameters>
    <moduleName>some.pkg.ModuleName</moduleName>
    <methodName>alphaOp</methodName>
  </action>
  <action name="beta">
    <inputList/>
    <userParameters>
    </userParameters>
    <moduleName>other.Module</moduleName>
  </action>
  <action name="gamma">
    <inputList>
      <wfDataObject name="src">
        <containerType>value</containerType>
      </wfDataObject>
    </inputList>
    <outputList>
      <wfDataObject name="dst">
        <containerType>value</containerType>
      </wfDataObject>
    </outputList>
    <moduleName>g.Mod</moduleName>
    <methodName>gammaOp</methodName>
  </action>
</actionList>
"""


def _writeRegistry(dirPath: str, text: str = SAMPLE_REGISTRY) -> str:
    fp = os.path.join(dirPath, "actionData.xml")
    with open(fp, "w", encoding="utf-8") as ofh:
        ofh.write(text)
    return fp


class ActionRegistryIoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__regPath = _writeRegistry(self.__tmpDir.name)

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _registry(self) -> Any:
        return ActionRegistryIo(filePath=self.__regPath, log=io.StringIO()).getRegistry()

    def testActionIds(self) -> None:
        self.assertEqual(sorted(self._registry().keys()), ["alpha", "beta", "gamma"])

    def testInputsKeepDocumentOrder(self) -> None:
        aD = self._registry()["alpha"]
        self.assertEqual(aD["INPUT_NAME_LIST"], ["second", "first"])
        # Empty <wfDataObject/> elements are ignored
        self.assertEqual(sorted(aD["INPUT_INFO_LIST"].keys()), ["first", "second"])
        self.assertEqual(aD["OUTPUT_NAME_LIST"], ["out"])

    def testWfDataObjectAttributes(self) -> None:
        aD = self._registry()["alpha"]
        self.assertEqual(
            aD["INPUT_INFO_LIST"]["second"],
            {
                "dataReferenceType": "file",
                "contentType": "model",
                "fileFormat": "pdbx",
                "containerType": None,
                "valueType": None,
                "selectorType": "attribute",
            },
        )
        first = aD["INPUT_INFO_LIST"]["first"]
        self.assertIsNone(first["dataReferenceType"])
        self.assertEqual(first["containerType"], "value")
        self.assertEqual(first["valueType"], "integer")
        self.assertIsNone(first["contentType"])
        self.assertEqual(aD["OUTPUT_INFO_LIST"]["out"]["containerType"], "list")
        self.assertEqual(aD["OUTPUT_INFO_LIST"]["out"]["valueType"], "string")

    def testParameters(self) -> None:
        aD = self._registry()["alpha"]
        self.assertEqual(aD["USER_PARAMETER_DICT"], {"mode": "r", "empty": None})
        self.assertEqual(aD["INTERNAL_PARAMETER_DICT"], {"force": "-f"})

    def testModuleAndMethod(self) -> None:
        reg = self._registry()
        self.assertEqual(reg["alpha"]["MODULE_NAME"], "some.pkg.ModuleName")
        self.assertEqual(reg["alpha"]["METHOD_NAME"], "alphaOp")
        self.assertEqual(reg["beta"]["MODULE_NAME"], "other.Module")
        self.assertIsNone(reg["beta"]["METHOD_NAME"])

    def testDefaultsForMissingSections(self) -> None:
        bD = self._registry()["beta"]
        self.assertEqual(bD["INPUT_INFO_LIST"], {})
        self.assertEqual(bD["INPUT_NAME_LIST"], [])
        self.assertEqual(bD["OUTPUT_INFO_LIST"], {})
        self.assertEqual(bD["OUTPUT_NAME_LIST"], [])
        self.assertEqual(bD["USER_PARAMETER_DICT"], {})
        self.assertEqual(bD["INTERNAL_PARAMETER_DICT"], {})

    def testMissingFile(self) -> None:
        log = io.StringIO()
        missing = os.path.join(self.__tmpDir.name, "nope.xml")
        aR = ActionRegistryIo(filePath=missing, log=log)
        self.assertEqual(aR.getRegistry(), {})
        self.assertIn("read failed for %s" % missing, log.getvalue())

    def testMalformedFile(self) -> None:
        log = io.StringIO()
        bad = _writeRegistry(self.__tmpDir.name, "<actionList><action name='x'>")
        aR = ActionRegistryIo(filePath=bad, log=log)
        self.assertEqual(aR.getRegistry(), {})
        self.assertIn("read failed", log.getvalue())

    def testDump(self) -> None:
        log = io.StringIO()
        aR = ActionRegistryIo(filePath=self.__regPath, log=log)
        aR.dump()
        text = log.getvalue()
        self.assertIn("Action registry file", text)
        self.assertIn("alphaOp", text)
        self.assertIn("some.pkg.ModuleName", text)


class ActionRegistryTempTests(unittest.TestCase):
    """ActionRegistry over a small registry, with ConfigInfo patched to point at it"""

    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        regPath = _writeRegistry(self.__tmpDir.name)
        with patch("wwpdb.utils.wf.process.ActionRegistry.ConfigInfo") as mockCi:
            mockCi.return_value.get.return_value = regPath
            self.__aR = ActionRegistry()
            mockCi.return_value.get.assert_called_once_with("SITE_REGISTRY_FILE_PATH")

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def testActions(self) -> None:
        self.assertEqual(sorted(self.__aR.getActions()), ["alpha", "beta", "gamma"])
        self.assertTrue(self.__aR.isDefinedAction("alpha"))
        self.assertFalse(self.__aR.isDefinedAction("delta"))

    def testCountsAndNames(self) -> None:
        aR = self.__aR
        self.assertEqual(aR.getInputObjectCount("alpha"), 2)
        self.assertEqual(aR.getInputObjectNames("alpha"), ["second", "first"])
        self.assertEqual(aR.getOutputObjectCount("alpha"), 1)
        self.assertEqual(aR.getOutputObjectNames("alpha"), ["out"])
        self.assertEqual(aR.getInputObjectCount("beta"), 0)
        self.assertEqual(aR.getOutputObjectNames("beta"), [])

    def testInputAccessors(self) -> None:
        aR = self.__aR
        self.assertTrue(aR.isSetInputReferenceType("alpha", "second"))
        self.assertEqual(aR.getInputReferenceType("alpha", "second"), "file")
        self.assertFalse(aR.isSetInputReferenceType("alpha", "first"))
        self.assertIsNone(aR.getInputReferenceType("alpha", "first"))
        self.assertTrue(aR.isSetInputContentType("alpha", "second"))
        self.assertEqual(aR.getInputContentType("alpha", "second"), "model")
        self.assertTrue(aR.isSetInputFileFormat("alpha", "second"))
        self.assertEqual(aR.getInputFileFormat("alpha", "second"), "pdbx")
        self.assertTrue(aR.isSetInputSelectorType("alpha", "second"))
        self.assertEqual(aR.getInputSelectorType("alpha", "second"), "attribute")
        self.assertFalse(aR.isSetInputContainerType("alpha", "second"))
        self.assertTrue(aR.isSetInputContainerType("alpha", "first"))
        self.assertEqual(aR.getInputContainerType("alpha", "first"), "value")
        self.assertTrue(aR.isSetInputValueType("alpha", "first"))
        self.assertEqual(aR.getInputValueType("alpha", "first"), "integer")
        self.assertFalse(aR.isSetInputValueType("alpha", "second"))

    def testOutputAccessors(self) -> None:
        aR = self.__aR
        self.assertFalse(aR.isSetOutputReferenceType("alpha", "out"))
        self.assertIsNone(aR.getOutputReferenceType("alpha", "out"))
        self.assertTrue(aR.isSetOutputContainerType("alpha", "out"))
        self.assertEqual(aR.getOutputContainerType("alpha", "out"), "list")
        self.assertTrue(aR.isSetOutputValueType("alpha", "out"))
        self.assertEqual(aR.getOutputValueType("alpha", "out"), "string")
        self.assertFalse(aR.isSetOutputSelectorType("alpha", "out"))
        self.assertIsNone(aR.getOutputSelectorType("alpha", "out"))
        self.assertFalse(aR.isSetOutputContentType("alpha", "out"))
        self.assertIsNone(aR.getOutputContentType("alpha", "out"))
        self.assertFalse(aR.isSetOutputFileFormat("alpha", "out"))
        self.assertIsNone(aR.getOutputFileFormat("alpha", "out"))
        # Output value type check works on the right field (contrast with the input variant below)
        self.assertFalse(self.__aR.isSetOutputValueType("gamma", "dst"))

    @unittest.expectedFailure
    def testInputValueTypeUnsetWhenOnlyContainerTypeGiven(self) -> None:
        # Bug: ActionRegistry.isSetInputValueType() tests "containerType" instead of "valueType"
        self.assertFalse(self.__aR.isSetInputValueType("gamma", "src"))

    def testDefaultInputName(self) -> None:
        # The default object name "1" is not used in this registry
        self.assertFalse(self.__aR.isSetInputContainerType("gamma"))
        self.assertIsNone(self.__aR.getInputContainerType("gamma"))
        self.assertFalse(self.__aR.isSetOutputContainerType("gamma"))

    def testModuleMethodAndParameters(self) -> None:
        aR = self.__aR
        self.assertEqual(aR.getModuleName("alpha"), "some.pkg.ModuleName")
        self.assertEqual(aR.getMethodName("alpha"), "alphaOp")
        self.assertIsNone(aR.getMethodName("beta"))
        self.assertEqual(aR.getUserParameterDict("alpha"), {"mode": "r", "empty": None})
        self.assertEqual(aR.getInternalParameterDict("alpha"), {"force": "-f"})

    def testSetUserParameter(self) -> None:
        aR = self.__aR
        self.assertEqual(aR.getUserParameter("alpha", "mode"), "r")
        self.assertTrue(aR.setUserParameter("alpha", "mode", "w"))
        self.assertEqual(aR.getUserParameter("alpha", "mode"), "w")
        self.assertTrue(aR.setUserParameter("alpha", "newKey", 5))
        self.assertEqual(aR.getUserParameterDict("alpha")["newKey"], 5)
        self.assertIsNone(aR.getUserParameter("alpha", "noSuchKey"))
        self.assertFalse(aR.setUserParameter("delta", "mode", "w"))
        self.assertIsNone(aR.getUserParameter("delta", "mode"))

    def testUnknownAction(self) -> None:
        aR = self.__aR
        with patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertEqual(aR.getInputObjectCount("delta"), 0)
            self.assertEqual(aR.getInputObjectNames("delta"), [])
        self.assertIn("KeyError", err.getvalue())
        self.assertEqual(aR.getOutputObjectCount("delta"), 0)
        self.assertEqual(aR.getOutputObjectNames("delta"), [])
        self.assertIsNone(aR.getModuleName("delta"))
        self.assertIsNone(aR.getMethodName("delta"))
        self.assertEqual(aR.getUserParameterDict("delta"), {})
        self.assertEqual(aR.getInternalParameterDict("delta"), {})
        for prefix in ("Input", "Output"):
            for feature in ("ReferenceType", "ContainerType", "ValueType", "SelectorType", "ContentType", "FileFormat"):
                with self.subTest(prefix=prefix, feature=feature):
                    self.assertFalse(getattr(aR, "isSet%s%s" % (prefix, feature))("delta", "src"))
                    self.assertIsNone(getattr(aR, "get%s%s" % (prefix, feature))("delta", "src"))

    def testMissingRegistryFile(self) -> None:
        log = io.StringIO()

        def quietIo(filePath: str) -> ActionRegistryIo:
            return ActionRegistryIo(filePath=filePath, log=log)

        missing = os.path.join(self.__tmpDir.name, "missing.xml")
        with patch("wwpdb.utils.wf.process.ActionRegistry.ConfigInfo") as mockCi, patch("wwpdb.utils.wf.process.ActionRegistry.ActionRegistryIo", side_effect=quietIo):
            mockCi.return_value.get.return_value = missing
            aR = ActionRegistry()
        self.assertIn("read failed for %s" % missing, log.getvalue())
        self.assertEqual(list(aR.getActions()), [])
        self.assertFalse(aR.isDefinedAction("alpha"))

    def testGetActionsFailure(self) -> None:
        # getActions() returns [] if the registry is not a dictionary
        with patch("wwpdb.utils.wf.process.ActionRegistry.ActionRegistryIo") as mockIo, patch("wwpdb.utils.wf.process.ActionRegistry.ConfigInfo"):
            mockIo.return_value.getRegistry.return_value = MagicMock(spec=[])
            aR = ActionRegistry()
        self.assertEqual(aR.getActions(), [])


class ActionRegistryMockSiteTests(unittest.TestCase):
    """ActionRegistry against the registry shipped with the mock site configuration"""

    aR: ActionRegistry

    @classmethod
    def setUpClass(cls) -> None:
        cls.aR = ActionRegistry()

    def testRegistryPathFromConfig(self) -> None:
        regPath = ConfigInfo().get("SITE_REGISTRY_FILE_PATH")
        self.assertTrue(os.path.exists(regPath))

    def testKnownActions(self) -> None:
        actions = list(self.aR.getActions())
        self.assertGreater(len(actions), 50)
        for act in ("copy", "copy-if-exists", "mkdir", "sizeof", "mtime", "diff", "select"):
            with self.subTest(action=act):
                self.assertIn(act, actions)
                self.assertTrue(self.aR.isDefinedAction(act))
        self.assertFalse(self.aR.isDefinedAction("not-an-action"))

    def testCopy(self) -> None:
        aR = self.aR
        self.assertEqual(aR.getModuleName("copy"), "wwpdb.utils.wf.plugins.FileUtils")
        self.assertEqual(aR.getMethodName("copy"), "copyOp")
        self.assertEqual(aR.getInputObjectNames("copy"), ["src"])
        self.assertEqual(aR.getOutputObjectNames("copy"), ["dst"])
        self.assertEqual(aR.getUserParameterDict("copy"), {"mode": "r"})
        self.assertEqual(aR.getInternalParameterDict("copy"), {})
        self.assertTrue(aR.isSetInputReferenceType("copy", "src"))
        self.assertEqual(aR.getInputReferenceType("copy", "src"), "file")
        self.assertFalse(aR.isSetInputContentType("copy", "src"))
        self.assertEqual(aR.getOutputReferenceType("copy", "dst"), "file")

    def testMkdirHasNoOutputs(self) -> None:
        self.assertEqual(self.aR.getInputObjectCount("mkdir"), 1)
        self.assertEqual(self.aR.getOutputObjectCount("mkdir"), 0)
        self.assertEqual(self.aR.getUserParameter("mkdir", "mode"), "0755")

    def testDiff(self) -> None:
        aR = self.aR
        self.assertEqual(aR.getInputObjectNames("diff"), ["src1", "src2"])
        self.assertEqual(aR.getInputObjectCount("diff"), 2)
        self.assertEqual(aR.getOutputContainerType("diff", "dst"), "list")
        self.assertFalse(aR.isSetOutputReferenceType("diff", "dst"))

    def testSelect(self) -> None:
        aR = self.aR
        self.assertEqual(aR.getModuleName("select"), "wwpdb.utils.wf.plugins.PdbxUtils")
        self.assertEqual(aR.getInputContentType("select", "src"), "model")
        self.assertEqual(aR.getInputFileFormat("select", "src"), "pdbx")
        self.assertEqual(aR.getInputSelectorType("select", "src"), "attribute")
        self.assertEqual(aR.getOutputContainerType("select", "dst"), "list")
        self.assertEqual(aR.getOutputValueType("select", "dst"), "string")
        self.assertEqual(aR.getInternalParameterDict("select"), {"blockNumber": "1"})


if __name__ == "__main__":
    unittest.main()

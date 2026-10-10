##
# File: PcmCsvUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the PcmCsvUtils workflow plugin"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.PcmCsvUtils import PcmCsvUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

PCM_COLUMNS = (
    "Comp_id",
    "Link_id",
    "Modified_residue_id",
    "Type",
    "Category",
    "Position",
    "Polypeptide_position",
    "Comp_id_linking_atom",
    "Modified_residue_id_linking_atom",
    "First_instance_model_db_code",
)
PCM_HEADER = ",".join(PCM_COLUMNS)


def _fileObj(filePath: str) -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    return obj


def _valueObj(containerType: str) -> WfDataObject:
    obj = WfDataObject()
    obj.setContainerTypeName(containerType)
    obj.setValueTypeName("string")
    return obj


class PcmCsvUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__log = io.StringIO()
        self.__util = PcmCsvUtils(verbose=True, log=self.__log)

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _writeCsv(self, content: str) -> str:
        fPath = os.path.join(self.__tmpDir.name, "pcm-missing-data.csv")
        with open(fPath, "w") as ofh:
            ofh.write(content)
        return fPath

    def _run(self, srcPath: str, dst: Any) -> bool:
        kw: Dict[str, Any] = {
            "inputObjectD": {"src": _fileObj(srcPath)},
            "outputObjectD": {"dst": dst},
            "userParameterD": {},
            "internalParameterD": {},
        }
        return bool(self.__util.missingPcmDataOp(**kw))

    def testMissingDataValue(self) -> None:
        srcPath = self._writeCsv(PCM_HEADER + "\nSEP,,,,,,,,,\n")
        dst = _valueObj("value")
        self.assertTrue(self._run(srcPath, dst))
        self.assertEqual(dst.getValue(), "YES")

    def testMissingDataList(self) -> None:
        srcPath = self._writeCsv(PCM_HEADER + "\n")
        dst = _valueObj("list")
        self.assertTrue(self._run(srcPath, dst))
        self.assertEqual(dst.getValue(), ["YES"])

    def testOtherContentIsNo(self) -> None:
        srcPath = self._writeCsv("Some,other,header\n")
        for containerType, expected in (("value", "NO"), ("list", ["NO"])):
            with self.subTest(containerType=containerType):
                dst = _valueObj(containerType)
                self.assertTrue(self._run(srcPath, dst))
                self.assertEqual(dst.getValue(), expected)

    def testUnreadableFileIsNo(self) -> None:
        dst = _valueObj("value")
        self.assertTrue(self._run(os.path.join(self.__tmpDir.name, "missing.csv"), dst))
        self.assertEqual(dst.getValue(), "NO")

    def testUnsupportedContainer(self) -> None:
        srcPath = self._writeCsv(PCM_HEADER + "\n")
        dst = _valueObj("dict")
        self.assertFalse(self._run(srcPath, dst))
        self.assertIsNone(dst.getValue())

    def testExceptionReturnsFalse(self) -> None:
        src = MagicMock(spec=WfDataObject)
        src.getFilePathReference.side_effect = RuntimeError("boom")
        kw: Dict[str, Any] = {"inputObjectD": {"src": src}, "outputObjectD": {"dst": _valueObj("value")}, "userParameterD": {}, "internalParameterD": {}}
        self.assertFalse(self.__util.missingPcmDataOp(**kw))
        self.assertIn("RuntimeError: boom", self.__log.getvalue())

    def testMissingOutputReturnsFalse(self) -> None:
        srcPath = self._writeCsv(PCM_HEADER + "\n")
        kw: Dict[str, Any] = {"inputObjectD": {"src": _fileObj(srcPath)}, "outputObjectD": {}, "userParameterD": {}, "internalParameterD": {}}
        self.assertFalse(self.__util.missingPcmDataOp(**kw))
        self.assertIn("KeyError", self.__log.getvalue())


if __name__ == "__main__":
    unittest.main()

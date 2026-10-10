##
# File: ReportUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the ReportUtils workflow plugin"""

import io
import sys
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.ReportUtils import ReportUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


def _fileObj(filePath: str) -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    return obj


def _kwArgs() -> Dict[str, Any]:
    return {
        "inputObjectD": {"src1": _fileObj("/data/model.cif"), "src2": _fileObj("/data/ligand.cif")},
        "outputObjectD": {"dst": _fileObj("/data/out.cif")},
        "userParameterD": {},
        "internalParameterD": {},
    }


class ReportUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__log = io.StringIO()

    @patch("wwpdb.utils.wf.plugins.ReportUtils.PdbxMergeCategory")
    def testCombineLigandInfo(self, mockMerge: MagicMock) -> None:
        mockMerge.return_value.merge.return_value = True
        util = ReportUtils(verbose=True, log=self.__log)
        self.assertTrue(util.combineLigandInfoOp(**_kwArgs()))
        mockMerge.return_value.merge.assert_called_once_with(
            "/data/model.cif",
            "/data/ligand.cif",
            "/data/out.cif",
            ["pdbx_entry_details"],
            ["pdbx_binding_assay", "pdbx_entity_instance_feature"],
        )
        text = self.__log.getvalue()
        self.assertIn("src1 input  file paths:  /data/model.cif", text)
        self.assertIn("output path: /data/out.cif", text)
        self.assertIn("return: True", text)

    @patch("wwpdb.utils.wf.plugins.ReportUtils.PdbxMergeCategory")
    def testMergeFailurePropagates(self, mockMerge: MagicMock) -> None:
        mockMerge.return_value.merge.return_value = False
        util = ReportUtils(verbose=False, log=self.__log)
        self.assertFalse(util.combineLigandInfoOp(**_kwArgs()))
        self.assertEqual(self.__log.getvalue(), "")

    @patch("wwpdb.utils.wf.plugins.ReportUtils.PdbxMergeCategory")
    def testExceptionReturnsFalse(self, mockMerge: MagicMock) -> None:
        mockMerge.return_value.merge.side_effect = OSError("cannot read")
        util = ReportUtils(verbose=False, log=self.__log)
        self.assertFalse(util.combineLigandInfoOp(**_kwArgs()))
        self.assertIn("cannot read", self.__log.getvalue())

    @patch("wwpdb.utils.wf.plugins.ReportUtils.PdbxMergeCategory")
    def testMissingInputReturnsFalse(self, mockMerge: MagicMock) -> None:
        kw = _kwArgs()
        del kw["inputObjectD"]["src2"]
        util = ReportUtils(verbose=False, log=self.__log)
        self.assertFalse(util.combineLigandInfoOp(**kw))
        mockMerge.assert_not_called()


if __name__ == "__main__":
    unittest.main()

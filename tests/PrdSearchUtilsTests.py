##
# File: PrdSearchUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the PrdSearchUtils workflow plugin"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.wf.plugins.PrdSearchUtils import PrdSearchUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


class PrdSearchUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__dirPath = self.__tmpDir.name
        self.__resultPath = os.path.join(self.__dirPath, "D_000001_prd-summary_P1.cif.V1")
        self.__log = io.StringIO()
        self.__siteId = ConfigInfo().get("SITE_PREFIX")

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _kwArgs(self) -> Dict[str, Any]:
        src = MagicMock(spec=WfDataObject)
        src.getFilePathReference.return_value = "/data/D_000001_model_P1.cif.V1"
        dst = MagicMock(spec=WfDataObject)
        dst.getFilePathReference.return_value = self.__resultPath
        dst.getDirPathReference.return_value = self.__dirPath
        return {"inputObjectD": {"src": src}, "outputObjectD": {"dst": dst}, "userParameterD": {}, "internalParameterD": {}}

    def _writeResult(self, filePath: str) -> None:
        with open(filePath, "w") as ofh:
            ofh.write("data_prd\n")

    @patch("wwpdb.utils.wf.plugins.PrdSearchUtils.RcsbDpUtility")
    def testSearchAndSummary(self, mockDp: MagicMock) -> None:
        dpSearch = MagicMock()
        dpSearch.exp.side_effect = self._writeResult
        dpSummary = MagicMock()
        mockDp.side_effect = [dpSearch, dpSummary]

        util = PrdSearchUtils(verbose=False, log=self.__log)
        self.assertTrue(util.PrdSearchOp(**self._kwArgs()))

        workDir = os.path.join(self.__dirPath, "search")
        self.assertEqual(mockDp.call_count, 2)
        for c in mockDp.call_args_list:
            self.assertEqual(c, call(tmpPath=self.__dirPath, siteId=self.__siteId, verbose=False, log=self.__log))
        dpSearch.setWorkingDir.assert_called_once_with(workDir)
        expected: List[Any] = [
            call(name="firstmodel", value=os.path.join(workDir, "firstmodel.cif")),
            call(name="logfile", value=os.path.join(workDir, "search-prd.log")),
        ]
        self.assertEqual(dpSearch.addInput.call_args_list, expected)
        dpSearch.imp.assert_called_once_with("/data/D_000001_model_P1.cif.V1")
        dpSearch.op.assert_called_once_with("prd-search")
        dpSearch.exp.assert_called_once_with(self.__resultPath)
        dpSearch.cleanup.assert_not_called()

        self.assertEqual(
            dpSummary.addInput.call_args_list,
            [call(name="resultFile", value=self.__resultPath), call(name="logfile", value=os.path.join(workDir, "process-prd.log"))],
        )
        dpSummary.op.assert_called_once_with("prd-process-summary")
        dpSummary.cleanup.assert_not_called()

    @patch("wwpdb.utils.wf.plugins.PrdSearchUtils.RcsbDpUtility")
    def testMissingResultStopsEarly(self, mockDp: MagicMock) -> None:
        util = PrdSearchUtils(verbose=False, log=self.__log)
        self.assertFalse(util.PrdSearchOp(**self._kwArgs()))
        self.assertEqual(mockDp.call_count, 1)
        mockDp.return_value.op.assert_called_once_with("prd-search")

    @patch("wwpdb.utils.wf.plugins.PrdSearchUtils.RcsbDpUtility")
    def testExceptionReturnsFalse(self, mockDp: MagicMock) -> None:
        mockDp.return_value.op.side_effect = RuntimeError("search failed")
        util = PrdSearchUtils(verbose=False, log=self.__log)
        self.assertFalse(util.PrdSearchOp(**self._kwArgs()))
        self.assertIn("search failed", self.__log.getvalue())
        mockDp.return_value.exp.assert_not_called()


if __name__ == "__main__":
    unittest.main()

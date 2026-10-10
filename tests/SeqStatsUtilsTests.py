##
# File: SeqStatsUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the (obsolete) SeqStatsUtils workflow plugin"""

import io
import sys
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.SeqStatsUtils import SeqStatsUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


def _kwArgs(outputObjectD: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"inputObjectD": {}, "outputObjectD": outputObjectD if outputObjectD is not None else {}, "userParameterD": {}, "internalParameterD": {}}


def _dstObj() -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getWorkflowInstanceId.return_value = "W_000123"
    obj.getDepositionDataSetId.return_value = "D_000001"
    obj.getStorageType.return_value = "wf-instance"
    obj.getDirPathReference.return_value = "/data/wf/D_000001/W_000123"
    return obj


class SeqStatsUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__log = io.StringIO()

    def testPrepareSequenceData(self) -> None:
        util = SeqStatsUtils(verbose=True, log=self.__log)
        self.assertTrue(util.prepareSequenceDataOp(**_kwArgs()))
        self.assertIn("This module is obsolete", self.__log.getvalue())

    def testPrepareSequenceDataQuiet(self) -> None:
        util = SeqStatsUtils(verbose=False, log=self.__log)
        self.assertTrue(util.prepareSequenceDataOp(**_kwArgs()))
        self.assertEqual(self.__log.getvalue(), "")

    def testPrepareSequenceDataBadArgs(self) -> None:
        util = SeqStatsUtils(verbose=False, log=self.__log)
        self.assertFalse(util.prepareSequenceDataOp(inputObjectD={}))
        self.assertIn("KeyError", self.__log.getvalue())

    def testEvalSequenceData(self) -> None:
        dst = WfDataObject()
        dst.setContainerTypeName("value")
        dst.setValueTypeName("boolean")
        dst.setValue(True)
        util = SeqStatsUtils(verbose=True, log=self.__log)
        self.assertTrue(util.evalSequenceDataOp(**_kwArgs({"dst": dst})))
        self.assertIs(dst.getValue(), False)
        self.assertIn("return : False", self.__log.getvalue())

    def testEvalSequenceDataMissingDst(self) -> None:
        util = SeqStatsUtils(verbose=False, log=self.__log)
        self.assertFalse(util.evalSequenceDataOp(**_kwArgs()))

    def testUpdateOps(self) -> None:
        for opName in ("updateModelSequenceOp", "updateModelSequenceAssignOp"):
            with self.subTest(op=opName):
                log = io.StringIO()
                dst1 = _dstObj()
                util = SeqStatsUtils(verbose=True, log=log)
                self.assertTrue(getattr(util, opName)(**_kwArgs({"dst1": dst1})))
                dst1.getWorkflowInstanceId.assert_called_once_with()
                dst1.getDepositionDataSetId.assert_called_once_with()
                text = log.getvalue()
                self.assertIn("instance id : W_000123", text)
                self.assertIn("dep data id : D_000001", text)
                self.assertIn("fileSoure   : wf-instance", text)
                self.assertIn("/data/wf/D_000001/W_000123", text)
                self.assertIn("obsolete", text)

    def testUpdateOpsFailure(self) -> None:
        for opName in ("updateModelSequenceOp", "updateModelSequenceAssignOp"):
            with self.subTest(op=opName):
                dst1 = _dstObj()
                dst1.getDirPathReference.side_effect = ValueError("no path")
                util = SeqStatsUtils(verbose=False, log=io.StringIO())
                self.assertFalse(getattr(util, opName)(**_kwArgs({"dst1": dst1})))
                self.assertFalse(getattr(util, opName)(**_kwArgs()))


if __name__ == "__main__":
    unittest.main()

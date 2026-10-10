##
# File: DpUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the DpUtils plugin (RcsbDpUtility is mocked)"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.DpUtils import DpUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


def mockObj(filePath: Optional[str], dirPath: Optional[str] = None) -> MagicMock:
    wfo = MagicMock(spec=WfDataObject)
    wfo.getFilePathReference.return_value = filePath
    wfo.getDirPathReference.return_value = dirPath
    return wfo


class DpUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__tmp = self.__tmpDir.name
        self.__lfh = io.StringIO()
        self.__inp = os.path.join(self.__tmp, "model.cif")
        self.__out = os.path.join(self.__tmp, "out.cif")
        patcherDp = patch("wwpdb.utils.wf.plugins.DpUtils.RcsbDpUtility")
        patcherCi = patch("wwpdb.utils.wf.plugins.DpUtils.ConfigInfo")
        self.__mockDpCls = patcherDp.start()
        mockCiCls = patcherCi.start()
        mockCiCls.return_value.get.return_value = "TESTSITE"
        self.addCleanup(patcherDp.stop)
        self.addCleanup(patcherCi.stop)
        self.__dp = self.__mockDpCls.return_value

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def __args(self) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src": mockObj(self.__inp)},
            "outputObjectD": {"dst": mockObj(self.__out, self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def __checkCtor(self, du: DpUtils) -> None:
        self.__mockDpCls.assert_called_once_with(tmpPath=self.__tmp, siteId="TESTSITE", verbose=True, log=self.__lfh)
        self.assertIsNotNone(du)

    def testPolymerLinkageDistanceOp(self) -> None:
        du = DpUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.polymerLinkageDistanceOp(**self.__args()))
        self.__checkCtor(du)
        self.assertEqual(self.__dp.method_calls, [call.imp(self.__inp), call.op("annot-poly-link-dist"), call.exp(self.__out), call.cleanup()])
        self.assertIn("Distance file path: %s" % self.__out, self.__lfh.getvalue())

    def testCentreOfMassCalculation(self) -> None:
        du = DpUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.centreOfMassCalculation(**self.__args()))
        self.__checkCtor(du)
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.op("centre-of-mass"), call.expLog(os.path.join(self.__tmp, "centre-of-mass.log")), call.exp(self.__out), call.cleanup()],
        )

    def testGenerateComplexityOp(self) -> None:
        du = DpUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.generateComplexityOp(**self.__args()))
        self.__checkCtor(du)
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.op("annot-complexity"), call.expLog(os.path.join(self.__tmp, "generate-complexity.log")), call.exp(self.__out), call.cleanup()],
        )

    def testOpsReturnFalseOnException(self) -> None:
        self.__dp.op.side_effect = RuntimeError("boom")
        for opName in ["polymerLinkageDistanceOp", "centreOfMassCalculation", "generateComplexityOp"]:
            with self.subTest(op=opName):
                lfh = io.StringIO()
                du = DpUtils(verbose=False, log=lfh)
                self.assertFalse(getattr(du, opName)(**self.__args()))
                self.assertIn("RuntimeError: boom", lfh.getvalue())

    def testOpsReturnFalseOnMissingArgs(self) -> None:
        du = DpUtils(verbose=False, log=io.StringIO())
        for opName in ["polymerLinkageDistanceOp", "centreOfMassCalculation", "generateComplexityOp"]:
            with self.subTest(op=opName):
                self.assertFalse(getattr(du, opName)(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.__mockDpCls.assert_not_called()


if __name__ == "__main__":
    unittest.main()

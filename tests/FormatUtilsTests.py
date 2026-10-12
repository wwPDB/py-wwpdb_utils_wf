##
# File: FormatUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the FormatUtils plugin (RcsbDpUtility is mocked)"""

import io
import os
import sys
import tempfile
import unittest
from typing import TYPE_CHECKING, Any, Dict, Optional
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.FormatUtils import FormatUtils

if TYPE_CHECKING:
    from wwpdb.utils.wf.plugins.UtilsBase import PluginKwargs
from wwpdb.utils.wf.WfDataObject import WfDataObject


def mockObj(filePath: Optional[str], dirPath: Optional[str] = None) -> MagicMock:
    wfo = MagicMock(spec=WfDataObject)
    wfo.getFilePathReference.return_value = filePath
    wfo.getDirPathReference.return_value = dirPath
    return wfo


def valueObj() -> WfDataObject:
    wfo = WfDataObject()
    wfo.setContainerTypeName("value")
    wfo.setValueTypeName("string")
    return wfo


class FormatUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__tmp = self.__tmpDir.name
        self.__lfh = io.StringIO()
        self.__inp = os.path.join(self.__tmp, "input.file")
        self.__out = os.path.join(self.__tmp, "output.file")
        patcherDp = patch("wwpdb.utils.wf.plugins.FormatUtils.RcsbDpUtility")
        patcherCi = patch("wwpdb.utils.wf.plugins.FormatUtils.ConfigInfo")
        self.__mockDpCls = patcherDp.start()
        self.__mockCiCls = patcherCi.start()
        self.__mockCiCls.return_value.get.return_value = "TESTSITE"
        self.addCleanup(patcherDp.stop)
        self.addCleanup(patcherCi.stop)
        self.__dp = self.__mockDpCls.return_value

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def __args(self, uD: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src": mockObj(self.__inp)},
            "outputObjectD": {"dst": mockObj(self.__out, self.__tmp)},
            "userParameterD": uD if uD is not None else {},
            "internalParameterD": {},
        }

    def __checkCtor(self) -> None:
        self.__mockDpCls.assert_called_once_with(tmpPath=self.__tmp, siteId="TESTSITE", verbose=True, log=self.__lfh)
        self.__mockCiCls.return_value.get.assert_called_with("SITE_PREFIX")

    def testSimpleConversions(self) -> None:
        opD = {
            "pdbx2pdbOp": "annot-cif2pdb",
            "pdb2pdbxOp": "annot-pdb2cif",
            "pdb2pdbxDepositOp": "annot-pdb2cif-dep",
            "rcsb2pdbxOp": "annot-cif2cif",
            "pdbx2pdbxDepositOp": "annot-cif2cif-dep",
        }
        for opName, dpOp in opD.items():
            with self.subTest(op=opName):
                self.__mockDpCls.reset_mock()
                fu = FormatUtils(verbose=True, log=self.__lfh)
                self.assertTrue(getattr(fu, opName)(**self.__args()))
                self.__checkCtor()
                self.assertEqual(self.__dp.method_calls, [call.imp(self.__inp), call.op(dpOp), call.exp(self.__out), call.cleanup()])

    def testNmrstar2pdbxOp(self) -> None:
        fu = FormatUtils(verbose=True, log=self.__lfh)
        self.assertTrue(fu.nmrstar2pdbxOp(**self.__args({"data_set_id": "D_000001"})))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.addInput(name="data_set_id", value="D_000001"), call.op("annot-nmrstar2pdbx"), call.exp(self.__out), call.cleanup()],
        )

    def testNmrstar2pdbxOpMissingParam(self) -> None:
        fu = FormatUtils(verbose=False, log=self.__lfh)
        self.assertFalse(fu.nmrstar2pdbxOp(**self.__args()))
        self.assertIn("KeyError", self.__lfh.getvalue())

    def testPdbx2nmrstarAnnotOp(self) -> None:
        fu = FormatUtils(verbose=True, log=self.__lfh)
        self.assertTrue(fu.pdbx2nmrstarAnnotOp(**self.__args({"data_set_id": "1ABC"})))
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.addInput(name="pdb_id", value="1ABC"), call.op("annot-pdbx2nmrstar"), call.exp(self.__out), call.cleanup()],
        )

    def testPdbx2nmrstarAnnotOpRejectsSwappedObjects(self) -> None:
        # Regression test: the op used to read its source from outputObjectD["src"] and its destination from
        # inputObjectD["dst"].  That swapped layout must now fail, since there is no inputObjectD["src"]
        fu = FormatUtils(verbose=True, log=self.__lfh)
        args: PluginKwargs = {
            "inputObjectD": {"dst": mockObj(self.__out)},
            "outputObjectD": {"src": mockObj(self.__inp), "dst": mockObj(None, self.__tmp)},
            "userParameterD": {"data_set_id": "1ABC"},
            "internalParameterD": {},
        }
        self.assertFalse(fu.pdbx2nmrstarAnnotOp(**args))
        self.assertIn("KeyError", self.__lfh.getvalue())
        self.__dp.op.assert_not_called()

    def __mtzArgs(self, uD: Dict[str, Any], xyzPath: Optional[str], status: WfDataObject) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src1": mockObj(os.path.join(self.__tmp, "sf.mtz")), "src2": mockObj(xyzPath)},
            "outputObjectD": {
                "dst1": mockObj(os.path.join(self.__tmp, "sf.cif"), self.__tmp),
                "dst2": mockObj(os.path.join(self.__tmp, "diag.log")),
                "dst3": mockObj(os.path.join(self.__tmp, "convert.log")),
                "dst4": status,
            },
            "userParameterD": uD,
            "internalParameterD": {},
        }

    def __writeLog(self, content: str) -> None:
        with open(os.path.join(self.__tmp, "convert.log"), "w") as ofh:
            ofh.write(content)

    def testMtz2pdbxOpFull(self) -> None:
        xyzPath = os.path.join(self.__tmp, "model.cif")
        with open(xyzPath, "w") as ofh:
            ofh.write("data_x\n")
        self.__writeLog("conversion complete\n")
        status = valueObj()
        fu = FormatUtils(verbose=True, log=self.__lfh)
        self.assertTrue(fu.mtz2pdbxOp(**self.__mtzArgs({"timeout": "30", "firstblockdiags": "Y"}, xyzPath, status)))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.imp(os.path.join(self.__tmp, "sf.mtz")),
                call.addInput(name="xyz_file_path", value=xyzPath, type="file"),
                call.setTimeout(30),
                call.addInput(name="firstblockdiags", value=True, type="param"),
                call.op("annot-sf-convert"),
                call.expLog(os.path.join(self.__tmp, "convert.log")),
                call.expList(dstPathList=[os.path.join(self.__tmp, "sf.cif"), os.path.join(self.__tmp, "diag.log"), os.path.join(self.__tmp, "mtzdmp.log")]),
                call.cleanup(),
            ],
        )
        self.assertEqual(status.getValue(), "ok")

    def testMtz2pdbxOpMinimal(self) -> None:
        # No coordinate file, no timeout, no first block option
        self.__writeLog("++WARN: something odd\n")
        status = valueObj()
        fu = FormatUtils(verbose=False, log=self.__lfh)
        self.assertTrue(fu.mtz2pdbxOp(**self.__mtzArgs({"timeout": "0"}, os.path.join(self.__tmp, "missing.cif"), status)))
        calledNames = [c[0] for c in self.__dp.method_calls]
        self.assertNotIn("addInput", calledNames)
        self.assertNotIn("setTimeout", calledNames)
        self.assertEqual(status.getValue(), "warn")

    def testMtz2pdbxOpStatus(self) -> None:
        cases = [
            ("info\n++ERROR bad data\n", "error"),
            ("ERROR: bad\n", "error"),
            ("warn: lower case\n", "warn"),
            ("error: first\nWARN: second\n", "error"),
            ("all good\n", "ok"),
            (None, "error"),
        ]
        for content, expected in cases:
            with self.subTest(content=content):
                logPath = os.path.join(self.__tmp, "convert.log")
                if os.path.exists(logPath):
                    os.remove(logPath)
                if content is not None:
                    self.__writeLog(content)
                status = valueObj()
                fu = FormatUtils(verbose=False, log=self.__lfh)
                self.assertTrue(fu.mtz2pdbxOp(**self.__mtzArgs({"timeout": "0", "firstblockdiags": "N"}, None, status)))
                self.assertEqual(status.getValue(), expected)

    def testMtz2pdbxOpBadTimeout(self) -> None:
        fu = FormatUtils(verbose=False, log=self.__lfh)
        self.assertFalse(fu.mtz2pdbxOp(**self.__mtzArgs({"timeout": "soon"}, None, valueObj())))
        self.__mockDpCls.assert_not_called()

    def testOpsReturnFalseOnException(self) -> None:
        self.__dp.op.side_effect = RuntimeError("dp failure")
        opL = ["pdbx2pdbOp", "pdb2pdbxOp", "pdb2pdbxDepositOp", "rcsb2pdbxOp", "pdbx2pdbxDepositOp", "nmrstar2pdbxOp"]
        for opName in opL:
            with self.subTest(op=opName):
                lfh = io.StringIO()
                fu = FormatUtils(verbose=False, log=lfh)
                self.assertFalse(getattr(fu, opName)(**self.__args({"data_set_id": "D_000001"})))
                self.assertIn("RuntimeError: dp failure", lfh.getvalue())
        fu = FormatUtils(verbose=False, log=io.StringIO())
        self.assertFalse(fu.mtz2pdbxOp(**self.__mtzArgs({"timeout": "0"}, None, valueObj())))

    def testOpsReturnFalseOnMissingArgs(self) -> None:
        fu = FormatUtils(verbose=False, log=io.StringIO())
        opL = ["pdbx2pdbOp", "pdb2pdbxOp", "pdb2pdbxDepositOp", "rcsb2pdbxOp", "pdbx2pdbxDepositOp", "mtz2pdbxOp", "nmrstar2pdbxOp", "pdbx2nmrstarAnnotOp"]
        for opName in opL:
            with self.subTest(op=opName):
                self.assertFalse(getattr(fu, opName)(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.__mockDpCls.assert_not_called()


if __name__ == "__main__":
    unittest.main()

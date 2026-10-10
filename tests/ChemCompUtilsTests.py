##
# File: ChemCompUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the ChemCompUtils plugin (RcsbDpUtility, IoAdapterCore, PathInfo and MetalCoordinationUtility are mocked)"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.ChemCompUtils import ChemCompUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODNAME = "wwpdb.utils.wf.plugins.ChemCompUtils"


def mockObj(filePath: Optional[str], dirPath: Optional[str] = None, depId: Optional[str] = None) -> MagicMock:
    wfo = MagicMock(spec=WfDataObject)
    wfo.getFilePathReference.return_value = filePath
    wfo.getDirPathReference.return_value = dirPath
    wfo.getDepositionDataSetId.return_value = depId
    wfo.getWorkflowInstanceId.return_value = "W_000001"
    wfo.getStorageType.return_value = "wf-instance"
    return wfo


def fakeCategory(rows: List[Dict[str, Optional[str]]]) -> MagicMock:
    cat = MagicMock()
    cat.getRowCount.return_value = len(rows)

    def getValue(attributeName: str, rowIndex: int) -> Optional[str]:
        return rows[rowIndex].get(attributeName)

    cat.getValue.side_effect = getValue
    return cat


def fakeContainer(catD: Dict[str, MagicMock]) -> MagicMock:
    cont = MagicMock()
    cont.getObj.side_effect = catD.get
    return cont


class ChemCompUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__tmp = self.__tmpDir.name
        self.__lfh = io.StringIO()
        self.__model = os.path.join(self.__tmp, "model.cif")
        self.__link = os.path.join(self.__tmp, "cc-link.cif")
        self.__assign = os.path.join(self.__tmp, "cc-assign.cif")
        patchers = {
            "dp": patch(MODNAME + ".RcsbDpUtility"),
            "ci": patch(MODNAME + ".ConfigInfo"),
            "io": patch(MODNAME + ".IoAdapterCore"),
            "pi": patch(MODNAME + ".PathInfo"),
            "metal": patch(MODNAME + ".MetalCoordinationUtility"),
        }
        self.__m: Dict[str, MagicMock] = {}
        for name, p in patchers.items():
            self.__m[name] = p.start()
            self.addCleanup(p.stop)
        self.__m["ci"].return_value.get.return_value = "TESTSITE"
        self.__m["pi"].return_value.getFilePath.side_effect = lambda depId, **kw: "/%s/%s.%s" % (depId, kw["contentType"], kw["formatType"])
        self.__dp = self.__m["dp"].return_value
        self.__metal = self.__m["metal"].return_value
        self.__readD: Dict[str, List[MagicMock]] = {}
        self.__m["io"].return_value.readFile.side_effect = lambda inputFilePath, selectList, outDirPath: self.__readD.get(inputFilePath, [])  # noqa: ARG005

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def __touch(self, fp: str) -> None:
        with open(fp, "w") as ofh:
            ofh.write("data_x\n")

    def __args2(self) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src1": mockObj(self.__model, depId="D_000001"), "src2": mockObj(self.__link)},
            "outputObjectD": {"dst": mockObj(self.__assign, self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def __args1(self) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src": mockObj(self.__model, depId="D_000001")},
            "outputObjectD": {"dst": mockObj(self.__assign, self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def __checkCtor(self) -> None:
        self.__m["dp"].assert_called_once_with(tmpPath=self.__tmp, siteId="TESTSITE", verbose=True, log=self.__lfh)

    def testChemCompLinkOp(self) -> None:
        cc = ChemCompUtils(verbose=True, log=self.__lfh)
        self.assertTrue(cc.chemCompLinkOp(**self.__args1()))
        self.__checkCtor()
        self.assertEqual(self.__dp.method_calls, [call.imp(self.__model), call.op("chem-comp-link"), call.exp(self.__assign), call.cleanup()])

    def testChemCompAssignOpWithLink(self) -> None:
        self.__touch(self.__link)
        cc = ChemCompUtils(verbose=True, log=self.__lfh)
        self.assertTrue(cc.chemCompAssignOp(**self.__args2()))
        self.__checkCtor()
        # No cleanup - working directory must be preserved
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.setWorkingDir(os.path.join(self.__tmp, "assign")),
                call.addInput(name="id", value="D_000001"),
                call.addInput(name="cc_link_file_path", value=self.__link, type="file"),
                call.imp(self.__model),
                call.op("chem-comp-assign"),
                call.exp(self.__assign),
            ],
        )
        # Assignment file not produced (exp mocked) - no metal coordination
        self.__m["io"].assert_not_called()
        self.__m["metal"].assert_not_called()

    def testChemCompAssignOpsWithoutLink(self) -> None:
        cases = [
            ("chemCompAssignOp", self.__args2(), "chem-comp-assign"),
            ("chemCompAssignUIOp", self.__args2(), "chem-comp-assign"),
            ("chemCompAssignNLOp", self.__args1(), "chem-comp-assign"),
            ("chemCompAssignNLUIOp", self.__args1(), "chem-comp-assign"),
            ("chemCompAssignExactOp", self.__args2(), "chem-comp-assign-exact"),
            ("chemCompAssignExactNLOp", self.__args1(), "chem-comp-assign-exact"),
        ]
        for opName, args, dpOp in cases:
            with self.subTest(op=opName):
                self.__m["dp"].reset_mock()
                cc = ChemCompUtils(verbose=True, log=self.__lfh)
                self.assertTrue(getattr(cc, opName)(**args))
                self.__checkCtor()
                self.assertEqual(
                    self.__dp.method_calls,
                    [
                        call.setWorkingDir(os.path.join(self.__tmp, "assign")),
                        call.addInput(name="id", value="D_000001"),
                        call.imp(self.__model),
                        call.op(dpOp),
                        call.exp(self.__assign),
                    ],
                )

    def testChemCompAssignWithLinkVariants(self) -> None:
        self.__touch(self.__link)
        for opName in ["chemCompAssignUIOp", "chemCompAssignExactOp"]:
            with self.subTest(op=opName):
                self.__m["dp"].reset_mock()
                cc = ChemCompUtils(verbose=False, log=self.__lfh)
                self.assertTrue(getattr(cc, opName)(**self.__args2()))
                self.assertIn(call.addInput(name="cc_link_file_path", value=self.__link, type="file"), self.__dp.method_calls)

    def testChemCompInstanceUpdateOp(self) -> None:
        self.__touch(self.__assign)
        out = os.path.join(self.__tmp, "model-out.cif")
        args = {
            "inputObjectD": {"src1": mockObj(self.__model), "src2": mockObj(self.__assign)},
            "outputObjectD": {"dst": mockObj(out, self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }
        cc = ChemCompUtils(verbose=True, log=self.__lfh)
        self.assertTrue(cc.chemCompInstanceUpdateOp(**args))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [call.addInput(name="cc_assign_file_path", value=self.__assign, type="file"), call.imp(self.__model), call.op("chem-comp-instance-update"), call.exp(out)],
        )

    def testChemCompInstanceUpdateOpNoAssignFile(self) -> None:
        args = {
            "inputObjectD": {"src1": mockObj(self.__model), "src2": mockObj(None)},
            "outputObjectD": {"dst": mockObj(self.__assign, self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertTrue(cc.chemCompInstanceUpdateOp(**args))
        self.__dp.addInput.assert_not_called()

    def testOpsReturnFalseOnException(self) -> None:
        self.__dp.op.side_effect = RuntimeError("dp failure")
        cases = [
            ("chemCompLinkOp", self.__args1()),
            ("chemCompAssignOp", self.__args2()),
            ("chemCompAssignUIOp", self.__args2()),
            ("chemCompAssignNLOp", self.__args1()),
            ("chemCompAssignNLUIOp", self.__args1()),
            ("chemCompAssignExactOp", self.__args2()),
            ("chemCompAssignExactNLOp", self.__args1()),
            ("chemCompInstanceUpdateOp", self.__args2()),
        ]
        for opName, args in cases:
            with self.subTest(op=opName):
                lfh = io.StringIO()
                cc = ChemCompUtils(verbose=False, log=lfh)
                self.assertFalse(getattr(cc, opName)(**args))
                self.assertIn("RuntimeError: dp failure", lfh.getvalue())

    def testOpsReturnFalseOnMissingArgs(self) -> None:
        cc = ChemCompUtils(verbose=False, log=io.StringIO())
        opL = [
            "chemCompLinkOp",
            "chemCompAssignOp",
            "chemCompAssignUIOp",
            "chemCompAssignNLOp",
            "chemCompAssignNLUIOp",
            "chemCompAssignExactOp",
            "chemCompAssignExactNLOp",
            "chemCompInstanceUpdateOp",
        ]
        for opName in opL:
            with self.subTest(op=opName):
                self.assertFalse(getattr(cc, opName)(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.__m["dp"].assert_not_called()

    # --- metal coordination follow-up (run after chem-comp-assign when the assignment file exists) ---

    def __setAssign(self, metalIds: List[Optional[str]], status: Optional[str] = None) -> None:
        self.__touch(self.__assign)
        catD = {"pdbx_polyatomic_metal_ccd": fakeCategory([{"id": v} for v in metalIds])}
        if status is not None:
            catD["pdbx_entry_info"] = fakeCategory([{"status": status}])
        self.__readD[self.__assign] = [fakeContainer(catD)]

    def __setModelTasks(self, tasks: List[str]) -> None:
        self.__readD[self.__model] = [fakeContainer({"pdbx_data_processing_status": fakeCategory([{"task_name": t} for t in tasks])})]

    def __checkMetalRun(self, noTimeOutFlag: bool, ids: List[str]) -> None:
        self.__m["metal"].assert_called_once_with(wrkPath=self.__tmp, siteId="TESTSITE", verbose=False, log=self.__lfh)
        self.assertEqual(
            self.__metal.method_calls,
            [
                call.setModelCoordinatesFilePath(self.__model),
                call.setPolyAtomicMetalLigandIdList(ids),
                call.setFindGeoOutputFilePath("/D_000001/findgeo-annotation.json"),
                call.setMetalCoordOutputFilePath("/D_000001/metalcoord-annotation.json"),
                call.run(noTimeOutFlag=noTimeOutFlag, regularFilter="-filter-regular"),
            ],
        )
        self.__m["pi"].return_value.getFilePath.assert_any_call(
            "D_000001", wfInstanceId="W_000001", contentType="findgeo-annotation", formatType="json", fileSource="wf-instance", versionId="next"
        )

    def testMetalCoordinationAutoRuns(self) -> None:
        self.__setAssign(["MO1", ".", "?", None, "FE4"], status="TIMEOUT")
        self.__setModelTasks(["chem comp assign"])
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertTrue(cc.chemCompAssignOp(**self.__args2()))
        self.__m["io"].return_value.readFile.assert_any_call(inputFilePath=self.__assign, selectList=["pdbx_entry_info", "pdbx_polyatomic_metal_ccd"], outDirPath=self.__tmp)
        self.__m["io"].return_value.readFile.assert_any_call(inputFilePath=self.__model, selectList=["pdbx_data_processing_status"], outDirPath=self.__tmp)
        self.__checkMetalRun(False, ["MO1", "FE4"])

    def testMetalCoordinationAutoNoEntryInfo(self) -> None:
        self.__setAssign(["MO1"])
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertTrue(cc.chemCompAssignNLOp(**self.__args1()))
        self.__checkMetalRun(False, ["MO1"])

    def testMetalCoordinationAutoSkippedWhenStatusOk(self) -> None:
        self.__setAssign(["MO1"], status="OK")
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertTrue(cc.chemCompAssignOp(**self.__args2()))
        self.__m["metal"].assert_not_called()

    def testMetalCoordinationAutoSkippedWhenAlreadyRun(self) -> None:
        self.__setAssign(["MO1"], status="TIMEOUT")
        self.__setModelTasks(["chem comp assign", "metal coordination"])
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertTrue(cc.chemCompAssignNLOp(**self.__args1()))
        self.__m["metal"].assert_not_called()

    def testMetalCoordinationUiIgnoresStatus(self) -> None:
        for opName, args in [("chemCompAssignUIOp", self.__args2()), ("chemCompAssignNLUIOp", self.__args1())]:
            with self.subTest(op=opName):
                self.__m["metal"].reset_mock()
                self.__m["pi"].return_value.getFilePath.reset_mock()
                self.__setAssign(["MO1"], status="OK")
                self.__setModelTasks(["metal coordination"])
                cc = ChemCompUtils(verbose=False, log=self.__lfh)
                self.assertTrue(getattr(cc, opName)(**args))
                self.__checkMetalRun(True, ["MO1"])

    def testMetalCoordinationSkippedWithoutMetals(self) -> None:
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        # Empty read result
        self.__touch(self.__assign)
        self.assertTrue(cc.chemCompAssignUIOp(**self.__args2()))
        # Category present but only placeholder values
        self.__setAssign([".", "?"])
        self.assertTrue(cc.chemCompAssignUIOp(**self.__args2()))
        # Category absent
        self.__readD[self.__assign] = [fakeContainer({})]
        self.assertTrue(cc.chemCompAssignUIOp(**self.__args2()))
        self.__m["metal"].assert_not_called()

    def testMetalCoordinationFailureReturnsFalse(self) -> None:
        self.__setAssign(["MO1"])
        self.__metal.run.side_effect = RuntimeError("metal failure")
        cc = ChemCompUtils(verbose=False, log=self.__lfh)
        self.assertFalse(cc.chemCompAssignUIOp(**self.__args2()))
        self.assertIn("metal failure", self.__lfh.getvalue())


if __name__ == "__main__":
    unittest.main()

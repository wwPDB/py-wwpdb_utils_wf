##
# File: NmrUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the NmrUtils workflow plugin

NmrDpUtility (wwpdb.utils.nmr) and NmrChemShiftProcessUtils (wwpdb.apps.ann_tasks_v2) are optional packages
imported at module load inside contextlib.suppress(), so they are patched as module-level names with create=True.
"""

import io
import json
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.wf.plugins.NmrUtils import NmrUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODULE = "wwpdb.utils.wf.plugins.NmrUtils"
CONF = {"nonblk_anomalous_cs": True, "max_count": 3}


def _dataObj(filePath: Optional[str] = None, dirPath: Optional[str] = None, value: Any = None) -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    obj.getDirPathReference.return_value = dirPath
    obj.getValue.return_value = value
    return obj


class NmrUtilsTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.dirPath = self.tmpDir.name
        self.log = io.StringIO()
        self.siteId = ConfigInfo().get("SITE_PREFIX")

    def tearDown(self) -> None:
        self.tmpDir.cleanup()

    def path(self, name: str) -> str:
        return os.path.join(self.dirPath, name)

    def write(self, name: str, content: str) -> str:
        fPath = self.path(name)
        with open(fPath, "w") as ofh:
            ofh.write(content)
        return fPath

    def kwArgs(self, inp: Dict[str, Any], out: Dict[str, Any]) -> Dict[str, Any]:
        """Builds op arguments; plain strings become file references in the temp dir"""
        inpD = {k: (v if isinstance(v, MagicMock) else _dataObj(v, self.dirPath)) for k, v in inp.items()}
        outD = {k: (v if isinstance(v, (MagicMock, WfDataObject)) else _dataObj(v, self.dirPath)) for k, v in out.items()}
        return {"inputObjectD": inpD, "outputObjectD": outD, "userParameterD": {}, "internalParameterD": {}}

    def valueObj(self) -> WfDataObject:
        obj = WfDataObject()
        obj.setContainerTypeName("value")
        return obj


class RcsbDpOpsTests(NmrUtilsTestBase):
    """Deprecated chemical shift operations implemented with RcsbDpUtility and PdbxChemShiftReport"""

    def setUp(self) -> None:
        super().setUp()
        dpPatch = patch(MODULE + ".RcsbDpUtility")
        csrPatch = patch(MODULE + ".PdbxChemShiftReport")
        self.mockDp = dpPatch.start()
        self.mockCsr = csrPatch.start()
        self.addCleanup(dpPatch.stop)
        self.addCleanup(csrPatch.stop)
        csr = self.mockCsr.return_value
        csr.getStatus.return_value = ["WARN", "ING"]
        csr.getWarnings.return_value = ["warning 1", "warning 2"]
        csr.getErrors.return_value = []

    def _assertReport(self, chkPath: str, dsts: List[WfDataObject]) -> None:
        self.mockCsr.assert_called_once_with(inputPath=chkPath, verbose=True, log=self.log)
        self.assertEqual(dsts[0].getValue(), "warning")
        self.assertEqual(dsts[1].getValue(), ["warning 1", "warning 2"])
        self.assertEqual(dsts[2].getValue(), [])

    def _uploadCalls(self, csList: List[str], nameList: List[str], chkPath: str, csOut: str) -> List[Any]:
        return [
            call.setDebugMode(flag=True),
            call.addInput(name="chemical_shifts_file_path_list", value=csList),
            call.addInput(name="chemical_shifts_auth_file_name_list", value=nameList),
            call.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath),
            call.op("annot-chem-shifts-upload-check"),
            call.expLog(self.path("upload-chemical-shift-check.log")),
            call.exp(csOut),
            call.cleanup(),
        ]

    def testUploadChemicalShift(self) -> None:
        csList = ["/data/cs1.str", "/data/cs2.str"]
        nameList = ["a.str", "b.str"]
        dsts = [self.valueObj() for _ in range(3)]
        kw = self.kwArgs(
            {"src1": _dataObj(value=csList), "src2": _dataObj(value=nameList)},
            {"dst1": self.path("cs.cif"), "dst2": self.path("chk.cif"), "dst3": dsts[0], "dst4": dsts[1], "dst5": dsts[2]},
        )
        util = NmrUtils(verbose=True, log=self.log)
        self.assertTrue(util.uploadChemicalShiftOp(**kw))
        self.mockDp.assert_called_once_with(tmpPath=self.dirPath, siteId=self.siteId, verbose=True, log=self.log)
        self.assertEqual(self.mockDp.return_value.method_calls, self._uploadCalls(csList, nameList, self.path("chk.cif"), self.path("cs.cif")))
        self._assertReport(self.path("chk.cif"), dsts)
        self.assertIn("Warning count : 2", self.log.getvalue())

    def testUploadChemicalShiftAlt(self) -> None:
        csListPath = self.write("cs-list.txt", "/data/cs1.str\n /data/cs2.str \n")
        nameListPath = self.write("name-list.txt", "a.str\nb.str\n")
        kw = self.kwArgs({"src1": csListPath, "src2": nameListPath}, {"dst1": self.path("cs.cif"), "dst2": self.path("chk.cif")})
        util = NmrUtils(verbose=True, log=self.log)
        self.assertTrue(util.uploadChemicalShiftAltOp(**kw))
        expected = self._uploadCalls(["/data/cs1.str", "/data/cs2.str"], ["a.str", "b.str"], self.path("chk.cif"), self.path("cs.cif"))
        self.assertEqual(self.mockDp.return_value.method_calls, expected)
        self.mockCsr.assert_not_called()

    def _atomNameCalls(self) -> List[Any]:
        return [
            call.imp("/data/cs.cif"),
            call.addInput(name="coordinate_file_path", value="/data/xyz.cif"),
            call.addInput(name="chemical_shifts_coord_check_file_path", value=self.path("chk.cif")),
            call.op("annot-chem-shifts-atom-name-check"),
            call.expLog(self.path("atom-name-check-cs-xyz.log")),
            call.exp(self.path("cs-out.cif")),
            call.cleanup(),
        ]

    def testAtomNameCheckCsXyz(self) -> None:
        dsts = [self.valueObj() for _ in range(3)]
        kw = self.kwArgs(
            {"src1": "/data/cs.cif", "src2": "/data/xyz.cif"},
            {"dst1": self.path("cs-out.cif"), "dst2": self.path("chk.cif"), "dst3": dsts[0], "dst4": dsts[1], "dst5": dsts[2]},
        )
        util = NmrUtils(verbose=True, log=self.log)
        self.assertTrue(util.atomNameCheckCsXyzOp(**kw))
        self.assertEqual(self.mockDp.return_value.method_calls, self._atomNameCalls())
        self._assertReport(self.path("chk.cif"), dsts)

    def testAtomNameCheckCsXyzAlt(self) -> None:
        kw = self.kwArgs({"src1": "/data/cs.cif", "src2": "/data/xyz.cif"}, {"dst1": self.path("cs-out.cif"), "dst2": self.path("chk.cif")})
        util = NmrUtils(verbose=True, log=self.log)
        self.assertTrue(util.atomNameCheckCsXyzAltOp(**kw))
        self.assertEqual(self.mockDp.return_value.method_calls, self._atomNameCalls())
        self.assertIn("Report file path:       %s" % self.path("chk.cif"), self.log.getvalue())

    def testFailures(self) -> None:
        self.mockDp.return_value.op.side_effect = RuntimeError("dp failed")
        full: Dict[str, Any] = {"dst1": self.path("o1"), "dst2": self.path("o2"), "dst3": self.valueObj(), "dst4": self.valueObj(), "dst5": self.valueObj()}
        cases: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = [
            ("uploadChemicalShiftOp", {"src1": _dataObj(value=[]), "src2": _dataObj(value=[])}, full),
            ("uploadChemicalShiftAltOp", {"src1": self.write("l1", ""), "src2": self.write("l2", "")}, full),
            ("uploadChemicalShiftAltOp", {"src1": self.path("missing"), "src2": self.path("missing")}, full),
            ("atomNameCheckCsXyzOp", {"src1": "/cs", "src2": "/xyz"}, full),
            ("atomNameCheckCsXyzAltOp", {"src1": "/cs", "src2": "/xyz"}, full),
        ]
        for opName, inp, out in cases:
            with self.subTest(op=opName, inp=sorted(inp)):
                log = io.StringIO()
                util = NmrUtils(verbose=False, log=log)
                self.assertFalse(getattr(util, opName)(**self.kwArgs(inp, out)))
                self.assertIn("Error", log.getvalue())
        self.mockDp.return_value.cleanup.assert_not_called()


class ChemShiftProcessUtilsTests(NmrUtilsTestBase):
    @patch(MODULE + ".NmrChemShiftProcessUtils", create=True)
    def testAutoChemShiftProcess(self, mockUtil: MagicMock) -> None:
        out = {"dst%d" % i: self.path("out%d" % i) for i in range(1, 9)}
        kw = self.kwArgs({"src1": "/data/xyz.cif", "src2": "/data/cs.cif"}, out)
        util = NmrUtils(verbose=False, log=self.log)
        self.assertTrue(util.autoChemShiftProcessOp(**kw))
        mockUtil.assert_called_once_with(siteId=self.siteId, verbose=False, log=self.log)
        self.assertEqual(
            mockUtil.return_value.method_calls,
            [
                call.setWorkingDirPath(dirPath=self.dirPath),
                call.setInputModelFileName(fileName="/data/xyz.cif"),
                call.setInputCsFileName(fileName="/data/cs.cif"),
                call.setOutputModelFileName(fileName=out["dst1"]),
                call.setOutputCsFileName(fileName=out["dst2"]),
                call.setOutputReportFileName(fileName=out["dst8"]),
                call.setOutputValidationFileList(dstPathList=[out["dst3"], out["dst4"], out["dst5"], out["dst6"], out["dst7"]]),
                call.run(),
            ],
        )

    @patch(MODULE + ".NmrChemShiftProcessUtils", create=True)
    def testAutoNmrNefProcess(self, mockUtil: MagicMock) -> None:
        kw = self.kwArgs({"src1": "/data/xyz.cif", "src2": "/data/in.nef"}, {"dst1": self.path("xyz.cif"), "dst2": self.path("out.nef")})
        util = NmrUtils(verbose=False, log=self.log)
        self.assertTrue(util.autoNmrNefProcessOp(**kw))
        self.assertEqual(
            mockUtil.return_value.method_calls,
            [
                call.setWorkingDirPath(dirPath=self.dirPath),
                call.setInputModelFileName(fileName="/data/xyz.cif"),
                call.setInputNefFileName(fileName="/data/in.nef"),
                call.setOutputModelFileName(fileName=self.path("xyz.cif")),
                call.setOutputNefFileName(fileName=self.path("out.nef")),
                call.runNefProcess(),
            ],
        )

    @patch(MODULE + ".NmrChemShiftProcessUtils", create=True)
    def testFailures(self, mockUtil: MagicMock) -> None:
        mockUtil.return_value.run.side_effect = RuntimeError("run failed")
        mockUtil.return_value.runNefProcess.side_effect = RuntimeError("nef failed")
        util = NmrUtils(verbose=False, log=self.log)
        out = {"dst%d" % i: self.path("out%d" % i) for i in range(1, 9)}
        self.assertFalse(util.autoChemShiftProcessOp(**self.kwArgs({"src1": "/x", "src2": "/c"}, out)))
        self.assertFalse(util.autoNmrNefProcessOp(**self.kwArgs({"src1": "/x", "src2": "/n"}, out)))
        self.assertFalse(util.autoChemShiftProcessOp(**self.kwArgs({"src1": "/x", "src2": "/c"}, {"dst1": "/o"})))
        text = self.log.getvalue()
        self.assertIn("run failed", text)
        self.assertIn("nef failed", text)
        self.assertIn("KeyError", text)


class NmrDpUtilityOpsTests(NmrUtilsTestBase):
    """Operations implemented with wwpdb.utils.nmr NmrDpUtility"""

    def setUp(self) -> None:
        super().setUp()
        dpPatch = patch(MODULE + ".NmrDpUtility", create=True)
        self.mockDp = dpPatch.start()
        self.addCleanup(dpPatch.stop)
        self.dp = self.mockDp.return_value
        self.dp.op.return_value = True
        self.confPath = self.write("conf.json", json.dumps(CONF))
        self.authPath = self.write("auth.txt", "orig.str\nsecond.str\n")

    def _confCalls(self) -> List[Any]:
        return [call.addInput(name="nonblk_anomalous_cs", value=True, type="param"), call.addInput(name="max_count", value=3, type="param")]

    def _run(self, opName: str, inp: Dict[str, Any], out: Dict[str, Any], verbose: bool = True) -> Any:
        util = NmrUtils(verbose=verbose, log=self.log)
        ret = getattr(util, opName)(**self.kwArgs(inp, out))
        if ret:
            self.mockDp.assert_called_once_with(verbose=verbose, log=self.log)
        return ret

    def _cases(self, conf: bool) -> List[Any]:
        """(opName, inputs, outputs, expected NmrDpUtility method calls)"""
        c = self._confCalls() if conf else []
        cnf = self.confPath if conf else self.path("no-conf.json")
        o = self.path
        return [
            (
                "nefConsistencyCheckOp",
                {"src0": cnf, "src1": "/in.nef", "src2": "/model.cif", "prc2": "/prc.cif"},
                {"dst": o("rep.json")},
                [
                    call.setSource("/in.nef"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                ]
                + c
                + [call.setLog(o("rep.json")), call.op("nmr-nef-consistency-check")],
            ),
            (
                "strConsistencyCheckOp",
                {"src0": cnf, "src1": "/in.str", "src2": "/model.cif", "prc2": "/prc.cif"},
                {"dst": o("rep.json")},
                [
                    call.setSource("/in.str"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                ]
                + c
                + [call.setLog(o("rep.json")), call.op("nmr-str-consistency-check")],
            ),
            (
                "mrgConsistencyCheckOp",
                {"src0": cnf, "src1": "/in.str", "src2": "/model.cif", "prc2": "/prc.cif", "src3": "/in.json"},
                {"dst": o("rep.json")},
                [
                    call.setSource("/in.str"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="report_file_path", value="/in.json", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                ]
                + c
                + [call.setLog(o("rep.json")), call.op("nmr-str-consistency-check")],
            ),
            (
                "nef2strDepositOp",
                {"src0": cnf, "src1": "/in.nef", "src2": "/model.cif", "prc2": "/prc.cif", "src3": "/in.json"},
                {"dst1": o("out.nef"), "dst2": o("out.str"), "dst3": o("nef.json"), "dst4": o("str.json")},
                [
                    call.setSource("/in.nef"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                    call.addInput(name="report_file_path", value="/in.json", type="file"),
                ]
                + c
                + [
                    call.setDestination(o("out.nef")),
                    call.addOutput(name="nmr-star_file_path", value=o("out.str"), type="file"),
                    call.addOutput(name="report_file_path", value=o("str.json"), type="file"),
                    call.addOutput(name="leave_intl_note", value=False, type="param"),
                    call.setLog(o("nef.json")),
                    call.op("nmr-nef2str-deposit"),
                ],
            ),
            (
                "nef2cifDepositOp",
                {"src0": cnf, "src1": "/in.nef", "src2": self.authPath, "src3": "/model.cif", "prc3": "/prc.cif", "src4": "/in.json"},
                {"dst%d" % i: o("out%d" % i) for i in range(1, 7)},
                [
                    call.setSource("/in.nef", "orig.str"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                    call.addInput(name="report_file_path", value="/in.json", type="file"),
                ]
                + c
                + [
                    call.setDestination(o("out1")),
                    call.addOutput(name="nmr-star_file_path", value=o("out2"), type="file"),
                    call.addOutput(name="nmr_cif_file_path", value=o("out3"), type="file"),
                    call.addOutput(name="report_file_path", value=o("out5"), type="file"),
                    call.addOutput(name="leave_intl_note", value=False, type="param"),
                    call.addOutput(name="nmrif_file_path", value=o("out6"), type="file"),
                    call.setLog(o("out4")),
                    call.op("nmr-nef2cif-deposit"),
                ],
            ),
            (
                "str2strDepositOp",
                {"src0": cnf, "src1": "/in.str", "src2": "/model.cif", "prc2": "/prc.cif", "src3": "/in.json"},
                {"dst1": o("out.str"), "dst2": o("out.json")},
                [
                    call.setSource("/in.str"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                    call.addInput(name="report_file_path", value="/in.json", type="file"),
                ]
                + c
                + [
                    call.setDestination(o("out.str")),
                    call.addOutput(name="leave_intl_note", value=False, type="param"),
                    call.setLog(o("out.json")),
                    call.op("nmr-str2str-deposit"),
                ],
            ),
            (
                "str2cifDepositOp",
                {"src0": cnf, "src1": "/in.str", "src2": self.authPath, "src3": "/model.cif", "prc3": "/prc.cif", "src4": "/in.json"},
                {"dst%d" % i: o("out%d" % i) for i in range(1, 5)},
                [
                    call.setSource("/in.str", "orig.str"),
                    call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                    call.addInput(name="proc_coord_file_path", value="/prc.cif", type="file"),
                    call.addInput(name="report_file_path", value="/in.json", type="file"),
                ]
                + c
                + [
                    call.setDestination(o("out1")),
                    call.addOutput(name="nmr_cif_file_path", value=o("out2"), type="file"),
                    call.addOutput(name="leave_intl_note", value=False, type="param"),
                    call.addOutput(name="nmrif_file_path", value=o("out4"), type="file"),
                    call.setLog(o("out3")),
                    call.op("nmr-str2cif-deposit"),
                ],
            ),
            (
                "nmrIfMergeDepositOp",
                {"src0": cnf, "src1": "/in.cif", "src2": "/model.cif", "src3": "/nmrif.cif"},
                {"dst1": o("out.cif")},
                [call.setSource("/in.cif"), call.addInput(name="coordinate_file_path", value="/model.cif", type="file")]
                + c
                + [
                    call.addOutput(name="nmr_cif_file_path", value=o("out.cif"), type="file"),
                    call.addInput(name="nmrif_file_path", value="/nmrif.cif", type="file"),
                    call.op("nmr-if-merge-deposit"),
                ],
            ),
        ]

    def testOpsWithConfig(self) -> None:
        for opName, inp, out, expected in self._cases(conf=True):
            with self.subTest(op=opName):
                self.mockDp.reset_mock()
                self.assertTrue(self._run(opName, inp, out))
                self.assertEqual(self.dp.method_calls, expected)
                self.assertIn("+NmrUtils.", self.log.getvalue())

    def testOpsWithoutConfig(self) -> None:
        for opName, inp, out, expected in self._cases(conf=False):
            with self.subTest(op=opName):
                self.mockDp.reset_mock()
                self.assertTrue(self._run(opName, inp, out, verbose=False))
                self.assertEqual(self.dp.method_calls, expected)
        self.assertEqual(self.log.getvalue(), "")

    def testOpStatusIsReturned(self) -> None:
        self.dp.op.return_value = False
        for opName, inp, out, _expected in self._cases(conf=False):
            with self.subTest(op=opName):
                self.assertFalse(self._run(opName, inp, out, verbose=False))

    def testOpExceptions(self) -> None:
        self.dp.op.side_effect = RuntimeError("nmr failure")
        for opName, inp, out, _expected in self._cases(conf=True):
            with self.subTest(op=opName):
                log = io.StringIO()
                util = NmrUtils(verbose=False, log=log)
                self.assertFalse(getattr(util, opName)(**self.kwArgs(inp, out)))
                self.assertIn("nmr failure", log.getvalue())

    def testBadConfigJson(self) -> None:
        badConf = self.write("bad.json", "{not json")
        _opName, inp, out, _expected = self._cases(conf=True)[0]
        inp = dict(inp, src0=badConf)
        self.assertFalse(self._run("nefConsistencyCheckOp", inp, out))
        self.dp.op.assert_not_called()

    def testOriginalFileNameBlank(self) -> None:
        blankAuth = self.write("blank.txt", "   \nignored\n")
        emptyAuth = self.write("empty.txt", "")
        for authPath in (blankAuth, emptyAuth):
            for idx, srcName in ((4, "/in.nef"), (6, "/in.str")):
                opName, inp, out, _expected = self._cases(conf=False)[idx]
                with self.subTest(op=opName, auth=os.path.basename(authPath)):
                    self.mockDp.reset_mock()
                    self.assertTrue(self._run(opName, dict(inp, src2=authPath), out, verbose=False))
                    self.dp.setSource.assert_called_once_with(srcName, None)

    def testStr2nefRelease(self) -> None:
        out = {"dst0": self.path("chk.json"), "dst1": self.path("out.str"), "dst2": self.path("out.nef"), "dst3": self.path("str.json"), "dst4": self.path("nef.json")}
        self.dp.op.side_effect = [False, True]
        self.assertTrue(self._run("str2nefReleaseOp", {"src1": "/in.str", "src2": "/model.cif"}, out))
        self.assertEqual(
            self.dp.method_calls,
            [
                call.setSource("/in.str"),
                call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                call.addInput(name="nonblk_anomalous_cs", value=True, type="param"),
                call.addInput(name="nonblk_bad_nterm", value=True, type="param"),
                call.addInput(name="resolve_conflict", value=True, type="param"),
                call.addInput(name="check_mandatory_tag", value=True, type="param"),
                call.setLog(out["dst0"]),
                call.op("nmr-str-consistency-check"),
                call.setSource("/in.str"),
                call.addInput(name="coordinate_file_path", value="/model.cif", type="file"),
                call.addInput(name="report_file_path", value=out["dst0"], type="file"),
                call.setDestination(out["dst1"]),
                call.addOutput(name="nef_file_path", value=out["dst2"], type="file"),
                call.addOutput(name="report_file_path", value=out["dst4"], type="file"),
                call.addOutput(name="leave_intl_note", value=False, type="param"),
                call.setLog(out["dst3"]),
                call.op("nmr-str2nef-release"),
            ],
        )
        self.assertIn("NEF file path:                     %s" % out["dst2"], self.log.getvalue())

    def testStr2nefReleaseFailure(self) -> None:
        self.dp.op.side_effect = [True, False]
        out = {"dst%d" % i: self.path("o%d" % i) for i in range(5)}
        self.assertFalse(self._run("str2nefReleaseOp", {"src1": "/in.str", "src2": "/model.cif"}, out, verbose=False))
        self.dp.op.side_effect = RuntimeError("boom")
        self.assertFalse(self._run("str2nefReleaseOp", {"src1": "/in.str", "src2": "/model.cif"}, out, verbose=False))
        self.assertIn("boom", self.log.getvalue())


class RestraintClassificationTests(NmrUtilsTestBase):
    """csStrConsistencyCheckOp() and csMrMergeOp() sort restraint files into NMR-STAR/NEF and atypical formats"""

    def setUp(self) -> None:
        super().setUp()
        dpPatch = patch(MODULE + ".NmrDpUtility", create=True)
        self.mockDp = dpPatch.start()
        self.addCleanup(dpPatch.stop)
        self.dp = self.mockDp.return_value
        self.dp.op.return_value = True
        self.csListPath = self.write("cs-list.txt", "/data/cs1.str\n/data/cs2.str\n")
        # Restraint files of each flavour
        self.starMr = self.write("mr-star.str", "data_restraints\nsave_dist\nloop_\n_a.b\n1\nstop_\nsave_\n")
        self.loopOnlyMr = self.write("mr-loop.str", "  loop_\n_x.y\n1\n")
        self.amberMr = self.write("mr-amber.txt", "&rst iat=1,2, r1=1.0, r2=2.0 &end\n")
        self.peakMr = self.write("peak.txt", "1 8.1 4.2 1.0e5\n")
        self.binaryMr = self.path("mr-binary.bin")
        with open(self.binaryMr, "wb") as ofh:
            ofh.write(b"\xff\xfe\x00\x81\x9f binary")

    def _mrJson(self, entries: List[Dict[str, str]]) -> str:
        return self.write("mr.json", json.dumps(entries))

    @staticmethod
    def _mr(fileName: str, fileType: str, orig: str) -> Dict[str, str]:
        return {"file_name": fileName, "file_type": fileType, "original_file_name": orig}

    def _inputValue(self, name: str) -> Any:
        found = [c.kwargs for c in self.dp.addInput.call_args_list if c.kwargs.get("name") == name]
        self.assertLessEqual(len(found), 1, name)
        return found[0]["value"] if found else None

    def _inputType(self, name: str) -> Any:
        found = [c.kwargs for c in self.dp.addInput.call_args_list if c.kwargs.get("name") == name]
        return found[0]["type"] if found else None

    def testCsStrConsistencyCheck(self) -> None:
        mrJson = self._mrJson(
            [
                self._mr(self.starMr, "nm-res-xpl", "a.str"),
                self._mr(self.loopOnlyMr, "nm-aux-amb", "b.str"),
                self._mr(self.amberMr, "nm-res-amb", "c.txt"),
                self._mr(self.peakMr, "nm-pea-any", "d.txt"),
                self._mr(self.amberMr, "nm-shi", "e.txt"),
            ]
        )
        util = NmrUtils(verbose=True, log=self.log)
        kw = self.kwArgs({"src1": self.csListPath, "src2": mrJson, "src3": "/model.cif", "prc3": "/prc.cif"}, {"dst": self.path("rep.json")})
        self.assertTrue(util.csStrConsistencyCheckOp(**kw))
        self.assertEqual(self._inputValue("chem_shift_file_path_list"), ["/data/cs1.str", "/data/cs2.str"])
        self.assertEqual(self._inputType("chem_shift_file_path_list"), "file_list")
        self.assertEqual(self._inputValue("restraint_file_path_list"), [self.starMr, self.loopOnlyMr])
        # nm-pea files are not considered by this (deprecated) method, nm-shi is never a restraint
        self.assertEqual(self._inputValue("atypical_restraint_file_path_list"), [self._mr(self.amberMr, "nm-res-amb", "c.txt")])
        self.assertEqual(self._inputValue("coordinate_file_path"), "/model.cif")
        self.assertEqual(self._inputValue("proc_coord_file_path"), "/prc.cif")
        for name, value in (("nonblk_anomalous_cs", True), ("nonblk_bad_nterm", True), ("resolve_conflict", True), ("check_mandatory_tag", False)):
            self.assertIs(self._inputValue(name), value, name)
        self.dp.setLog.assert_called_once_with(self.path("rep.json"))
        self.dp.op.assert_called_once_with("nmr-cs-str-consistency-check")
        text = self.log.getvalue()
        self.assertIn("MR file path list:", text)
        self.assertIn("AR file path list:", text)

    def testCsStrConsistencyCheckNoRestraints(self) -> None:
        self.dp.op.return_value = False
        util = NmrUtils(verbose=True, log=self.log)
        kw = self.kwArgs({"src1": self.csListPath, "src2": self.path("none.json"), "src3": "/m.cif", "prc3": "/p.cif"}, {"dst": self.path("rep.json")})
        self.assertFalse(util.csStrConsistencyCheckOp(**kw))
        self.assertIsNone(self._inputValue("restraint_file_path_list"))
        self.assertIsNone(self._inputValue("atypical_restraint_file_path_list"))
        self.assertNotIn("MR file path list", self.log.getvalue())

    def testCsStrConsistencyCheckFailures(self) -> None:
        util = NmrUtils(verbose=False, log=self.log)
        # Unlike csMrMergeOp(), read errors on restraint files are not tolerated by the deprecated method
        mrJson = self._mrJson([self._mr(self.path("gone.str"), "nm-res-oth", "gone.str")])
        kw = self.kwArgs({"src1": self.csListPath, "src2": mrJson, "src3": "/m.cif", "prc3": "/p.cif"}, {"dst": "/rep.json"})
        self.assertFalse(util.csStrConsistencyCheckOp(**kw))
        self.assertIn("FileNotFoundError", self.log.getvalue())
        kw = self.kwArgs({"src1": self.path("missing.txt"), "src2": mrJson, "src3": "/m.cif", "prc3": "/p.cif"}, {"dst": "/rep.json"})
        self.assertFalse(util.csStrConsistencyCheckOp(**kw))
        self.mockDp.assert_not_called()

    def testCsMrMerge(self) -> None:
        authPath = self.write("auth.txt", "first.str\n\nthird-ignored.str\n")
        mrJson = self._mrJson(
            [
                self._mr(self.starMr, "nm-res-xpl", "a.str"),
                self._mr(self.amberMr, "nm-res-amb", "c.txt"),
                self._mr(self.peakMr, "nm-pea-any", "d.txt"),
                self._mr(self.binaryMr, "nm-res-oth", "x.bin"),
                self._mr(self.amberMr, "nm-shi", "e.txt"),
            ]
        )
        out = {"dst1": self.path("out.str"), "dst2": self.path("out.json"), "dst3": self.path("nmrif.cif")}
        util = NmrUtils(verbose=True, log=self.log)
        kw = self.kwArgs({"src1": self.csListPath, "src2": authPath, "src3": mrJson, "src4": "/model.cif", "prc4": "/prc.cif"}, out)
        self.assertTrue(util.csMrMergeOp(**kw))
        self.mockDp.assert_called_once_with(verbose=True, log=self.log)
        self.assertEqual(
            self._inputValue("chem_shift_file_path_list"),
            [{"file_name": "/data/cs1.str", "file_type": "nmr-star", "original_file_name": "first.str"}, {"file_name": "/data/cs2.str", "file_type": "nmr-star"}],
        )
        self.assertEqual(self._inputType("chem_shift_file_path_list"), "file_dict_list")
        self.assertEqual(self._inputValue("restraint_file_path_list"), [self.starMr])
        self.assertEqual(
            self._inputValue("atypical_restraint_file_path_list"),
            [self._mr(self.amberMr, "nm-res-amb", "c.txt"), self._mr(self.peakMr, "nm-pea-any", "d.txt"), self._mr(self.binaryMr, "nm-res-oth", "x.bin")],
        )
        self.assertIs(self._inputValue("merge_any_pk_as_is"), True)
        self.assertIs(self._inputValue("check_mandatory_tag"), False)
        self.dp.setDestination.assert_called_once_with(out["dst1"])
        self.dp.addOutput.assert_called_once_with(name="nmrif_file_path", value=out["dst3"], type="file")
        self.dp.setLog.assert_called_once_with(out["dst2"])
        self.dp.op.assert_called_once_with("nmr-cs-mr-merge")
        self.assertIn("NMRIF output file path:     %s" % out["dst3"], self.log.getvalue())

    def testCsMrMergeCsOnly(self) -> None:
        authPath = self.write("auth.txt", "")
        self.dp.op.return_value = False
        util = NmrUtils(verbose=False, log=self.log)
        kw = self.kwArgs(
            {"src1": self.csListPath, "src2": authPath, "src3": self.path("none.json"), "src4": "/m.cif", "prc4": "/p.cif"},
            {"dst1": "/o.str", "dst2": "/o.json", "dst3": "/o.cif"},
        )
        self.assertFalse(util.csMrMergeOp(**kw))
        self.assertEqual(
            self._inputValue("chem_shift_file_path_list"), [{"file_name": "/data/cs1.str", "file_type": "nmr-star"}, {"file_name": "/data/cs2.str", "file_type": "nmr-star"}]
        )
        self.assertIsNone(self._inputValue("restraint_file_path_list"))
        self.assertIsNone(self._inputValue("atypical_restraint_file_path_list"))
        self.dp.op.assert_called_once_with("nmr-cs-mr-merge")

    def testCsMrMergeFailures(self) -> None:
        util = NmrUtils(verbose=False, log=self.log)
        authPath = self.write("auth.txt", "")
        cases = {
            "missingCsList": {"src1": self.path("missing"), "src2": authPath, "src3": self.path("none.json"), "src4": "/m", "prc4": "/p"},
            "missingMrFile": {"src1": self.csListPath, "src2": authPath, "src3": self._mrJson([self._mr(self.path("gone"), "nm-res-xpl", "g")]), "src4": "/m", "prc4": "/p"},
            "badMrJson": {"src1": self.csListPath, "src2": authPath, "src3": self.write("bad.json", "[{"), "src4": "/m", "prc4": "/p"},
        }
        for name, inp in cases.items():
            with self.subTest(case=name):
                self.assertFalse(util.csMrMergeOp(**self.kwArgs(inp, {"dst1": "/o", "dst2": "/o", "dst3": "/o"})))
        self.mockDp.assert_not_called()
        self.dp.op.side_effect = RuntimeError("merge failed")
        inp = {"src1": self.csListPath, "src2": authPath, "src3": self.path("none.json"), "src4": "/m", "prc4": "/p"}
        self.assertFalse(util.csMrMergeOp(**self.kwArgs(inp, {"dst1": "/o", "dst2": "/o", "dst3": "/o"})))
        self.assertIn("merge failed", self.log.getvalue())


if __name__ == "__main__":
    unittest.main()

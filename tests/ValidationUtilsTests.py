##
# File: ValidationUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the ValidationUtils workflow plugin and its module-level helpers"""

import io
import os
import sys
import tempfile
import unittest
import warnings
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from mmcif.io.IoAdapterPy import IoAdapterPy

from wwpdb.utils.wf.plugins.ValidationUtils import ValidationUtils, remediate_cs_file, starToPdbx
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODULE = "wwpdb.utils.wf.plugins.ValidationUtils"

CS_STAR = """data_cs
save_assigned_chem_shift_list_1
_Assigned_chem_shift_list.Sf_category assigned_chemical_shifts
_Assigned_chem_shift_list.ID 1
loop_
_Atom_chem_shift.ID
_Atom_chem_shift.Val
1 8.1
2 4.2
stop_
save_
"""

CONFIG = {"SITE_PREFIX": "TESTSITE", "SITE_NAME": "TESTNAME", "SITE_WEB_APPS_TOP_PATH": "/webapps"}


def _fileObj(filePath: Optional[str], dirPath: str = "", depId: str = "D_000001") -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    obj.getDirPathReference.return_value = dirPath
    obj.getDepositionDataSetId.return_value = depId
    obj.getWorkflowInstanceId.return_value = "W_000001"
    obj.getStorageType.return_value = "wf-instance"
    return obj


def _mockConfig(extra: Optional[Dict[str, Any]] = None) -> MagicMock:
    values = dict(CONFIG)
    values.update(extra or {})
    mockCi = MagicMock()
    mockCi.return_value.get.side_effect = lambda key, default=None: values.get(key, default)
    return mockCi


def _addInputNames(mockObj: MagicMock) -> Dict[str, Any]:
    return {c.kwargs["name"]: c.kwargs["value"] for c in mockObj.addInput.call_args_list}


class ModuleFunctionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _write(self, name: str, content: str) -> str:
        fPath = os.path.join(self.__tmpDir.name, name)
        with open(fPath, "w") as ofh:
            ofh.write(content)
        return fPath

    def testStarToPdbx(self) -> None:
        starPath = self._write("cs.str", CS_STAR)
        outPath = os.path.join(self.__tmpDir.name, "cs.cif")
        log = io.StringIO()
        self.assertTrue(starToPdbx(starPath=starPath, pdbxPath=outPath, log=log))
        self.assertIn("('assigned_chem_shift_list_1', 'definition')", log.getvalue())
        containers = IoAdapterPy(False, log).readFile(outPath)
        self.assertEqual([(c.getName(), c.getType()) for c in containers], [("cs", "data"), ("assigned_chem_shift_list_1", "data")])
        self.assertEqual(containers[1].getObj("Atom_chem_shift").getAttributeValueList("Val"), ["8.1", "4.2"])

    def testStarToPdbxNoConversion(self) -> None:
        log = io.StringIO()
        singlePath = self._write("single.cif", "data_x\n_entity.id 1\n")
        outPath = os.path.join(self.__tmpDir.name, "out.cif")
        self.assertFalse(starToPdbx(starPath=None, pdbxPath=outPath, log=log))
        self.assertFalse(starToPdbx(starPath=singlePath, pdbxPath=None, log=log))
        self.assertFalse(starToPdbx(starPath=singlePath, pdbxPath=outPath, log=log))
        self.assertFalse(os.path.exists(outPath))

    def testStarToPdbxException(self) -> None:
        log = io.StringIO()
        with patch(MODULE + ".IoAdapterPy") as mockIo:
            mockIo.return_value.readFile.side_effect = ValueError("bad star")
            self.assertFalse(starToPdbx(starPath="/in.str", pdbxPath="/out.cif", log=log))
        self.assertIn("ValueError: bad star", log.getvalue())

    def testRemediateCsFile(self) -> None:
        with patch(MODULE + ".CifToNmrStar", create=True) as mockCtns:
            mockCtns.return_value.convert.return_value = True
            self.assertTrue(remediate_cs_file("/in.str", "/out.str"))
            mockCtns.return_value.convert.assert_called_once_with(cifPath="/in.str", strPath="/out.str")


class ValidationReportTests(unittest.TestCase):
    """Tests for validationReportAllOp (RcsbDpUtility) and validationReportAllOpV2/V3 (ValidationWrapper)"""

    def setUp(self) -> None:
        self.tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.dirPath = self.tmpDir.name
        self.log = io.StringIO()
        self.modelPath = self._write("model.cif", "data_x\n")

    def tearDown(self) -> None:
        self.tmpDir.cleanup()

    def _write(self, name: str, content: str = "x\n") -> str:
        fPath = os.path.join(self.dirPath, name)
        with open(fPath, "w") as ofh:
            ofh.write(content)
        return fPath

    def _outPaths(self, count: int) -> List[str]:
        return [os.path.join(self.dirPath, "out-%d" % i) for i in range(1, count + 1)]

    def _kwArgs(
        self, srcPaths: Dict[str, str], nDst: int, uD: Optional[Dict[str, Any]] = None, depId: str = "D_000001", extraOut: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        inpD: Dict[str, Any] = {"src1": _fileObj(self.modelPath, self.dirPath, depId)}
        for key, value in srcPaths.items():
            inpD[key] = _fileObj(value, self.dirPath)
        outD: Dict[str, Any] = {"dst%d" % (i + 1): _fileObj(p, self.dirPath) for i, p in enumerate(self._outPaths(nDst))}
        outD.update(extraOut or {})
        return {
            "inputObjectD": inpD,
            "outputObjectD": outD,
            "userParameterD": uD if uD is not None else {"validation_mode": "annotate", "in_annotation": "no"},
            "internalParameterD": {},
        }

    # --- validationReportAllOp -------------------------------------------------
    @patch(MODULE + ".RcsbDpUtility")
    def testAllOpWithAllInputs(self, mockDp: MagicMock) -> None:
        srcs = {"src%d" % i: self._write("in-%d" % i) for i in range(2, 6)}
        util = ValidationUtils(verbose=True, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertTrue(util.validationReportAllOp(**self._kwArgs(srcs, 6)))
        mockDp.assert_called_once_with(tmpPath=self.dirPath, siteId="TESTSITE", verbose=True, log=self.log)
        dp = mockDp.return_value
        dp.imp.assert_called_once_with(self.modelPath)
        self.assertEqual(
            _addInputNames(dp),
            {
                "request_validation_mode": "annotate",
                "request_annotation_context": "no",
                "entry_id": "D_000001",
                "sf_file_path": srcs["src2"],
                "cs_file_path": srcs["src3"],
                "vol_file_path": srcs["src4"],
                "fsc_file_path": srcs["src5"],
            },
        )
        dp.op.assert_called_once_with("annot-wwpdb-validate-all")
        dp.expLog.assert_called_once_with(os.path.join(self.dirPath, "val-report-all.log"))
        o = self._outPaths(6)
        dp.expList.assert_called_once_with(dstPathList=[o[0], o[1], o[2], o[3], o[4], os.path.join(self.dirPath, "val-report-images.tar"), o[5]])
        dp.cleanup.assert_called_once_with()
        self.assertIn("validation mode:       annotate", self.log.getvalue())

    @patch(MODULE + ".RcsbDpUtility")
    def testAllOpMinimalInputs(self, mockDp: MagicMock) -> None:
        missing = os.path.join(self.dirPath, "missing")
        srcs = {"src2": missing, "src3": missing}
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertTrue(util.validationReportAllOp(**self._kwArgs(srcs, 6, {"validation_mode": "other", "in_annotation": "maybe"}, depId="D1")))
        dp = mockDp.return_value
        dp.addInput.assert_not_called()
        dp.op.assert_called_once_with("annot-wwpdb-validate-all")
        self.assertEqual(self.log.getvalue(), "")

    @patch(MODULE + ".RcsbDpUtility")
    def testAllOpFailures(self, mockDp: MagicMock) -> None:
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertFalse(util.validationReportAllOp(**self._kwArgs({}, 6, {})))
            self.assertIn("KeyError", self.log.getvalue())
            mockDp.return_value.op.side_effect = RuntimeError("validation failed")
            self.assertFalse(util.validationReportAllOp(**self._kwArgs({}, 6)))
        self.assertIn("validation failed", self.log.getvalue())
        mockDp.return_value.cleanup.assert_not_called()

    # --- validationReportAllOpV2 -----------------------------------------------
    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV2WithAllInputs(self, mockVw: MagicMock) -> None:
        srcs = {"src%d" % i: self._write("in-%d" % i) for i in range(2, 7)}
        util = ValidationUtils(verbose=True, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig({"WF_VALIDATION_REMOVE": "yes"})):
            self.assertTrue(util.validationReportAllOpV2(**self._kwArgs(srcs, 8, {"validation_mode": "release", "in_annotation": "yes"})))
        mockVw.assert_called_once_with(tmpPath=self.dirPath, siteId="TESTSITE", verbose=True, log=self.log)
        vw = mockVw.return_value
        vw.imp.assert_called_once_with(self.modelPath)
        self.assertEqual(
            _addInputNames(vw),
            {
                "request_validation_mode": "release",
                "request_annotation_context": "yes",
                "always_clear_calcs": "Y",
                "entry_id": "D_000001",
                "sf_file_path": srcs["src2"],
                "cs_file_path": srcs["src3"],
                "vol_file_path": srcs["src4"],
                "fsc_file_path": srcs["src5"],
                "emdb_xml_path": srcs["src6"],
            },
        )
        vw.op.assert_called_once_with("annot-wwpdb-validate-all-sf")
        o = self._outPaths(8)
        vw.expList.assert_called_once_with(dstPathList=[o[0], o[1], o[2], o[3], o[4], os.path.join(self.dirPath, "val-report-images.tar"), o[7], o[5], o[6]])
        vw.cleanup.assert_called_once_with()
        self.assertIn("EMDB XML   file path:  %s" % srcs["src6"], self.log.getvalue())

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV2MinimalInputs(self, mockVw: MagicMock) -> None:
        missing = os.path.join(self.dirPath, "missing")
        srcs = {"src%d" % i: missing for i in range(2, 7)}
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertTrue(util.validationReportAllOpV2(**self._kwArgs(srcs, 8, {"validation_mode": "x", "in_annotation": "x"}, depId="")))
        mockVw.return_value.addInput.assert_not_called()

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV2Failure(self, mockVw: MagicMock) -> None:
        mockVw.return_value.expList.side_effect = OSError("disk full")
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertFalse(util.validationReportAllOpV2(**self._kwArgs({}, 8)))
            self.assertFalse(util.validationReportAllOpV2(**self._kwArgs({}, 7)))
        self.assertIn("disk full", self.log.getvalue())
        self.assertIn("KeyError: 'dst8'", self.log.getvalue())

    # --- validationReportAllOpV3 -----------------------------------------------
    def _siteNameObj(self, containerType: str) -> WfDataObject:
        obj = WfDataObject()
        obj.setContainerTypeName(containerType)
        return obj

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV3NmrDataOverridesCs(self, mockVw: MagicMock) -> None:
        srcs = {"src%d" % i: self._write("in-%d" % i) for i in range(2, 7)}
        dst9 = self._siteNameObj("value")
        util = ValidationUtils(verbose=True, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig({"WF_VALIDATION_REMOVE": "1"})), patch(MODULE + ".starToPdbx") as mockS2p:
            self.assertTrue(util.validationReportAllOpV3(**self._kwArgs(srcs, 8, {"validation_mode": "deposit", "in_annotation": "yes"}, extraOut={"dst9": dst9})))
        mockS2p.assert_not_called()
        self.assertEqual(dst9.getValue(), "TESTNAME")
        vw = mockVw.return_value
        self.assertEqual(
            vw.addInput.call_args_list,
            [
                call(name="request_validation_mode", value="deposit"),
                call(name="request_annotation_context", value="yes"),
                call(name="always_clear_calcs", value="Y"),
                call(name="entry_id", value="D_000001"),
                call(name="sf_file_path", value=srcs["src2"]),
                call(name="cs_file_path", value=srcs["src6"]),
                call(name="nmr_restraint_file_path", value=srcs["src6"]),
                call(name="vol_file_path", value=srcs["src4"]),
                call(name="fsc_file_path", value=srcs["src5"]),
            ],
        )
        vw.op.assert_called_once_with("annot-wwpdb-validate-all-sf")
        o = self._outPaths(8)
        vw.expList.assert_called_once_with(dstPathList=[o[0], o[1], o[2], o[3], o[4], os.path.join(self.dirPath, "val-report-images.tar"), o[7], o[5], o[6]])
        vw.cleanup.assert_called_once_with()
        self.assertIn("NMRdata file path:       %s" % srcs["src6"], self.log.getvalue())

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV3CsFileOutsideAnnotation(self, mockVw: MagicMock) -> None:
        csPath = self._write("cs.cif")
        dst9 = self._siteNameObj("list")
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()), patch(MODULE + ".starToPdbx") as mockS2p:
            self.assertTrue(util.validationReportAllOpV3(**self._kwArgs({"src3": csPath}, 8, {"validation_mode": "server", "in_annotation": "no"}, extraOut={"dst9": dst9})))
        mockS2p.assert_not_called()
        self.assertIsNone(dst9.getValue())
        self.assertEqual(_addInputNames(mockVw.return_value)["cs_file_path"], csPath)
        self.assertNotIn("always_clear_calcs", _addInputNames(mockVw.return_value))

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV3CsFileRemediatedInAnnotation(self, mockVw: MagicMock) -> None:
        csPath = self._write("D_000001_cs_P1.cif.V1")
        captured: Dict[str, Any] = {}

        def fakeRemediate(infile: str, outfile: str) -> bool:
            captured["exists"] = os.path.isdir(os.path.dirname(outfile))
            captured["files"] = (infile, outfile)
            return True

        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()), patch(MODULE + ".starToPdbx") as mockS2p, patch(
            MODULE + ".remediate_cs_file", side_effect=fakeRemediate
        ), warnings.catch_warnings():
            # The library relies on implicit cleanup of its TemporaryDirectory when the method returns
            warnings.simplefilter("ignore", ResourceWarning)
            self.assertTrue(
                util.validationReportAllOpV3(**self._kwArgs({"src3": csPath, "src6": os.path.join(self.dirPath, "nope")}, 8, {"validation_mode": "legacy", "in_annotation": "yes"}))
            )
        infile, outfile = captured["files"]
        self.assertTrue(captured["exists"])
        tmpSub = os.path.dirname(outfile)
        self.assertEqual(os.path.dirname(tmpSub), self.dirPath)
        self.assertFalse(os.path.exists(tmpSub))
        self.assertEqual(infile, os.path.join(tmpSub, "D_000001_cs_P1.cif.V1.str"))
        self.assertEqual(outfile, os.path.join(tmpSub, "D_000001_cs_P1.cif.V1"))
        mockS2p.assert_called_once_with(csPath, infile, self.log)
        names = _addInputNames(mockVw.return_value)
        self.assertEqual(names["cs_file_path"], outfile)
        self.assertNotIn("nmr_restraint_file_path", names)
        self.assertIn("Remediating CS file", self.log.getvalue())

    @patch(MODULE + ".ValidationWrapper")
    def testAllOpV3Failure(self, mockVw: MagicMock) -> None:
        mockVw.return_value.op.side_effect = RuntimeError("validation failed")
        util = ValidationUtils(verbose=False, log=self.log)
        with patch(MODULE + ".ConfigInfo", _mockConfig()):
            self.assertFalse(util.validationReportAllOpV3(**self._kwArgs({}, 8)))
        self.assertIn("validation failed", self.log.getvalue())
        mockVw.return_value.cleanup.assert_not_called()


class CorrespondLetterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__dirPath = self.__tmpDir.name
        self.__sessionPath = os.path.join(self.__dirPath, "session")
        os.makedirs(self.__sessionPath)
        self.__modelPath = os.path.join(self.__dirPath, "model.cif")
        with open(self.__modelPath, "w") as ofh:
            ofh.write("data_x\n")
        self.__letterPath = os.path.join(self.__dirPath, "letter.txt")
        self.__log = io.StringIO()
        patchers = [
            patch(MODULE + ".ConfigInfo", _mockConfig()),
            patch(MODULE + ".InputRequest"),
            patch(MODULE + ".DataExchange"),
            patch(MODULE + ".CorresPNDTemplate", create=True),
        ]
        _ci, self.mockReq, self.mockDe, self.mockTpl = [p.start() for p in patchers]
        for p in patchers:
            self.addCleanup(p.stop)
        self.mockReq.return_value.newSessionObj.return_value.getPath.return_value = self.__sessionPath
        self.mockDe.return_value.copyToSession.return_value = "/session/file"

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _kwArgs(self, modelPath: Optional[str] = None) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src1": _fileObj(modelPath or self.__modelPath, self.__dirPath), "src2": _fileObj("/data/val.xml")},
            "outputObjectD": {"dst": _fileObj(self.__letterPath, self.__dirPath)},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def testLetterCopied(self) -> None:
        with open(os.path.join(self.__sessionPath, "D_000001_correspondence-to-depositor_P1.txt"), "w") as ofh:
            ofh.write("Dear depositor\n")
        util = ValidationUtils(verbose=True, log=self.__log)
        self.assertTrue(util.validationGetCorrespondLetterOp(**self._kwArgs()))
        req = self.mockReq.return_value
        req.setValue.assert_has_calls(
            [
                call("TopSessionPath", self.__dirPath),
                call("TopPath", "/webapps"),
                call("TemplatePath", os.path.join("/webapps", "htdocs", "validation_tasks_v2")),
                call("WWPDB_SITE_ID", "TESTSITE"),
                call("entryid", "D_000001"),
                call("entryfilename", "D_000001_model_P1.cif"),
            ]
        )
        self.mockDe.assert_called_once_with(reqObj=req, depDataSetId="D_000001", wfInstanceId="W_000001", fileSource="wf-instance", verbose=True, log=self.__log)
        self.assertEqual(
            self.mockDe.return_value.copyToSession.call_args_list,
            [
                call(contentType="model", formatType="pdbx", version="latest", partitionNumber=1),
                call(contentType="validation-data", formatType="xml", version="latest", partitionNumber=1),
            ],
        )
        self.mockTpl.assert_called_once_with(reqObj=req, verbose=True, log=self.__log)
        self.mockTpl.return_value.get.assert_called_once_with()
        with open(self.__letterPath) as ifh:
            self.assertEqual(ifh.read(), "Dear depositor\n")
        self.assertIn("Cor letter file path:  %s" % self.__letterPath, self.__log.getvalue())

    def testNoLetterProduced(self) -> None:
        util = ValidationUtils(verbose=False, log=self.__log)
        self.assertTrue(util.validationGetCorrespondLetterOp(**self._kwArgs()))
        self.assertFalse(os.path.exists(self.__letterPath))

    def testModelNotCopied(self) -> None:
        self.mockDe.return_value.copyToSession.return_value = None
        util = ValidationUtils(verbose=False, log=self.__log)
        self.assertFalse(util.validationGetCorrespondLetterOp(**self._kwArgs()))
        self.mockTpl.assert_not_called()

    def testUnreadableModel(self) -> None:
        util = ValidationUtils(verbose=False, log=self.__log)
        self.assertFalse(util.validationGetCorrespondLetterOp(**self._kwArgs(os.path.join(self.__dirPath, "missing.cif"))))
        self.mockReq.assert_not_called()

    def testExceptionReturnsFalse(self) -> None:
        self.mockTpl.return_value.get.side_effect = RuntimeError("template error")
        util = ValidationUtils(verbose=False, log=self.__log)
        self.assertFalse(util.validationGetCorrespondLetterOp(**self._kwArgs()))
        self.assertIn("template error", self.__log.getvalue())


if __name__ == "__main__":
    unittest.main()

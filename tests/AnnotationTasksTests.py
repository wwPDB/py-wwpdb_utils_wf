##
# File: AnnotationTasksTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the AnnotationUtils workflow plugin.

External programs (RcsbDpUtility, DensityWrapper, MetalCoordinationUtility, DbLoadingApi) and the optional
annotation packages (wwpdb.apps.ann_tasks_v2, PathInfo, InputRequest) are replaced with mocks.
"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from mmcif.io.IoAdapterCore import IoAdapterCore

from wwpdb.utils.wf.plugins.AnnotationUtils import AnnotationUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODULE = "wwpdb.utils.wf.plugins.AnnotationUtils"
SITE_ID = "WWPDB_UNIT_TEST"
DEP_ID = "D_1000000001"


def _fileObj(filePath: Optional[str] = None, dirPath: Optional[str] = None, depId: str = DEP_ID) -> MagicMock:
    """Return a WfDataObject stand-in that reports the given file reference."""
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    obj.getDirPathReference.return_value = dirPath
    obj.getDepositionDataSetId.return_value = depId
    return obj


def _writeFile(filePath: str, text: str = "") -> str:
    with open(filePath, "w") as ofh:
        ofh.write(text)
    return filePath


def _readFile(filePath: str) -> str:
    with open(filePath) as ifh:
        return ifh.read()


class AnnotationUtilsTestBase(unittest.TestCase):
    """Common fixture: temp directory, log capture, patched ConfigInfo and RcsbDpUtility."""

    def setUp(self) -> None:
        self.tmpDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpDir.cleanup)
        self.dirPath = self.tmpDir.name
        self.log = io.StringIO()
        self.au = AnnotationUtils(verbose=True, log=self.log)

        cI = MagicMock()
        cI.get.return_value = SITE_ID
        self.mockConfigInfo = self._patch("ConfigInfo", return_value=cI)
        self.dp = MagicMock(name="dp")
        self.mockDp = self._patch("RcsbDpUtility", return_value=self.dp)

    def _patch(self, name: str, create: bool = False, **kwargs: Any) -> MagicMock:
        patcher = patch("%s.%s" % (MODULE, name), create=create, **kwargs)
        mock: MagicMock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _path(self, name: str) -> str:
        return os.path.join(self.dirPath, name)

    def _run(
        self,
        method: Callable[..., Any],
        inp: Dict[str, Any],
        out: Dict[str, Any],
        uD: Optional[Dict[str, Any]] = None,
    ) -> Any:
        return method(inputObjectD=inp, outputObjectD=out, userParameterD=uD if uD is not None else {}, internalParameterD={})

    def _srcDst(self, dstName: str = "report.txt") -> Tuple[Dict[str, Any], Dict[str, Any], str, str]:
        srcPath = self._path("model.cif")
        dstPath = self._path(dstName)
        inp = {"src": _fileObj(srcPath, self.dirPath)}
        out = {"dst": _fileObj(dstPath, self.dirPath)}
        return inp, out, srcPath, dstPath

    def assertDpCreated(self, times: int = 1) -> None:
        self.assertEqual(self.mockDp.call_count, times)
        self.mockDp.assert_called_with(tmpPath=self.dirPath, siteId=SITE_ID, verbose=True, log=self.log)

    def assertFailsOnException(self, method: Callable[..., Any], inp: Dict[str, Any], out: Dict[str, Any], uD: Optional[Dict[str, Any]] = None) -> None:
        self.assertFalse(self._run(method, inp, out, uD))
        self.assertIn("Traceback", self.log.getvalue())


class SimpleDpOpsTests(AnnotationUtilsTestBase):
    """Ops that import one file, run one RcsbDpUtility op and export one file."""

    # (method name, dp op name, log file name or None)
    CASES: ClassVar[List[Tuple[str, str, Optional[str]]]] = [
        ("specialPositionCheckOp", "annot-dcc-special-position", "special-position-check.log"),
        ("formatCheckPdbxOp", "annot-format-check-pdbx", "format-check-pdbx.log"),
        ("formatCheckPdbOp", "annot-format-check-pdb", "format-check-pdb.log"),
        ("dictCheckOp", "check-cif", "dict-check.log"),
        ("dictR4CheckOp", "check-cif-v4", "dict-check.log"),
        ("geometryCheckOp", "validate-geometry", "geometry-check-report.log"),
        ("miscCheckReportOp", "annot-extra-checks", "misc-check-report.log"),
        ("nucleicAcidGeometryOp", "annot-base-pair-info", "base-pair-position.log"),
        ("solventPositionAddDerivedOp", "annot-reposition-solvent-add-derived", "solvent-position.log"),
        ("solventPositionOp", "annot-reposition-solvent", "solvent-position.log"),
        ("solventPositionAnalysis", "annot-distant-solvent", "solvent-position-analysis.log"),
        ("linkOp", "annot-link-ssbond", "annot-link-and-ss-bond.log"),
        ("cisPeptideOp", "annot-cis-peptide", None),
        ("updateGeometryValidationOp", "annot-validate-geometry", None),
        ("getCorresInfoOp", "annot-get-corres-info", None),
        ("secondaryStructureOp", "annot-secondary-structure", "annot-secondary-structure-w-top.log"),
        ("assemblyUpdateDepInfoOp", "annot-update-dep-assembly-info", "assembly-depinfo-update.log"),
    ]

    def testSuccess(self) -> None:
        for methodName, opName, logName in self.CASES:
            with self.subTest(method=methodName):
                self.mockDp.reset_mock()
                self.dp.reset_mock()
                inp, out, srcPath, dstPath = self._srcDst()
                self.assertTrue(self._run(getattr(self.au, methodName), inp, out))
                self.assertDpCreated()
                expected = [call.imp(srcPath), call.op(opName)]
                if logName is not None:
                    expected.append(call.expLog(self._path(logName)))
                expected += [call.exp(dstPath), call.cleanup()]
                self.assertEqual(self.dp.mock_calls, expected)
                self.assertIn(srcPath, self.log.getvalue())

    def testDpFailureReturnsFalse(self) -> None:
        self.dp.op.side_effect = RuntimeError("program failed")
        for methodName, _opName, _logName in self.CASES:
            with self.subTest(method=methodName):
                inp, out, _srcPath, _dstPath = self._srcDst()
                self.assertFailsOnException(getattr(self.au, methodName), inp, out)
                self.dp.exp.assert_not_called()

    def testMissingInputReturnsFalse(self) -> None:
        for methodName, _opName, _logName in self.CASES:
            with self.subTest(method=methodName):
                _inp, out, _srcPath, _dstPath = self._srcDst()
                self.assertFalse(self._run(getattr(self.au, methodName), {}, out))
        self.mockDp.assert_not_called()

    def testFormatCheckNmrFlag(self) -> None:
        for methodName in ("formatCheckPdbxOp", "formatCheckPdbOp"):
            for flag, expectNmr in (("Y", True), ("N", False)):
                with self.subTest(method=methodName, flag=flag):
                    self.dp.reset_mock()
                    inp, out, _srcPath, _dstPath = self._srcDst()
                    self.assertTrue(self._run(getattr(self.au, methodName), inp, out, {"nmr_flag": flag}))
                    if expectNmr:
                        self.dp.addInput.assert_called_once_with(name="nmr", value="Y")
                    else:
                        self.dp.addInput.assert_not_called()

    def testDictCheckFirstOp(self) -> None:
        inp, out, srcPath, dstPath = self._srcDst()
        self.assertTrue(self._run(self.au.dictCheckFirstOp, inp, out))
        self.assertDpCreated()
        self.assertEqual(
            self.dp.mock_calls,
            [call.imp(srcPath), call.addInput("first_block"), call.op("check-cif"), call.expLog(self._path("dict-check.log")), call.exp(dstPath), call.cleanup()],
        )

    def testDictCheckFirstOpFailure(self) -> None:
        self.mockDp.side_effect = RuntimeError("no dp")
        inp, out, _srcPath, _dstPath = self._srcDst()
        self.assertFailsOnException(self.au.dictCheckFirstOp, inp, out)

    def testNonVerboseIsQuiet(self) -> None:
        au = AnnotationUtils(verbose=False, log=self.log)
        inp, out, _srcPath, _dstPath = self._srcDst()
        self.assertTrue(self._run(au.dictCheckOp, inp, out))
        self.mockDp.assert_called_once_with(tmpPath=self.dirPath, siteId=SITE_ID, verbose=False, log=self.log)
        self.assertEqual(self.log.getvalue(), "")


class MultiFileDpOpsTests(AnnotationUtilsTestBase):
    """Ops with several inputs/outputs or several RcsbDpUtility steps."""

    def testDccCheckReportWithSf(self) -> None:
        sfPath = _writeFile(self._path("sf.cif"), "data_sf\n")
        xyzPath = self._path("model.cif")
        reportPath = self._path("dcc.cif")
        logPath = self._path("dcc.log")
        inp = {"src1": _fileObj(xyzPath), "src2": _fileObj(sfPath)}
        out = {"dst1": _fileObj(reportPath, self.dirPath), "dst2": _fileObj(logPath)}
        self.assertTrue(self._run(self.au.dccCheckReportOp, inp, out))
        self.assertDpCreated()
        self.assertEqual(
            self.dp.mock_calls,
            [
                call.imp(xyzPath),
                call.addInput(name="sf_file_path", value=sfPath, type="file"),
                call.op("annot-dcc-report"),
                call.expLog(logPath),
                call.exp(reportPath),
                call.cleanup(),
            ],
        )

    def testDccCheckReportWithoutSf(self) -> None:
        inp = {"src1": _fileObj(self._path("model.cif")), "src2": _fileObj(self._path("missing-sf.cif"))}
        out = {"dst1": _fileObj(self._path("dcc.cif"), self.dirPath), "dst2": _fileObj(self._path("dcc.log"))}
        self.assertTrue(self._run(self.au.dccCheckReportOp, inp, out))
        self.dp.addInput.assert_not_called()
        self.dp.op.assert_called_once_with("annot-dcc-report")

    def testDccCheckReportFailure(self) -> None:
        self.dp.exp.side_effect = OSError("cannot export")
        inp = {"src1": _fileObj(self._path("model.cif")), "src2": _fileObj(None)}
        out = {"dst1": _fileObj(self._path("dcc.cif"), self.dirPath), "dst2": _fileObj(self._path("dcc.log"))}
        self.assertFailsOnException(self.au.dccCheckReportOp, inp, out)
        self.dp.cleanup.assert_not_called()

    def _linkPtmObjects(self, nOut: int) -> Tuple[Dict[str, Any], Dict[str, Any], str, List[str]]:
        srcPath = self._path("model.cif")
        dstPaths = [self._path("out%d" % i) for i in range(1, nOut + 1)]
        inp = {"src": _fileObj(srcPath)}
        out = {"dst%d" % (i + 1): _fileObj(p, self.dirPath) for i, p in enumerate(dstPaths)}
        return inp, out, srcPath, dstPaths

    def testLinkPtmOps(self) -> None:
        # (method name, number of outputs, extra addInput call or None, op name)
        cases: List[Tuple[str, int, Optional[Any], str]] = [
            ("linkPtmOp", 2, None, "annot-link-ssbond-with-ptm"),
            ("linkPtmMccOp", 3, None, "annot-link-ssbond-with-ptm-mcc"),
            ("linkPtmMccWithSkipOp", 3, call.addInput(name="check_skip_option", value="add"), "annot-link-ssbond-with-ptm-mcc"),
        ]
        for methodName, nOut, extra, opName in cases:
            with self.subTest(method=methodName):
                self.dp.reset_mock()
                self.mockDp.reset_mock()
                inp, out, srcPath, dstPaths = self._linkPtmObjects(nOut)
                self.assertTrue(self._run(getattr(self.au, methodName), inp, out))
                self.assertDpCreated()
                expected = [call.imp(srcPath)]
                if extra is not None:
                    expected.append(extra)
                expected += [call.op(opName), call.expLog(self._path("annot-link-and-ss-bond.log")), call.expList(dstPathList=dstPaths), call.cleanup()]
                self.assertEqual(self.dp.mock_calls, expected)

    def testLinkPtmOpsFailure(self) -> None:
        for methodName in ("linkPtmOp", "linkPtmMccOp", "linkPtmMccWithSkipOp"):
            with self.subTest(method=methodName):
                # Missing the last output object raises KeyError before any work is done
                inp, out, _srcPath, _dstPaths = self._linkPtmObjects(1)
                self.assertFailsOnException(getattr(self.au, methodName), inp, out)
        self.mockDp.assert_not_called()

    def testTopologyOps(self) -> None:
        cases = [
            ("secondaryStructureTopologyOp", "annot-secondary-structure", "annot-secondary-structure-w-top.log"),
            ("consolidatedTasksOp", "annot-consolidated-tasks", "annot-consolidated-tasks-w-top.log"),
        ]
        for methodName, opName, logName in cases:
            with self.subTest(method=methodName):
                self.dp.reset_mock()
                srcPath = self._path("model.cif")
                topPath = self._path("topology.txt")
                dstPath = self._path("model-out.cif")
                inp = {"src1": _fileObj(srcPath), "src2": _fileObj(topPath)}
                out = {"dst": _fileObj(dstPath, self.dirPath)}
                self.assertTrue(self._run(getattr(self.au, methodName), inp, out))
                self.assertEqual(
                    self.dp.mock_calls,
                    [
                        call.imp(srcPath),
                        call.addInput(name="ss_topology_file_path", value=topPath),
                        call.op(opName),
                        call.expLog(self._path(logName)),
                        call.exp(dstPath),
                        call.cleanup(),
                    ],
                )
                self.assertIn(topPath, self.log.getvalue())

    def testTopologyOpsFailure(self) -> None:
        self.dp.imp.side_effect = RuntimeError("bad import")
        for methodName in ("secondaryStructureTopologyOp", "consolidatedTasksOp"):
            with self.subTest(method=methodName):
                inp = {"src1": _fileObj(self._path("m.cif")), "src2": _fileObj(self._path("t.txt"))}
                out = {"dst": _fileObj(self._path("o.cif"), self.dirPath)}
                self.assertFailsOnException(getattr(self.au, methodName), inp, out)

    def testSiteEnvironmentOp(self) -> None:
        inp, out, srcPath, dstPath = self._srcDst("model-out.cif")
        resultPath = self._path(DEP_ID + "-site-anal.cif")
        self.assertTrue(self._run(self.au.siteEnvironmentOp, inp, out))
        self.assertDpCreated()
        self.assertEqual(
            self.dp.mock_calls,
            [
                call.imp(srcPath),
                call.addInput(name="block_id", value=DEP_ID),
                call.op("annot-site"),
                call.expLog(self._path("site-anal.log")),
                call.exp(resultPath),
                call.imp(srcPath),
                call.addInput(name="site_info_file_path", value=resultPath, type="file"),
                call.op("annot-merge-struct-site"),
                call.exp(dstPath),
                call.cleanup(),
            ],
        )

    def testSiteEnvironmentOpFailure(self) -> None:
        self.dp.op.side_effect = [None, RuntimeError("merge failed")]
        inp, out, _srcPath, _dstPath = self._srcDst("model-out.cif")
        self.assertFailsOnException(self.au.siteEnvironmentOp, inp, out)
        self.dp.cleanup.assert_not_called()

    def testAssemblyReportOp(self) -> None:
        inp, out, srcPath, dstPath = self._srcDst("assembly-report.xml")
        self.assertTrue(self._run(self.au.assemblyReportOp, inp, out))
        self.assertDpCreated()
        self.assertEqual(
            self.dp.mock_calls,
            [
                call.imp(srcPath),
                call.addInput(name="pisa_session_name", value="session_" + DEP_ID),
                call.op("pisa-analysis"),
                call.expLog(self._path("assembly-analysis.log")),
                call.op("pisa-assembly-report-xml"),
                call.exp(dstPath),
                call.expLog(self._path("assembly-report.log")),
                call.cleanup(),
            ],
        )

    def testAssemblyReportOpFailure(self) -> None:
        self.dp.op.side_effect = RuntimeError("pisa failed")
        inp, out, _srcPath, _dstPath = self._srcDst("assembly-report.xml")
        self.assertFailsOnException(self.au.assemblyReportOp, inp, out)


class AssemblyReportAndModelsTests(AnnotationUtilsTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.reader = MagicMock(name="PisaAssemblyReader()")
        self.mockReader = self._patch("PisaAssemblyReader", create=True, return_value=self.reader)
        self.srcPath = self._path("model.cif")
        self.reportPath = self._path("assembly-report.xml")
        self.dst2 = MagicMock(spec=WfDataObject)
        self.inp = {"src": _fileObj(self.srcPath)}
        self.out = {"dst1": _fileObj(self.reportPath, self.dirPath), "dst2": self.dst2}

    def testModelsGenerated(self) -> None:
        # Assembly 0 is skipped and anything above 50 stops the loop
        self.reader.getAssemblyDict.return_value = {2: "b", 0: "x", 51: "z", 1: "a"}
        self.assertTrue(self._run(self.au.assemblyReportAndModelsOp, self.inp, self.out))
        self.reader.read.assert_called_once_with(self.reportPath)
        expectedPaths = [self._path(DEP_ID + "_assembly-model-xyz_P%d.cif.V1" % i) for i in (1, 2)]
        self.dst2.setValue.assert_called_once_with(expectedPaths)
        self.assertEqual(
            self.dp.mock_calls[-7:],
            [
                call.addInput(name="pisa_assembly_id", value=1),
                call.op("pisa-assembly-coordinates-cif"),
                call.exp(expectedPaths[0]),
                call.addInput(name="pisa_assembly_id", value=2),
                call.op("pisa-assembly-coordinates-cif"),
                call.exp(expectedPaths[1]),
                call.cleanup(),
            ],
        )
        self.assertEqual(
            self.dp.mock_calls[:7],
            [
                call.imp(self.srcPath),
                call.addInput(name="pisa_session_name", value="session_" + DEP_ID),
                call.op("pisa-analysis"),
                call.expLog(self._path("assembly-analysis.log")),
                call.op("pisa-assembly-report-xml"),
                call.exp(self.reportPath),
                call.expLog(self._path("assembly-report.log")),
            ],
        )

    def testNoAssemblies(self) -> None:
        self.reader.getAssemblyDict.return_value = {}
        self.assertTrue(self._run(self.au.assemblyReportAndModelsOp, self.inp, self.out))
        self.dst2.setValue.assert_called_once_with([])
        self.assertNotIn(call.op("pisa-assembly-coordinates-cif"), self.dp.mock_calls)

    def testReaderFailure(self) -> None:
        self.reader.read.side_effect = RuntimeError("bad xml")
        self.assertFailsOnException(self.au.assemblyReportAndModelsOp, self.inp, self.out)
        self.dst2.setValue.assert_not_called()


class XmlCheckTests(AnnotationUtilsTestBase):
    DIAG = "input_file_1 validates\nstdin: noise\ninput_file_1:12: element foo: invalid\n\n  other problem  \n"

    def setUp(self) -> None:
        super().setUp()
        self.srcPath = self._path("model.cif")
        self.reportPath = self._path("xml-check.txt")
        self.expPath = self._path(DEP_ID + "_model-temp_P1.cif.V1")
        self.xmlPath = self.expPath + ".xml-noatom"
        self.inp = {"src": _fileObj(self.srcPath)}
        self.out = {"dst": _fileObj(self.reportPath, self.dirPath)}
        self.dp.exp.side_effect = lambda p: _writeFile(p, "data_x\n")
        self.dp.expList.side_effect = self._expList
        self.diag = self.DIAG

    def _expList(self, outputList: List[str]) -> None:
        if outputList[0].endswith(".xml-noatom"):
            _writeFile(outputList[0], "<xml/>")
        elif outputList[0].endswith("check-xml.diag.txt"):
            _writeFile(outputList[0], self.diag)

    def testSuccess(self) -> None:
        _writeFile(self.expPath, "stale")
        self.assertTrue(self._run(self.au.xmlCheckOp, self.inp, self.out))
        self.assertEqual(self.mockDp.call_count, 4)
        ops = [c.args[0] for c in self.dp.op.call_args_list]
        self.assertEqual(ops, ["cif2pdbx-ext", "annot-public-pdbx-to-xml-noatom", "annot-check-xml-xmllint", "annot-check-xml-stdinparse"])
        self.dp.addInput.assert_called_once_with(name="destination", value="archive_next")
        self.dp.imp.assert_has_calls([call(self.srcPath), call(self.expPath), call(self.xmlPath), call(self.xmlPath)])
        # Diagnostics from both checks are filtered and appended to the report
        self.assertEqual(_readFile(self.reportPath), "12: element foo: invalid\nother problem\n" * 2)
        # Intermediate files are removed
        self.assertFalse(os.path.exists(self.expPath))
        self.assertFalse(os.path.exists(self.xmlPath))
        self.assertFalse(os.path.exists(self._path("check-xml.diag.txt")))

    def testValidXmlGivesEmptyReport(self) -> None:
        self.diag = "input_file_1 validates\n"
        self.assertTrue(self._run(self.au.xmlCheckOp, self.inp, self.out))
        self.assertEqual(_readFile(self.reportPath), "")

    def testNoExportedModel(self) -> None:
        self.dp.exp.side_effect = None
        self.assertFalse(self._run(self.au.xmlCheckOp, self.inp, self.out))
        self.assertEqual(self.mockDp.call_count, 1)

    def testXmlGenerationFails(self) -> None:
        self.dp.expList.side_effect = None
        self.assertFalse(self._run(self.au.xmlCheckOp, self.inp, self.out))
        self.assertFalse(os.path.exists(self.expPath))
        self.assertEqual(self.mockDp.call_count, 2)

    def testXmlGenerationRaises(self) -> None:
        self.dp.expList.side_effect = RuntimeError("xml failed")
        self.assertFalse(self._run(self.au.xmlCheckOp, self.inp, self.out))
        self.assertIn("xml failed", self.log.getvalue())

    def testException(self) -> None:
        self.mockDp.side_effect = RuntimeError("no dp")
        self.assertFailsOnException(self.au.xmlCheckOp, self.inp, self.out)


class MergeXyzTests(AnnotationUtilsTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.inpPath = self._path("model.cif")
        self.newPath = self._path("new.cif")
        self.mergedPath = self._path("merged.cif")
        self.logPath = self._path("merge.log")
        self.dst3 = MagicMock(spec=WfDataObject)
        self.inp = {"src1": _fileObj(self.inpPath), "src2": _fileObj(self.newPath)}
        self.out = {"dst1": _fileObj(self.mergedPath, self.dirPath), "dst2": _fileObj(self.logPath), "dst3": self.dst3}

    def testMergeOk(self) -> None:
        _writeFile(self.newPath, "data_new\n")
        _writeFile(self.mergedPath, "data_merged\n")
        _writeFile(self.logPath, "working\nFinished!\n")
        self.assertTrue(self._run(self.au.mergeXyzOp, self.inp, self.out, {"deposit": "yes"}))
        self.assertDpCreated()
        self.assertEqual(
            self.dp.mock_calls,
            [
                call.setDebugMode(flag=True),
                call.imp(self.inpPath),
                call.addInput(name="new_coordinate_file_path", value=self.newPath, type="file"),
                call.addInput(name="new_coordinate_format", value="cif", type="param"),
                call.addInput(name="deposit", value=True, type="param"),
                call.op("annot-merge-xyz"),
                call.expLog(self.logPath),
                call.exp(self.mergedPath),
                call.cleanup(),
            ],
        )
        self.dst3.setValue.assert_called_once_with("ok")

    def testFormatAndDepositParameters(self) -> None:
        _writeFile(self.newPath, "ATOM\n")
        cases = [
            ({"new_coordinate_format": "pdb", "deposit": "no"}, "pdb", False),
            ({"new_coordinate_format": "mmcif"}, "cif", False),
            ({"new_coordinate_format": "pdbx", "deposit": "True"}, "cif", True),
        ]
        for uD, fmt, deposit in cases:
            with self.subTest(uD=uD):
                self.dp.reset_mock()
                self.assertTrue(self._run(self.au.mergeXyzOp, self.inp, self.out, uD))
                self.dp.addInput.assert_any_call(name="new_coordinate_format", value=fmt, type="param")
                depositCall = call(name="deposit", value=True, type="param")
                self.assertEqual(depositCall in self.dp.addInput.call_args_list, deposit)

    def testMissingNewFileAndMergedOutput(self) -> None:
        self.assertTrue(self._run(self.au.mergeXyzOp, self.inp, self.out))
        self.dp.addInput.assert_not_called()
        self.assertIn("XYZ new source input not found", self.log.getvalue())
        self.dst3.setValue.assert_called_once_with("error")

    def testLogWithoutFinished(self) -> None:
        _writeFile(self.mergedPath, "data_merged\n")
        _writeFile(self.logPath, "something went wrong\n")
        self.assertTrue(self._run(self.au.mergeXyzOp, self.inp, self.out))
        self.dst3.setValue.assert_called_once_with("error")

    def testMissingLog(self) -> None:
        _writeFile(self.mergedPath, "data_merged\n")
        self.assertTrue(self._run(self.au.mergeXyzOp, self.inp, self.out))
        self.dst3.setValue.assert_called_once_with("error")

    def testException(self) -> None:
        self.dp.op.side_effect = RuntimeError("merge failed")
        self.assertFailsOnException(self.au.mergeXyzOp, self.inp, self.out)
        self.dst3.setValue.assert_not_called()


class CombineCifFilesTests(AnnotationUtilsTestBase):
    SRC = "data_SRC\n_entry.id SRC\n#\n_struct.entry_id SRC\n_struct.title 'Source title'\n"
    MRG = (
        "data_MRG\n_entry.id MRG\n#\n_struct.entry_id MRG\n_struct.title 'Merge title'\n#\n"
        "_exptl.entry_id MRG\n_exptl.method 'X-RAY DIFFRACTION'\n#\n_cell.entry_id MRG\n_cell.length_a 10.0\n"
    )

    def setUp(self) -> None:
        super().setUp()
        self.srcPath = _writeFile(self._path("src.cif"), self.SRC)
        self.mrgPath = _writeFile(self._path("mrg.cif"), self.MRG)
        self.outPath = self._path("out.cif")
        self.inp = {"src1": _fileObj(self.srcPath), "src2": _fileObj(self.mrgPath)}
        self.out = {"dst": _fileObj(self.outPath)}

    def _readOut(self) -> Any:
        containers = IoAdapterCore().readFile(inputFilePath=self.outPath, outDirPath=self.dirPath)
        self.assertEqual(len(containers), 1)
        return containers[0]

    def testMergeAllCategoriesWithoutOverwrite(self) -> None:
        self.assertTrue(self._run(self.au.combineCifFilesOp, self.inp, self.out))
        block = self._readOut()
        self.assertEqual(block.getName(), "SRC")
        self.assertEqual(sorted(block.getObjNameList()), ["cell", "entry", "exptl", "struct"])
        self.assertEqual(block.getObj("struct").getValue("title", 0), "Source title")
        self.assertEqual(block.getObj("exptl").getValue("method", 0), "X-RAY DIFFRACTION")

    def testMergeSelectedCategories(self) -> None:
        self.assertTrue(self._run(self.au.combineCifFilesOp, self.inp, self.out, {"categories": "exptl,struct"}))
        block = self._readOut()
        self.assertEqual(sorted(block.getObjNameList()), ["entry", "exptl", "struct"])

    def testNothingToMerge(self) -> None:
        self.assertTrue(self._run(self.au.combineCifFilesOp, self.inp, self.out, {"categories": "refine"}))
        self.assertIn("nothing to merge", self.log.getvalue())
        self.assertFalse(os.path.exists(self.outPath))

    def testMissingSource(self) -> None:
        self.inp["src1"] = _fileObj(self._path("missing.cif"))
        self.assertFalse(self._run(self.au.combineCifFilesOp, self.inp, self.out))
        self.assertIn("failed to load src1", self.log.getvalue())

    def testMissingMergeFile(self) -> None:
        self.inp["src2"] = _fileObj(self._path("missing.cif"))
        self.assertFalse(self._run(self.au.combineCifFilesOp, self.inp, self.out))
        self.assertIn("Failed to load src2", self.log.getvalue())

    def testException(self) -> None:
        self.assertFailsOnException(self.au.combineCifFilesOp, {"src1": _fileObj(self.srcPath)}, self.out)


class CollaboratorOpsTests(AnnotationUtilsTestBase):
    """Ops that delegate to other OneDep classes instead of RcsbDpUtility."""

    def testStatusLoadOp(self) -> None:
        dbLd = MagicMock()
        mockDb = self._patch("DbLoadingApi", return_value=dbLd)
        srcPath = self._path("status.cif")
        inp = {"src": _fileObj(srcPath, self.dirPath)}
        for result in (True, False):
            with self.subTest(result=result):
                dbLd.doLoadStatus.return_value = result
                self.assertEqual(self._run(self.au.statusLoadOp, inp, {}), result)
                dbLd.doLoadStatus.assert_called_with(srcPath, self.dirPath)
        mockDb.assert_called_with(log=self.log, verbose=True)
        dbLd.doLoadStatus.side_effect = RuntimeError("db down")
        self.assertFailsOnException(self.au.statusLoadOp, inp, {})

    def _metalObjects(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        dst1 = _fileObj(self._path("model-out.cif"), self.dirPath)
        dst1.getWorkflowInstanceId.return_value = "W_000001"
        dst1.getStorageType.return_value = "wf-instance"
        inp = {"src1": _fileObj(self._path("model.cif")), "src2": _fileObj(self._path("metal.txt"))}
        out = {"dst1": dst1, "dst2": _fileObj(self._path("metal.csv"))}
        return inp, out

    def testMetalCoordinationOps(self) -> None:
        pI = MagicMock()
        pI.getFilePath.side_effect = lambda entryId, **kw: "/path/%s/%s.%s" % (entryId, kw["contentType"], kw["formatType"])
        mockPathInfo = self._patch("PathInfo", create=True, return_value=pI)
        mp = MagicMock()
        mockMcu = self._patch("MetalCoordinationUtility", return_value=mp)
        for methodName, extra in (("metalCoordinationOp", {}), ("metalCoordinationWithLargeTimeoutOp", {"noTimeOut": True})):
            with self.subTest(method=methodName):
                mp.reset_mock()
                pI.getFilePath.reset_mock()
                inp, out = self._metalObjects()
                self.assertTrue(self._run(getattr(self.au, methodName), inp, out))
                mockPathInfo.assert_called_with(siteId=SITE_ID, verbose=True, log=self.log)
                mockMcu.assert_called_with(wrkPath=self.dirPath, siteId=SITE_ID, verbose=True, log=self.log)
                pI.getFilePath.assert_any_call(DEP_ID, wfInstanceId="W_000001", contentType="findgeo-annotation", formatType="json", fileSource="wf-instance", versionId="next")
                self.assertEqual(
                    mp.mock_calls,
                    [
                        call.setModelCoordinatesFilePath(self._path("model.cif")),
                        call.setPolyAtomicMetalLigandInfoWithFilePath(self._path("metal.txt")),
                        call.setFindGeoOutputFilePath("/path/%s/findgeo-annotation.json" % DEP_ID),
                        call.setMetalCoordOutputFilePath("/path/%s/metalcoord-annotation.json" % DEP_ID),
                        call.setMetalAnnotationOutputFilePath(self._path(DEP_ID + ".Annotation.txt")),
                        call.runUpdate(pdbxPath=self._path("model-out.cif"), csvPath=self._path("metal.csv"), **extra),
                    ],
                )

    def testMetalCoordinationOpsFailure(self) -> None:
        self._patch("PathInfo", create=True)
        mp = MagicMock()
        mp.runUpdate.side_effect = RuntimeError("timeout")
        self._patch("MetalCoordinationUtility", return_value=mp)
        for methodName in ("metalCoordinationOp", "metalCoordinationWithLargeTimeoutOp"):
            with self.subTest(method=methodName):
                inp, out = self._metalObjects()
                self.assertFailsOnException(getattr(self.au, methodName), inp, out)

    def _emObjects(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        inp = {"src": _fileObj(self._path("model.cif")), "sessdir": _fileObj(None, self.dirPath)}
        out = {"dst": _fileObj(self._path("model-out.cif"))}
        return inp, out

    def testEm3dAutoMapFixOp(self) -> None:
        eaf = MagicMock()
        eaf.autoFixMapLabels.return_value = False
        mockEaf = self._patch("EmAutoFix", create=True, return_value=eaf)
        inp, out = self._emObjects()
        # Returns True even when no fix was applied
        self.assertTrue(self._run(self.au.em3dAutoMapFixOp, inp, out))
        mockEaf.assert_called_once_with(sessionPath=self.dirPath, siteId=SITE_ID)
        eaf.autoFixMapLabels.assert_called_once_with(datasetid=DEP_ID, modelin=self._path("model.cif"), modelout=self._path("model-out.cif"))
        eaf.autoFixMapLabels.side_effect = RuntimeError("bad map")
        self.assertFailsOnException(self.au.em3dAutoMapFixOp, inp, out)

    def testEm3dAutoEmMapFixVersOp(self) -> None:
        eaf = MagicMock()
        eaf.autoFixEmMapVersions.return_value = "fixed"
        mockEaf = self._patch("EmMapAutoFixVers", create=True, return_value=eaf)
        inp, out = self._emObjects()
        for uD, location in (({}, "archive"), ({"location": "deposit"}, "deposit")):
            with self.subTest(location=location):
                self.assertTrue(self._run(self.au.em3dAutoEmMapFixVersOp, inp, out, uD))
                eaf.autoFixEmMapVersions.assert_called_with(datasetid=DEP_ID, modelin=self._path("model.cif"), modelout=self._path("model-out.cif"), location=location)
        mockEaf.assert_called_with(sessionPath=self.dirPath, siteId=SITE_ID)
        self.assertIn("fixvers returns fixed", self.log.getvalue())
        eaf.autoFixEmMapVersions.side_effect = RuntimeError("bad")
        self.assertFailsOnException(self.au.em3dAutoEmMapFixVersOp, inp, out)

    def testUpdatePdbxDatabaseRelatedOp(self) -> None:
        ur = MagicMock()
        ur.updateRelatedEntries.return_value = True
        mockUr = self._patch("UpdateRelated", create=True, return_value=ur)
        inp, out, srcPath, dstPath = self._srcDst("model-out.cif")
        self.assertTrue(self._run(self.au.updatePdbxDatabaseRelatedOp, inp, out))
        mockUr.assert_called_once_with(siteId=SITE_ID)
        ur.updateRelatedEntries.assert_called_once_with(srcPath, dstPath, self._path("update_pdbx_database_related.log"))
        ur.updateRelatedEntries.side_effect = RuntimeError("lookup failed")
        self.assertFailsOnException(self.au.updatePdbxDatabaseRelatedOp, inp, out)

    def testUpdateSFWavelengthOp(self) -> None:
        req = MagicMock()
        mockReq = self._patch("InputRequest", create=True, return_value=req)
        peu = MagicMock()
        peu.doUpdate.return_value = True
        mockPeu = self._patch("PdbxExpUpdate", create=True, return_value=peu)
        modelPath = self._path("model.cif")
        sfPath = self._path("sf.cif")
        sfOutPath = self._path("sf-out.cif")
        inp = {"src1": _fileObj(modelPath, self.dirPath), "src2": _fileObj(sfPath)}
        out = {"dst": _fileObj(sfOutPath)}

        # No SF file (NMR/EM): nothing to do
        self.assertTrue(self._run(self.au.updateSFWavelengthOp, inp, out))
        mockReq.assert_not_called()
        mockPeu.assert_not_called()

        _writeFile(sfPath, "data_sf\n")
        self.assertTrue(self._run(self.au.updateSFWavelengthOp, inp, out))
        req.setValue.assert_has_calls([call("TopSessionPath", self.dirPath), call("WWPDB_SITE_ID", SITE_ID)])
        req.newSessionObj.assert_called_once_with()
        mockPeu.assert_called_once_with(req, verbose=True, log=self.log)
        peu.doUpdate.assert_called_once_with(DEP_ID, modelInputFile=modelPath, expInputFile=sfPath, expOutputFile=sfOutPath, skipNotChanged=True)

        peu.doUpdate.side_effect = RuntimeError("bad sf")
        self.assertFailsOnException(self.au.updateSFWavelengthOp, inp, out)

    def testEmMapCheckOp(self) -> None:
        task = MagicMock()
        mockTask = self._patch("EmMapCheckTask", create=True, return_value=task)
        inp, out, srcPath, dstPath = self._srcDst()
        self.assertTrue(self._run(self.au.emMapCheckOp, inp, out))
        mockTask.assert_called_once_with(siteId=SITE_ID, sessionPath=self.dirPath, verbose=True, log=self.log)
        task.run.assert_called_once_with(DEP_ID, srcPath, dstPath)
        task.run.side_effect = RuntimeError("check failed")
        self.assertFailsOnException(self.au.emMapCheckOp, inp, out)


class EmdXmlHeaderCheckTests(AnnotationUtilsTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.srcPath = self._path("model.cif")
        self.reportPath = self._path("emd-report.txt")
        self.inp = {"src": _fileObj(self.srcPath)}
        self.out = {"dst": _fileObj(self.reportPath, self.dirPath)}

    def _workDirs(self) -> List[str]:
        return [d for d in os.listdir(self.dirPath) if d.startswith("rcsb-")]

    def testNoEmAdmin(self) -> None:
        _writeFile(self.srcPath, "data_X\n_entry.id X\n")
        mockEmh = self._patch("EmHeaderUtils", create=True)
        self.assertTrue(self._run(self.au.emdXmlHeaderCheckOp, self.inp, self.out))
        mockEmh.assert_not_called()

    def testMissingModel(self) -> None:
        mockEmh = self._patch("EmHeaderUtils", create=True)
        self.assertTrue(self._run(self.au.emdXmlHeaderCheckOp, self.inp, self.out))
        mockEmh.assert_not_called()

    def testHeaderTranslation(self) -> None:
        _writeFile(self.srcPath, "data_X\n_em_admin.entry_id X\n_em_admin.current_status HPUB\n")
        emh = MagicMock(spec=["transHeader"])
        emh.transHeader.return_value = True
        mockEmh = self._patch("EmHeaderUtils", create=True, return_value=emh)
        self.assertTrue(self._run(self.au.emdXmlHeaderCheckOp, self.inp, self.out))
        mockEmh.assert_called_once_with(siteId=SITE_ID, verbose=True, log=self.log)
        args, kwargs = emh.transHeader.call_args
        self.assertEqual(args[0], self.srcPath)
        self.assertEqual(os.path.basename(args[1]), DEP_ID + "-emd.xml")
        self.assertEqual(os.path.dirname(os.path.dirname(args[1])), self.dirPath)
        self.assertEqual(args[2], self.reportPath)
        self.assertEqual(kwargs, {"validateXml": True})
        self.assertIn("Status of xml translation True", self.log.getvalue())
        # Temporary working directory is removed
        self.assertEqual(self._workDirs(), [])

    def testEmdTranslationThenHeader(self) -> None:
        _writeFile(self.srcPath, "data_X\n_em_admin.entry_id X\n")
        emh = MagicMock(spec=["transHeader", "transEmd"])
        emh.transEmd.return_value = True
        self._patch("EmHeaderUtils", create=True, return_value=emh)
        self.assertTrue(self._run(self.au.emdXmlHeaderCheckOp, self.inp, self.out))
        emdArgs, emdKwargs = emh.transEmd.call_args
        self.assertEqual(emdArgs[0], self.srcPath)
        self.assertEqual(os.path.basename(emdArgs[1]), DEP_ID + "_model-emd.cif")
        self.assertEqual(emdKwargs, {"mode": "src-dst", "tags": []})
        # The translated model is what gets converted to XML
        self.assertEqual(emh.transHeader.call_args[0][0], emdArgs[1])

    def testEmdTranslationFails(self) -> None:
        _writeFile(self.srcPath, "data_X\n_em_admin.entry_id X\n")
        emh = MagicMock(spec=["transHeader", "transEmd"])
        emh.transEmd.return_value = False
        self._patch("EmHeaderUtils", create=True, return_value=emh)
        self.assertTrue(self._run(self.au.emdXmlHeaderCheckOp, self.inp, self.out))
        emh.transHeader.assert_not_called()
        self.assertIn("Translation of model failed", self.log.getvalue())

    def testException(self) -> None:
        _writeFile(self.srcPath, "data_X\n_em_admin.entry_id X\n")
        self._patch("EmHeaderUtils", create=True, side_effect=RuntimeError("no em"))
        self.assertFailsOnException(self.au.emdXmlHeaderCheckOp, self.inp, self.out)


class BcifConversionTests(AnnotationUtilsTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.dw = MagicMock()
        self.mockDw = self._patch("DensityWrapper", return_value=self.dw)

    def testEmVolumeMissingModel(self) -> None:
        inp = {"src": _fileObj(self._path("missing.cif"), self.dirPath)}
        self.assertFailsOnException(self.au.emVolumeBcifConversionOp, inp, {})
        self.assertIn("Missing model file", self.log.getvalue())

    def testEmVolumeNoEmMap(self) -> None:
        modelPath = _writeFile(self._path("model.cif"), "data_X\n_entry.id X\n")
        self.assertTrue(self._run(self.au.emVolumeBcifConversionOp, {"src": _fileObj(modelPath, self.dirPath)}, {}))
        self.mockDw.assert_not_called()

    def testEmVolumeConversion(self) -> None:
        text = "data_X\nloop_\n_em_map.id\n_em_map.file\n1 emd-map1.map\n2 emd-map2.map\n"
        modelPath = _writeFile(self._path("model.cif"), text)
        pi = MagicMock()
        pi.parseFileName.side_effect = lambda name: (DEP_ID, "em-volume", "map", name[-5])
        pi.getFilePath.side_effect = lambda depId, contentType, formatType, partNumber: "/%s/%s.%s.%s" % (depId, contentType, formatType, partNumber)
        mockPi = self._patch("PathInfo", create=True, return_value=pi)
        self.assertTrue(self._run(self.au.emVolumeBcifConversionOp, {"src": _fileObj(modelPath, self.dirPath)}, {}))
        mockPi.assert_called_once_with(siteId=SITE_ID)
        self.assertEqual(pi.parseFileName.call_args_list, [call("emd-map1.map"), call("emd-map2.map")])
        self.assertEqual(
            self.dw.convert_em_volume.call_args_list,
            [
                call(in_em_volume="/%s/em-volume.map.1" % DEP_ID, out_binary_volume="/%s/em-volume.bcif.1" % DEP_ID, working_dir=self.dirPath),
                call(in_em_volume="/%s/em-volume.map.2" % DEP_ID, out_binary_volume="/%s/em-volume.bcif.2" % DEP_ID, working_dir=self.dirPath),
            ],
        )

    @unittest.expectedFailure
    def testEmVolumeConversionFailureReturnsFalse(self) -> None:
        # Library bug: emVolumeBcifConversionOp() ignores the result of DensityWrapper.convert_em_volume() and always returns
        # True, although its docstring promises False on failure (xrayBcifConversionOp() does return the result).  See ERRORS.md #18
        text = "data_X\nloop_\n_em_map.id\n_em_map.file\n1 emd-map1.map\n"
        modelPath = _writeFile(self._path("model.cif"), text)
        pi = MagicMock()
        pi.parseFileName.return_value = (DEP_ID, "em-volume", "map", 1)
        pi.getFilePath.return_value = "/x/map"
        self._patch("PathInfo", create=True, return_value=pi)
        self.dw.convert_em_volume.return_value = False
        self.assertFalse(self._run(self.au.emVolumeBcifConversionOp, {"src": _fileObj(modelPath, self.dirPath)}, {}))

    def _xrayObjects(self) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        paths = [self._path("model.cif"), self._path("2fofc.cif"), self._path("fofc.cif")]
        inp = {"src%d" % (i + 1): _fileObj(p) for i, p in enumerate(paths)}
        out = {"dst": _fileObj(self._path("map.bcif"), self.dirPath)}
        return inp, out, paths

    def testXrayMissingMaps(self) -> None:
        inp, out, paths = self._xrayObjects()
        _writeFile(paths[0])
        _writeFile(paths[1])
        self.assertTrue(self._run(self.au.xrayBcifConversionOp, inp, out))
        self.mockDw.assert_not_called()

    def testXrayConversionResultIsReturned(self) -> None:
        inp, out, paths = self._xrayObjects()
        for p in paths:
            _writeFile(p)
        for result in (True, False):
            with self.subTest(result=result):
                self.dw.convert_xray_density_map.return_value = result
                self.assertEqual(self._run(self.au.xrayBcifConversionOp, inp, out), result)
        self.dw.convert_xray_density_map.assert_called_with(
            coord_file=paths[0], in_2fofc_cif=paths[1], in_fofc_cif=paths[2], out_binary_volume=self._path("map.bcif"), working_dir=self.dirPath
        )

    def testXrayException(self) -> None:
        inp, out, paths = self._xrayObjects()
        for p in paths:
            _writeFile(p)
        self.dw.convert_xray_density_map.side_effect = RuntimeError("conversion failed")
        with self.assertLogs(MODULE, level="ERROR"):
            self.assertFailsOnException(self.au.xrayBcifConversionOp, inp, out)


class NoOpTests(AnnotationUtilsTestBase):
    def testNoOp(self) -> None:
        self.assertTrue(self._run(self.au.noOp, {}, {}))
        self.mockDp.assert_not_called()


if __name__ == "__main__":
    unittest.main()

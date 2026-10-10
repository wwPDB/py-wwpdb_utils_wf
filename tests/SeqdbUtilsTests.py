##
# File: SeqdbUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the SeqdbUtils workflow plugin

The sequence module (wwpdb.apps.seqmodule) is optional and imported at module load inside
contextlib.suppress(), so the module-level names SeqModInputRequest and DataImporter are patched
with create=True.
"""

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

from wwpdb.utils.wf.plugins.SeqdbUtils import SeqdbUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODULE = "wwpdb.utils.wf.plugins.SeqdbUtils"


def _dataObj(filePath: Optional[str], dirPath: str, instanceId: str, storageType: str) -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    obj.getDirPathReference.return_value = dirPath
    obj.getDepositionDataSetId.return_value = "D_000001"
    obj.getWorkflowInstanceId.return_value = instanceId
    obj.getStorageType.return_value = storageType
    return obj


class SeqdbUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__dirPath = self.__tmpDir.name
        self.__log = io.StringIO()
        patchers = [
            patch(MODULE + ".SeqModInputRequest", create=True),
            patch(MODULE + ".DataImporter", create=True),
            patch(MODULE + ".getSiteId", return_value="TESTSITE"),
            patch(MODULE + ".RcsbDpUtility"),
        ]
        self.mockReq, self.mockDi, self.mockSiteId, self.mockDp = [p.start() for p in patchers]
        for p in patchers:
            self.addCleanup(p.stop)
        self.mockDi.return_value.loadSeqDataAssemble.return_value = (["1", "2"], True)

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def _kwArgs(self, uD: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        src = _dataObj("/data/D_000001_model_P1.cif.V1", "/data", "W_000001", "archive")
        dst = _dataObj(os.path.join(self.__dirPath, "out.cif"), self.__dirPath, "W_000002", "wf-instance")
        return {"inputObjectD": {"src": src}, "outputObjectD": {"dst": dst}, "userParameterD": uD or {}, "internalParameterD": {}}

    def _assertSetup(self) -> None:
        self.mockReq.assert_called_once_with({}, verbose=True, log=self.__log)
        req = self.mockReq.return_value
        req.setValue.assert_has_calls(
            [
                call("TopSessionPath", self.__dirPath),
                call("WWPDB_SITE_ID", "TESTSITE"),
                call("identifier", "D_000001"),
                call("instance", "W_000001"),
            ]
        )
        req.newSessionObj.assert_called_once_with()
        self.mockDi.assert_called_once_with(reqObj=req, fileSource="archive", maxRefAlign=100, verbose=True, log=self.__log)

    def testMySetup(self) -> None:
        util = SeqdbUtils(verbose=False, log=self.__log)
        util.mySetup(topSessionPath="/sessions")
        self.mockSiteId.assert_called_once_with(defaultSiteId="WWPDB_DEPOLY_TEST")
        self.mockReq.return_value.setValue.assert_has_calls([call("TopSessionPath", "/sessions"), call("WWPDB_SITE_ID", "TESTSITE")])

    def testMatchAllOps(self) -> None:
        for opName, autoFlag in (("matchAllOp", False), ("matchAllAutoOp", True)):
            with self.subTest(op=opName):
                self.mockReq.reset_mock()
                self.mockDi.reset_mock()
                util = SeqdbUtils(verbose=True, log=self.__log)
                self.assertTrue(getattr(util, opName)(**self._kwArgs()))
                self._assertSetup()
                dI = self.mockDi.return_value
                dI.copyModelFile.assert_called_once_with(inputFileSource="archive", inputWfInstanceId="W_000001")
                dI.loadSeqDataAssemble.assert_called_once_with(doAutoProcess=autoFlag)
                expected: List[Any] = [
                    call(messageHead="SeqdbUtils.%s(OnStart)" % opName),
                    call(
                        inputFileSource="session",
                        outputFileSource="wf-instance",
                        outputWfInstanceId="W_000002",
                        versionIndex=4,
                        includePolyLinkFile=True,
                        includeSeqAssignFile=autoFlag,
                        entityIdList=["1", "2"],
                        messageHead="SeqdbUtils.%s(OnFinish)" % opName,
                    ),
                ]
                self.assertEqual(dI.copyFiles.call_args_list, expected)
        self.assertIn("Input model PDBx file path: /data/D_000001_model_P1.cif.V1", self.__log.getvalue())

    def testMatchAllOpsFailure(self) -> None:
        self.mockDi.return_value.copyModelFile.side_effect = RuntimeError("copy failed")
        for opName in ("matchAllOp", "matchAllAutoOp"):
            with self.subTest(op=opName):
                util = SeqdbUtils(verbose=False, log=self.__log)
                self.assertFalse(getattr(util, opName)(**self._kwArgs()))
        self.assertIn("copy failed", self.__log.getvalue())

    def testMatchEntity(self) -> None:
        self.mockDi.return_value.loadSeqDataAssemble.return_value = (["2"], True)
        util = SeqdbUtils(verbose=True, log=self.__log)
        self.assertTrue(util.matchEntityOp(**self._kwArgs({"entity_id": 2})))
        self._assertSetup()
        dI = self.mockDi.return_value
        dI.loadSeqDataAssemble.assert_called_once_with(selectedEntityIdList=["2"], doRefSearch=True)
        dI.copyFiles.assert_called_with(
            inputFileSource="session",
            outputFileSource="wf-instance",
            outputWfInstanceId="W_000002",
            versionIndex=4,
            includePolyLinkFile=True,
            entityIdList=["2"],
            messageHead="SeqdbUtils.matchEntityOp(OnFinish)",
        )
        self.assertIn("Entity id : 2", self.__log.getvalue())

    def testMatchEntityReturnsLoadStatus(self) -> None:
        self.mockDi.return_value.loadSeqDataAssemble.return_value = ([], False)
        util = SeqdbUtils(verbose=False, log=self.__log)
        self.assertFalse(util.matchEntityOp(**self._kwArgs({"entity_id": "1"})))

    def testMatchEntityMissingParameter(self) -> None:
        util = SeqdbUtils(verbose=False, log=self.__log)
        self.assertFalse(util.matchEntityOp(**self._kwArgs()))
        self.assertIn("KeyError", self.__log.getvalue())
        self.mockDi.assert_not_called()

    def _updateKwArgs(self, seqAssignPath: Optional[str]) -> Dict[str, Any]:
        src1 = _dataObj("/data/D_000001_model_P1.cif.V1", "/data", "W_000001", "wf-instance")
        src2 = _dataObj(seqAssignPath, "/data", "W_000001", "wf-instance")
        dst = _dataObj(os.path.join(self.__dirPath, "out.cif"), self.__dirPath, "W_000001", "wf-instance")
        return {"inputObjectD": {"src1": src1, "src2": src2}, "outputObjectD": {"dst": dst}, "userParameterD": {}, "internalParameterD": {}}

    def testUpdateModelWithSeqAssignment(self) -> None:
        seqAssignPath = os.path.join(self.__dirPath, "seq-assign.cif")
        with open(seqAssignPath, "w") as ofh:
            ofh.write("data_x\n")
        util = SeqdbUtils(verbose=True, log=self.__log)
        self.assertTrue(util.updateModelWithSeqAssignmentOp(**self._updateKwArgs(seqAssignPath)))

        self.mockDp.assert_called_once_with(tmpPath=self.__dirPath, siteId="TESTSITE", verbose=True, log=self.__log)
        dp = self.mockDp.return_value
        dp.addInput.assert_called_once_with(name="seqmod_assign_file_path", value=seqAssignPath, type="file")
        dp.imp.assert_called_once_with("/data/D_000001_model_P1.cif.V1")
        dp.op.assert_called_once_with("annot-merge-sequence-data")
        dp.exp.assert_called_once_with(os.path.join(self.__dirPath, "out.cif"))
        dp.cleanup.assert_not_called()

        dI = self.mockDi.return_value
        dI.copyModelFile.assert_called_once_with(inputFileSource="wf-instance", inputWfInstanceId="W_000001", outputFileSource="archive", versionIndex=4)
        dI.copyFiles.assert_called_once_with(
            inputFileSource="wf-instance",
            inputWfInstanceId="W_000001",
            outputFileSource="archive",
            versionIndex=4,
            includePolyLinkFile=True,
            includeSeqAssignFile=True,
            messageHead="SeqdbUtils.updateModelWithSeqAssignmentOp(OnFinish)",
        )
        self.assertIn("Seq assign file path:  %s" % seqAssignPath, self.__log.getvalue())

    def testUpdateModelWithoutSeqAssignFile(self) -> None:
        for seqAssignPath in (None, os.path.join(self.__dirPath, "missing.cif")):
            with self.subTest(seqAssignPath=seqAssignPath):
                self.mockDp.reset_mock()
                util = SeqdbUtils(verbose=False, log=self.__log)
                self.assertTrue(util.updateModelWithSeqAssignmentOp(**self._updateKwArgs(seqAssignPath)))
                self.mockDp.return_value.addInput.assert_not_called()
                self.mockDp.return_value.op.assert_called_once_with("annot-merge-sequence-data")

    def testUpdateModelFailure(self) -> None:
        self.mockDp.return_value.op.side_effect = RuntimeError("merge failed")
        util = SeqdbUtils(verbose=False, log=self.__log)
        self.assertFalse(util.updateModelWithSeqAssignmentOp(**self._updateKwArgs(None)))
        self.assertIn("merge failed", self.__log.getvalue())
        self.mockDi.assert_not_called()


if __name__ == "__main__":
    unittest.main()

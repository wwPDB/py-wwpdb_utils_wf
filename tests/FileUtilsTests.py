##
# File: FileUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the FileUtils plugin (real file system operations in a temporary directory)"""

import datetime
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from typing import Any, ClassVar, Dict, List, Optional
from unittest.mock import patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.FileUtils import FileUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


def fileObj(filePath: str) -> WfDataObject:
    """WfDataObject referencing an external file path"""
    wfo = WfDataObject()
    wfo.setExternalFilePath(filePath)
    return wfo


def valueObj(valueTypeName: str, containerTypeName: str = "value") -> WfDataObject:
    """WfDataObject used as a value container"""
    wfo = WfDataObject()
    wfo.setContainerTypeName(containerTypeName)
    wfo.setValueTypeName(valueTypeName)
    return wfo


class FakeWfDataObject:
    """Stand-in for WfDataObject used by batchCopyOp that resolves paths in a temporary directory"""

    instances: ClassVar[List["FakeWfDataObject"]] = []
    topPath: ClassVar[str] = ""

    def __init__(self) -> None:
        self.depId: Optional[str] = None
        self.wfInstId: Optional[str] = None
        self.storageType: Optional[str] = None
        self.contentType: Optional[str] = None
        self.formatType: Optional[str] = None
        self.versionId: Optional[str] = None
        self.partNo: Optional[int] = None
        FakeWfDataObject.instances.append(self)

    def setDepositionDataSetId(self, depId: str) -> None:
        self.depId = depId

    def setWorkflowInstanceId(self, wfInstId: str) -> None:
        self.wfInstId = wfInstId

    def setStorageType(self, storageType: str) -> None:
        self.storageType = storageType

    def setContentTypeAndFormat(self, contentType: str, formatType: str) -> None:
        self.contentType = contentType
        self.formatType = formatType

    def setVersionId(self, versionId: str) -> None:
        self.versionId = versionId

    def setPartitionNumber(self, partNo: int) -> None:
        self.partNo = partNo

    def getFilePathReference(self) -> str:
        fn = "%s_%s_P%s.%s.V%s" % (self.depId, self.contentType, self.partNo, self.formatType, self.versionId)
        return os.path.join(self.topPath, str(self.storageType), fn)


class FileUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__tmp = self.__tmpDir.name
        self.__lfh = io.StringIO()
        self.__fu = FileUtils(verbose=True, log=self.__lfh)

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def __write(self, name: str, content: str) -> str:
        fp = os.path.join(self.__tmp, name)
        with open(fp, "w") as ofh:
            ofh.write(content)
        return fp

    def __run(self, opName: str, inD: Dict[str, Any], outD: Optional[Dict[str, Any]] = None, uD: Optional[Dict[str, Any]] = None) -> bool:
        op = getattr(self.__fu, opName)
        ret: bool = op(inputObjectD=inD, outputObjectD=outD if outD is not None else {}, userParameterD=uD if uD is not None else {}, internalParameterD={})
        return ret

    def testCopyOp(self) -> None:
        src = self.__write("src.txt", "hello\nworld\n")
        dst = os.path.join(self.__tmp, "dst.txt")
        self.assertTrue(self.__run("copyOp", {"src": fileObj(src)}, {"dst": fileObj(dst)}))
        with open(dst) as ifh:
            self.assertEqual(ifh.read(), "hello\nworld\n")
        self.assertIn("+FileUtils.copyOp Input  path %s" % src, self.__lfh.getvalue())

    def testCopyOpMissingSource(self) -> None:
        dst = os.path.join(self.__tmp, "dst.txt")
        self.assertFalse(self.__run("copyOp", {"src": fileObj(os.path.join(self.__tmp, "missing.txt"))}, {"dst": fileObj(dst)}))
        self.assertFalse(os.path.exists(dst))
        self.assertIn("Traceback", self.__lfh.getvalue())

    def testCopyOpMissingArgs(self) -> None:
        self.assertFalse(self.__run("copyOp", {}, {}))

    def testCopyIfExistsOp(self) -> None:
        src = self.__write("src.txt", "data")
        dst = os.path.join(self.__tmp, "dst.txt")
        self.assertTrue(self.__run("copyIfExistsOp", {"src": fileObj(src)}, {"dst": fileObj(dst)}))
        with open(dst) as ifh:
            self.assertEqual(ifh.read(), "data")

    def testCopyIfExistsOpMissingSource(self) -> None:
        dst = os.path.join(self.__tmp, "dst.txt")
        self.assertTrue(self.__run("copyIfExistsOp", {"src": fileObj(os.path.join(self.__tmp, "missing.txt"))}, {"dst": fileObj(dst)}))
        self.assertFalse(os.path.exists(dst))

    def testCopyIfExistsOpAlwaysTrueOnError(self) -> None:
        # Exceptions are swallowed and True is returned
        self.assertTrue(self.__run("copyIfExistsOp", {}, {}))
        src = self.__write("src.txt", "data")
        badDst = os.path.join(self.__tmp, "nodir", "dst.txt")
        self.assertTrue(self.__run("copyIfExistsOp", {"src": fileObj(src)}, {"dst": fileObj(badDst)}))
        self.assertFalse(os.path.exists(badDst))

    def testMakeDirOp(self) -> None:
        newDir = os.path.join(self.__tmp, "a", "b")
        self.assertTrue(self.__run("makeDirOp", {"src": fileObj(newDir)}, uD={"mode": "755"}))
        self.assertTrue(os.path.isdir(newDir))
        if sys.platform != "win32":
            self.assertTrue(stat.S_IMODE(os.stat(newDir).st_mode) & stat.S_IRWXU == stat.S_IRWXU)

    def testMakeDirOpExisting(self) -> None:
        # Existing directory - mode is not consulted
        self.assertTrue(self.__run("makeDirOp", {"src": fileObj(self.__tmp)}, uD={}))

    def testMakeDirOpBadMode(self) -> None:
        newDir = os.path.join(self.__tmp, "c")
        self.assertFalse(self.__run("makeDirOp", {"src": fileObj(newDir)}, uD={"mode": "rwx"}))
        self.assertFalse(os.path.exists(newDir))
        self.assertFalse(self.__run("makeDirOp", {"src": fileObj(newDir)}, uD={}))

    def testSizeOfOp(self) -> None:
        src = self.__write("src.txt", "12345")
        dst = valueObj("integer")
        self.assertTrue(self.__run("sizeOfOp", {"src": fileObj(src)}, {"dst": dst}))
        self.assertEqual(dst.getValue(), 5)

    def testSizeOfOpMissing(self) -> None:
        dst = valueObj("integer")
        self.assertFalse(self.__run("sizeOfOp", {"src": fileObj(os.path.join(self.__tmp, "missing.txt"))}, {"dst": dst}))
        self.assertEqual(dst.getValue(), 0)

    def testSizeOfOpException(self) -> None:
        self.assertFalse(self.__run("sizeOfOp", {"src": fileObj(self.__write("x", "y"))}, {}))

    def testMtimeOp(self) -> None:
        src = self.__write("src.txt", "abc")
        tSec = 1700000000
        os.utime(src, (tSec, tSec))
        dst = valueObj("datetime")
        self.assertTrue(self.__run("mtimeOp", {"src": fileObj(src)}, {"dst": dst}))
        self.assertEqual(dst.getValue(), datetime.datetime.fromtimestamp(tSec, tz=datetime.timezone.utc))

    def testMtimeOpMissing(self) -> None:
        dst = valueObj("datetime")
        self.assertFalse(self.__run("mtimeOp", {"src": fileObj(os.path.join(self.__tmp, "missing.txt"))}, {"dst": dst}))
        self.assertIsNone(dst.getValue())

    def testMtimeOpException(self) -> None:
        self.assertFalse(self.__run("mtimeOp", {}, {}))

    def testDiffOp(self) -> None:
        src1 = self.__write("a.txt", "one\ntwo\nthree\n")
        src2 = self.__write("b.txt", "one\nTWO\nthree\n")
        dst = valueObj("string", "list")
        self.assertTrue(self.__run("diffOp", {"src1": fileObj(src1), "src2": fileObj(src2)}, {"dst": dst}))
        diffL = list(dst.getValue())
        self.assertEqual(diffL[0], "*** src1\n")
        self.assertEqual(diffL[1], "--- src2\n")
        self.assertIn("! two\n", diffL)
        self.assertIn("! TWO\n", diffL)

    def testDiffOpIdentical(self) -> None:
        src1 = self.__write("a.txt", "same\n")
        src2 = self.__write("b.txt", "same\n")
        dst = valueObj("string", "list")
        self.assertTrue(self.__run("diffOp", {"src1": fileObj(src1), "src2": fileObj(src2)}, {"dst": dst}))
        self.assertEqual(list(dst.getValue()), [])

    def testDiffOpMissingFile(self) -> None:
        src1 = self.__write("a.txt", "same\n")
        dst = valueObj("string", "list")
        self.assertFalse(self.__run("diffOp", {"src1": fileObj(src1), "src2": fileObj(os.path.join(self.__tmp, "missing"))}, {"dst": dst}))
        self.assertIsNone(dst.getValue())

    def __batchConfig(self, instructions: List[Any]) -> str:
        return self.__write("batch.json", json.dumps({"deposition-id": "D_000001", "copy-instructions": instructions}))

    def testBatchCopyOp(self) -> None:
        FakeWfDataObject.instances = []
        FakeWfDataObject.topPath = self.__tmp
        os.makedirs(os.path.join(self.__tmp, "archive"))
        self.__write(os.path.join("archive", "D_000001_model_P1.pdbx.V1"), "model-data")
        self.__write(os.path.join("archive", "D_000001_model-upload_P1.pdbx.V2"), "milestone-data")
        instructions = [
            [
                "copy",
                {
                    "src": {"location": "archive", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
                    "dst": {"location": "deposit", "content": "model", "format": "pdbx", "version": "3", "partno": 1},
                },
            ],
            [
                "copy",
                {
                    "src": {"location": "archive", "content": "model", "milestone": "upload", "format": "pdbx", "version": "2", "partno": 1},
                    "dst": {"location": "deposit", "content": "model", "milestone": "upload", "format": "pdbx", "version": "1", "partno": 1},
                },
            ],
            ["move", {"src": {}, "dst": {}}],
        ]
        cfg = self.__batchConfig(instructions)
        with patch("wwpdb.utils.wf.plugins.FileUtils.WfDataObject", FakeWfDataObject):
            self.assertTrue(self.__run("batchCopyOp", {"src": fileObj(cfg)}))

        with open(os.path.join(self.__tmp, "deposit", "D_000001_model_P1.pdbx.V3")) as ifh:
            self.assertEqual(ifh.read(), "model-data")
        with open(os.path.join(self.__tmp, "deposit", "D_000001_model-upload_P1.pdbx.V1")) as ifh:
            self.assertEqual(ifh.read(), "milestone-data")
        # "move" is skipped - only two copy instructions make objects
        self.assertEqual(len(FakeWfDataObject.instances), 4)
        for wfo in FakeWfDataObject.instances:
            self.assertEqual(wfo.depId, "D_000001")
            self.assertEqual(wfo.wfInstId, "W_001")
        self.assertIn("Created directory", self.__lfh.getvalue())

    def testBatchCopyOpFailedCopyContinues(self) -> None:
        FakeWfDataObject.instances = []
        FakeWfDataObject.topPath = self.__tmp
        os.makedirs(os.path.join(self.__tmp, "archive"))
        self.__write(os.path.join("archive", "D_000001_model_P1.pdbx.V2"), "v2")
        instructions = [
            [
                "copy",
                {
                    "src": {"location": "archive", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
                    "dst": {"location": "deposit", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
                },
            ],
            [
                "copy",
                {
                    "src": {"location": "archive", "content": "model", "format": "pdbx", "version": "2", "partno": 1},
                    "dst": {"location": "deposit", "content": "model", "format": "pdbx", "version": "2", "partno": 1},
                },
            ],
        ]
        cfg = self.__batchConfig(instructions)
        with patch("wwpdb.utils.wf.plugins.FileUtils.WfDataObject", FakeWfDataObject):
            self.assertTrue(self.__run("batchCopyOp", {"src": fileObj(cfg)}))
        self.assertFalse(os.path.exists(os.path.join(self.__tmp, "deposit", "D_000001_model_P1.pdbx.V1")))
        self.assertTrue(os.path.exists(os.path.join(self.__tmp, "deposit", "D_000001_model_P1.pdbx.V2")))
        self.assertIn("+FileUtils.batchCopyOp Failed copy", self.__lfh.getvalue())

    def testBatchCopyOpMalformedInstructionQuiet(self) -> None:
        FakeWfDataObject.instances = []
        FakeWfDataObject.topPath = self.__tmp
        os.makedirs(os.path.join(self.__tmp, "archive"))
        self.__write(os.path.join("archive", "D_000001_model_P1.pdbx.V1"), "v1")
        good = {
            "src": {"location": "archive", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
            "dst": {"location": "deposit", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
        }
        cfg = self.__batchConfig([["copy", {"dst": {}}], ["copy", good]])
        fu = FileUtils(verbose=False, log=io.StringIO())
        with patch("wwpdb.utils.wf.plugins.FileUtils.WfDataObject", FakeWfDataObject):
            self.assertTrue(fu.batchCopyOp(inputObjectD={"src": fileObj(cfg)}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.assertTrue(os.path.exists(os.path.join(self.__tmp, "deposit", "D_000001_model_P1.pdbx.V1")))

    def testBatchCopyOpMalformedInstructionVerbose(self) -> None:
        # Regression test: in verbose mode the inner error handler used to log src_path/dst_path before they were
        # assigned, so a malformed instruction raised UnboundLocalError and aborted the whole batch.  The bad entry is
        # now logged and skipped, and the next instruction still runs.
        FakeWfDataObject.instances = []
        FakeWfDataObject.topPath = self.__tmp
        os.makedirs(os.path.join(self.__tmp, "archive"))
        self.__write(os.path.join("archive", "D_000001_model_P1.pdbx.V1"), "v1")
        good = {
            "src": {"location": "archive", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
            "dst": {"location": "deposit", "content": "model", "format": "pdbx", "version": "1", "partno": 1},
        }
        cfg = self.__batchConfig([["copy", {"dst": {}}], ["copy", good]])
        with patch("wwpdb.utils.wf.plugins.FileUtils.WfDataObject", FakeWfDataObject):
            self.assertTrue(self.__run("batchCopyOp", {"src": fileObj(cfg)}))
        self.assertTrue(os.path.exists(os.path.join(self.__tmp, "deposit", "D_000001_model_P1.pdbx.V1")))
        self.assertIn("+FileUtils.batchCopyOp Failed copy: None -> None", self.__lfh.getvalue())

    def testBatchCopyOpNoInstructions(self) -> None:
        cfg = self.__write("batch.json", json.dumps({"deposition-id": "D_000001"}))
        self.assertTrue(self.__run("batchCopyOp", {"src": fileObj(cfg)}))

    def testBatchCopyOpBadConfig(self) -> None:
        cfg = self.__write("batch.json", "{not json")
        self.assertFalse(self.__run("batchCopyOp", {"src": fileObj(cfg)}))
        self.assertFalse(self.__run("batchCopyOp", {"src": fileObj(os.path.join(self.__tmp, "missing.json"))}))

    def testQuietFailureDoesNotLog(self) -> None:
        lfh = io.StringIO()
        fu = FileUtils(verbose=False, log=lfh)
        self.assertFalse(fu.copyOp(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.assertEqual(lfh.getvalue(), "")


if __name__ == "__main__":
    unittest.main()

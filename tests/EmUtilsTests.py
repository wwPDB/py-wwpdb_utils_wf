##
# File: EmUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the EmUtils plugin (RcsbDpUtility, ConfigInfo and PathInfo are mocked)"""

import io
import json
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, Optional
from unittest.mock import ANY, MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.EmUtils import EmUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODNAME = "wwpdb.utils.wf.plugins.EmUtils"


def mockObj(filePath: Optional[str], dirPath: Optional[str] = None, depId: Optional[str] = None, storageType: Optional[str] = None) -> MagicMock:
    wfo = MagicMock(spec=WfDataObject)
    wfo.getFilePathReference.return_value = filePath
    wfo.getDirPathReference.return_value = dirPath
    wfo.getDepositionDataSetId.return_value = depId
    wfo.getStorageType.return_value = storageType
    return wfo


def fakeGetFilePath(dataSetId: str, **kw: Any) -> str:
    return "/%s/%s/%s.%s.P%s.%s.%s" % (kw["fileSource"], dataSetId, kw["contentType"], kw["formatType"], kw["partNumber"], kw["versionId"], kw["mileStone"])


class EmUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.__tmp = self.__tmpDir.name
        self.__lfh = io.StringIO()
        self.__inp = os.path.join(self.__tmp, "input.map")
        self.__out = os.path.join(self.__tmp, "output.map")
        self.__rpt = os.path.join(self.__tmp, "report.json")
        self.__log = os.path.join(self.__tmp, "run.log")
        patcherDp = patch(MODNAME + ".RcsbDpUtility")
        patcherCi = patch(MODNAME + ".ConfigInfo")
        patcherPi = patch(MODNAME + ".PathInfo")
        self.__mockDpCls = patcherDp.start()
        mockCiCls = patcherCi.start()
        self.__mockPiCls = patcherPi.start()
        mockCiCls.return_value.get.return_value = "TESTSITE"
        self.__mockPiCls.return_value.getFilePath.side_effect = fakeGetFilePath
        for p in (patcherDp, patcherCi, patcherPi):
            self.addCleanup(p.stop)
        self.__dp = self.__mockDpCls.return_value

    def tearDown(self) -> None:
        self.__tmpDir.cleanup()

    def __args(self, uD: Optional[Dict[str, Any]] = None, nDst: int = 2) -> Dict[str, Any]:
        outD: Dict[str, Any] = {"dst1": mockObj(self.__out, self.__tmp)}
        if nDst == 2:  # noqa: PLR2004
            outD["dst2"] = mockObj(self.__log)
        else:
            outD["dst2"] = mockObj(self.__rpt)
            outD["dst3"] = mockObj(self.__log)
        return {"inputObjectD": {"src": mockObj(self.__inp)}, "outputObjectD": outD, "userParameterD": uD if uD is not None else {}, "internalParameterD": {}}

    def __checkCtor(self) -> None:
        self.__mockDpCls.assert_called_once_with(tmpPath=self.__tmp, siteId="TESTSITE", verbose=True, log=self.__lfh)

    def testFscCheckOptions(self) -> None:
        self.__dp.op.return_value = 0
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertEqual(eu.fsc_check_options(**self.__args({"options": "-v"})), 0)
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.addInput(name="options", value="-v"), call.op("fsc_check"), call.expLog(self.__log), call.exp(self.__out), call.cleanup()],
        )

    def testFscCheckOptionsEmptyOptions(self) -> None:
        self.__dp.op.return_value = 3
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertEqual(eu.fsc_check_options(**self.__args({"options": ""})), 3)
        self.__dp.addInput.assert_not_called()

    def testFscCheckOptionsException(self) -> None:
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertEqual(eu.fsc_check_options(**self.__args({})), -100)
        self.assertIn("KeyError", self.__lfh.getvalue())

    def testImageMagickOp(self) -> None:
        self.__dp.op.return_value = 0
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertEqual(eu.imageMagickOp(**self.__args({"options": "-resize 400x400"})), 0)
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.addInput(name="options", value="-resize 400x400"), call.op("img-convert"), call.expLog(self.__log), call.exp(self.__out), call.cleanup()],
        )

    def testImageMagickOpException(self) -> None:
        self.__dp.op.side_effect = RuntimeError("convert failed")
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertEqual(eu.imageMagickOp(**self.__args({"options": ""})), -100)
        self.assertIn("convert failed", self.__lfh.getvalue())

    def testMapFixOp(self) -> None:
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertTrue(eu.mapFixOp(**self.__args({"options": "-label x"})))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [call.imp(self.__inp), call.addInput(name="options", value="-label x"), call.op("mapfix-big"), call.expLog(self.__log), call.exp(self.__out), call.cleanup()],
        )

    def testMapFixInPlaceOp(self) -> None:
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceOp(**self.__args({"options": "-voxel 1.0"}, nDst=3)))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.setDebugMode(flag=True),
                call.addInput(name="options", value="-voxel 1.0"),
                call.addInput(name="input_map_file_path", value=self.__inp),
                call.addInput(name="output_map_file_path", value=self.__out),
                call.op("deposit-update-map-header-in-place"),
                call.exp(self.__rpt),
                call.expLog(self.__log),
                call.cleanup(),
            ],
        )

    def testEmmapcheck(self) -> None:
        eu = EmUtils(verbose=True, log=self.__lfh)
        args = {
            "inputObjectD": {"src": mockObj("/in/check.json")},
            "outputObjectD": {"dst": mockObj("/out/check.json", self.__tmp)},
            "userParameterD": {},
            "internalParameterD": {},
        }
        self.assertTrue(eu.emmapcheck(**args))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.setDebugMode(flag=True),
                call.addInput(name="input_file_path", value="/in/check.json"),
                call.addInput(name="output_file_path", value="/out/check.json"),
                call.op("em-map-model-upload-check"),
                call.cleanup(),
            ],
        )

    def testEm2emSpiderOp(self) -> None:
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertTrue(eu.em2emSpiderOp(**self.__args({"pixel-spacing-x": 1.5, "pixel-spacing-y": 2.0, "pixel-spacing-z": 2.5})))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.imp(self.__inp),
                call.addInput(name="pixel-spacing-x", value="1.5"),
                call.addInput(name="pixel-spacing-y", value="2.0"),
                call.addInput(name="pixel-spacing-z", value="2.5"),
                call.op("em2em-spider"),
                call.expLog(self.__log),
                call.exp(self.__out),
                call.cleanup(),
            ],
        )

    def __altArgs(self, argsPath: str) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src1": mockObj(self.__inp), "src2": mockObj(argsPath)},
            "outputObjectD": {"dst1": mockObj(self.__out, self.__tmp), "dst2": mockObj(self.__rpt), "dst3": mockObj(self.__log)},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def testMapFixInPlaceAltOp(self) -> None:
        argsPath = os.path.join(self.__tmp, "args.txt")
        with open(argsPath, "w") as ofh:
            ofh.write("-voxel 1.1,1.1,1.1")
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceAltOp(**self.__altArgs(argsPath)))
        self.__checkCtor()
        self.assertEqual(
            self.__dp.method_calls,
            [
                call.setDebugMode(flag=True),
                call.addInput(name="options", value="-voxel 1.1,1.1,1.1"),
                call.addInput(name="input_map_file_path", value=self.__inp),
                call.addInput(name="output_map_file_path", value=self.__out),
                call.op("annot-update-map-header-in-place"),
                call.exp(self.__rpt),
                call.expLog(self.__log),
                call.cleanup(),
            ],
        )

    def testMapFixInPlaceAltOpNoArgsFile(self) -> None:
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceAltOp(**self.__altArgs(os.path.join(self.__tmp, "missing.txt"))))
        self.assertNotIn(call.addInput(name="options", value=ANY), self.__dp.method_calls)
        self.__dp.op.assert_called_once_with("annot-update-map-header-in-place")

    def __cfgArgs(self, cfgPath: str) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src1": mockObj(cfgPath, self.__tmp, depId="D_000001", storageType="archive")},
            "outputObjectD": {},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def testMapFixInPlaceCfgOp(self) -> None:
        cfgPath = os.path.join(self.__tmp, "mapfix.json")
        cfg = {"part-list": [1, 2], "map-content-type": "em-half-volume", "map-content-milestone": "upload", "cmd-line-arg-list": ["-voxel 1", "-voxel 2"]}
        with open(cfgPath, "w") as ofh:
            json.dump(cfg, ofh)
        eu = EmUtils(verbose=True, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceCfgOp(**self.__cfgArgs(cfgPath)))
        self.__mockPiCls.assert_called_once_with(siteId="TESTSITE", verbose=True, log=self.__lfh)
        self.assertEqual(self.__mockDpCls.call_count, 2)
        self.assertEqual(self.__dp.cleanup.call_count, 2)
        for p, arg in [(1, "-voxel 1"), (2, "-voxel 2")]:
            self.assertIn(call.addInput(name="options", value=arg), self.__dp.method_calls)
            self.assertIn(
                call.addInput(name="input_map_file_path", value="/archive/D_000001/em-half-volume.map.P%d.latest.upload" % p),
                self.__dp.method_calls,
            )
            self.assertIn(
                call.addInput(name="output_map_file_path", value="/archive/D_000001/em-half-volume.map.P%d.next.None" % p),
                self.__dp.method_calls,
            )
            self.assertIn(call.exp("/archive/D_000001/mapfix-header-report.json.P%d.next.None" % p), self.__dp.method_calls)
            self.assertIn(call.expLog("/archive/D_000001/mapfix-report.txt.P%d.next.None" % p), self.__dp.method_calls)
        self.assertEqual(self.__dp.op.call_args_list, [call("deposit-update-map-header-in-place")] * 2)

    def testMapFixInPlaceCfgOpNoMilestone(self) -> None:
        cfgPath = os.path.join(self.__tmp, "mapfix.json")
        with open(cfgPath, "w") as ofh:
            json.dump({"part-list": [3], "map-content-type": "em-volume", "cmd-line-arg-list": ["-x"]}, ofh)
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceCfgOp(**self.__cfgArgs(cfgPath)))
        self.assertIn(call.addInput(name="input_map_file_path", value="/archive/D_000001/em-volume.map.P3.latest.None"), self.__dp.method_calls)

    def testMapFixInPlaceCfgOpBadConfig(self) -> None:
        cfgPath = os.path.join(self.__tmp, "mapfix.json")
        with open(cfgPath, "w") as ofh:
            json.dump({"part-list": [1]}, ofh)
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertTrue(eu.mapFixInPlaceCfgOp(**self.__cfgArgs(cfgPath)))
        self.__mockDpCls.assert_not_called()
        self.assertIn("failed processing configuration file", self.__lfh.getvalue())

    def testMapFixInPlaceCfgOpDpFailure(self) -> None:
        cfgPath = os.path.join(self.__tmp, "mapfix.json")
        with open(cfgPath, "w") as ofh:
            json.dump({"part-list": [1], "map-content-type": "em-volume", "cmd-line-arg-list": ["-x"]}, ofh)
        self.__dp.op.side_effect = RuntimeError("mapfix failed")
        eu = EmUtils(verbose=False, log=self.__lfh)
        self.assertFalse(eu.mapFixInPlaceCfgOp(**self.__cfgArgs(cfgPath)))
        self.assertIn("mapfix failed", self.__lfh.getvalue())

    def testBooleanOpsReturnFalseOnException(self) -> None:
        self.__dp.op.side_effect = RuntimeError("dp failure")
        argsPath = os.path.join(self.__tmp, "missing.txt")
        cases = [
            ("mapFixOp", self.__args({"options": "x"})),
            ("mapFixInPlaceOp", self.__args({"options": "x"}, nDst=3)),
            ("em2emSpiderOp", self.__args({"pixel-spacing-x": 1, "pixel-spacing-y": 1, "pixel-spacing-z": 1})),
            ("mapFixInPlaceAltOp", self.__altArgs(argsPath)),
            ("emmapcheck", {"inputObjectD": {"src": mockObj("a")}, "outputObjectD": {"dst": mockObj("b", self.__tmp)}, "userParameterD": {}, "internalParameterD": {}}),
        ]
        for opName, args in cases:
            with self.subTest(op=opName):
                lfh = io.StringIO()
                eu = EmUtils(verbose=False, log=lfh)
                self.assertFalse(getattr(eu, opName)(**args))
                self.assertIn("RuntimeError: dp failure", lfh.getvalue())

    def testBooleanOpsReturnFalseOnMissingArgs(self) -> None:
        eu = EmUtils(verbose=False, log=io.StringIO())
        for opName in ["mapFixOp", "mapFixInPlaceOp", "emmapcheck", "em2emSpiderOp", "mapFixInPlaceAltOp", "mapFixInPlaceCfgOp"]:
            with self.subTest(op=opName):
                self.assertFalse(getattr(eu, opName)(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.__mockDpCls.assert_not_called()


if __name__ == "__main__":
    unittest.main()

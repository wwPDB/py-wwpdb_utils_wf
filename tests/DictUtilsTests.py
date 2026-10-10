##
# File: DictUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the DictUtils plugin (InstanceMapper and ConfigInfoAppEm are mocked)"""

import io
import sys
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.DictUtils import DictUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject


def mockObj(filePath: str) -> MagicMock:
    wfo = MagicMock(spec=WfDataObject)
    wfo.getFilePathReference.return_value = filePath
    return wfo


class DictUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__lfh = io.StringIO()
        patcherIm = patch("wwpdb.utils.wf.plugins.DictUtils.InstanceMapper")
        patcherCi = patch("wwpdb.utils.wf.plugins.DictUtils.ConfigInfoAppEm")
        self.__mockImCls = patcherIm.start()
        self.__mockCiCls = patcherCi.start()
        self.addCleanup(patcherIm.stop)
        self.addCleanup(patcherCi.stop)
        self.__mockCiCls.return_value.get_emd_mapping_file_path.return_value = "/map/emd-mapping.cif"
        self.__im = self.__mockImCls.return_value

    def __args(self) -> Dict[str, Any]:
        return {
            "inputObjectD": {"src": mockObj("/in/model.cif")},
            "outputObjectD": {"dst": mockObj("/out/model-emd.cif")},
            "userParameterD": {},
            "internalParameterD": {},
        }

    def testEm2EmdOp(self) -> None:
        self.__im.translate.return_value = True
        du = DictUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.em2emdOp(**self.__args()))
        self.__mockImCls.assert_called_once_with(verbose=True, log=self.__lfh)
        self.__im.setMappingFilePath.assert_called_once_with("/map/emd-mapping.cif")
        self.__im.translate.assert_called_once_with("/in/model.cif", "/out/model-emd.cif", mode="src-dst")
        self.assertIn("+DictUtils em2emdOp return status True", self.__lfh.getvalue())
        self.assertIn("Output result path: /out/model-emd.cif", self.__lfh.getvalue())

    def testEmd2EmOp(self) -> None:
        self.__im.translate.return_value = True
        du = DictUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.emd2emOp(**self.__args()))
        self.__im.setMappingFilePath.assert_called_once_with("/map/emd-mapping.cif")
        self.__im.translate.assert_called_once_with("/in/model.cif", "/out/model-emd.cif", mode="dst-src")
        self.assertIn("+DictUtils emd2emOp return status True", self.__lfh.getvalue())
        self.assertIn("+DictUtils.emd2emOp() - Input model PDBx file path: /in/model.cif", self.__lfh.getvalue())

    def testTranslateStatusPropagated(self) -> None:
        self.__im.translate.return_value = False
        du = DictUtils(verbose=False, log=self.__lfh)
        self.assertFalse(du.em2emdOp(**self.__args()))
        self.assertFalse(du.emd2emOp(**self.__args()))

    def testExceptionReturnsFalse(self) -> None:
        self.__im.translate.side_effect = OSError("cannot read")
        for opName in ["em2emdOp", "emd2emOp"]:
            with self.subTest(op=opName):
                lfh = io.StringIO()
                du = DictUtils(verbose=False, log=lfh)
                self.assertFalse(getattr(du, opName)(**self.__args()))
                self.assertIn("cannot read", lfh.getvalue())

    def testMissingArgsReturnsFalse(self) -> None:
        du = DictUtils(verbose=False, log=self.__lfh)
        self.assertFalse(du.em2emdOp(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.assertFalse(du.emd2emOp(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.__mockImCls.assert_not_called()


if __name__ == "__main__":
    unittest.main()

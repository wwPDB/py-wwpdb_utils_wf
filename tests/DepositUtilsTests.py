##
# File: DepositUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the DepositUtils plugin (DepositDataSync and ConfigInfo are mocked)"""

import io
import sys
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.DepositUtils import DepositUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODNAME = "wwpdb.utils.wf.plugins.DepositUtils"


class DepositUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__lfh = io.StringIO()
        # The optional deposit package may not be installed - create=True allows patching absent names
        patchers = {
            "ConfigInfo": patch(MODNAME + ".ConfigInfo"),
            "DepositDataSync": patch(MODNAME + ".DepositDataSync", create=True),
            "SyncDirection": patch(MODNAME + ".SyncDirection", create=True),
            "print_sync_result": patch(MODNAME + ".print_sync_result", create=True),
        }
        self.__mocks: Dict[str, MagicMock] = {}
        for name, patcher in patchers.items():
            self.__mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)
        self.__syncer = self.__mocks["DepositDataSync"].return_value

    def __setStoragePath(self, value: Optional[str]) -> None:
        self.__mocks["ConfigInfo"].return_value.get.return_value = value

    def __args(self, depId: str = "D_000001") -> Dict[str, Any]:
        src = MagicMock(spec=WfDataObject)
        src.getDepositionDataSetId.return_value = depId
        return {"inputObjectD": {"src": src}, "outputObjectD": {}, "userParameterD": {}, "internalParameterD": {}}

    def testSkipWhenNoStoragePath(self) -> None:
        self.__setStoragePath(None)
        du = DepositUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.syncToDepositOp(**self.__args()))
        self.__mocks["ConfigInfo"].return_value.get.assert_called_once_with("SITE_ARCHIVE_UI_STORAGE_PATH")
        self.__mocks["DepositDataSync"].assert_not_called()
        self.assertIn("No archive UI storage path configured", self.__lfh.getvalue())

    def testSyncSuccess(self) -> None:
        self.__setStoragePath("/ui/storage")
        result = {"success": True}
        self.__syncer.sync_single.return_value = result
        du = DepositUtils(verbose=True, log=self.__lfh)
        self.assertTrue(du.syncToDepositOp(**self.__args("D_1000000001")))
        self.__syncer.sync_single.assert_called_once_with("D_1000000001", self.__mocks["SyncDirection"].TO_DEPOSIT)
        self.__mocks["print_sync_result"].assert_called_once_with(result, self.__lfh)
        self.assertIn("starting sync to deposit", self.__lfh.getvalue())

    def testSyncFailureExits(self) -> None:
        self.__setStoragePath("/ui/storage")
        self.__syncer.sync_single.return_value = {"success": False}
        du = DepositUtils(verbose=True, log=self.__lfh)
        with self.assertRaises(SystemExit) as cm:
            du.syncToDepositOp(**self.__args())
        self.assertEqual(cm.exception.code, 1)

    def testSyncExceptionReturnsFalse(self) -> None:
        self.__setStoragePath("/ui/storage")
        self.__syncer.sync_single.side_effect = RuntimeError("sync broke")
        du = DepositUtils(verbose=True, log=self.__lfh)
        self.assertFalse(du.syncToDepositOp(**self.__args()))
        self.assertIn("RuntimeError: sync broke", self.__lfh.getvalue())

    def testExceptionQuietWhenNotVerbose(self) -> None:
        du = DepositUtils(verbose=False, log=self.__lfh)
        self.assertFalse(du.syncToDepositOp(inputObjectD={}, outputObjectD={}, userParameterD={}, internalParameterD={}))
        self.assertEqual(self.__lfh.getvalue(), "")


if __name__ == "__main__":
    unittest.main()

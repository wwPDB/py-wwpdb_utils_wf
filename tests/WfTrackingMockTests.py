##
# File: WfTrackingMockTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for WfTracking with WfDbApi mocked"""

import io
import sys
import unittest
from decimal import Decimal
from typing import Dict, Optional, Tuple
from unittest.mock import patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.dbapi.WfTracking import WfTracking

MODULE = "wwpdb.utils.wf.dbapi.WfTracking"
NOW = Decimal("845000000.123")
EXPECTED_SQL = "update wf_instance_last set status_timestamp=845000000.123, inst_status='open' where dep_set_id = 'D_1' and wf_class_id = 'Annotate' and wf_inst_id = 'W_000001'"
EXPECTED_INST = {"WF_INST_ID": "W_000001", "WF_CLASS_ID": "Annotate", "DEP_SET_ID": "D_1", "INST_STATUS": "open", "STATUS_TIMESTAMP": NOW}


class WfTrackingMockTests(unittest.TestCase):
    def setUp(self) -> None:
        apiPatcher = patch(MODULE + ".WfDbApi")
        self.mApiCls = apiPatcher.start()
        self.addCleanup(apiPatcher.stop)
        timePatcher = patch(MODULE + ".getTimeNow", return_value=NOW)
        timePatcher.start()
        self.addCleanup(timePatcher.stop)
        self.mApi = self.mApiCls.return_value
        self.log = io.StringIO()

    def _run(self, verbose: bool = False) -> bool:
        wft = WfTracking(verbose=verbose, log=self.log)
        ok: bool = wft.setInstanceStatus(depId="D_1", instId="W_000001", classId="Annotate", status="open")
        return ok

    def testExistingRecordIsUpdated(self) -> None:
        self.mApi.getObject.return_value = {"WF_INST_ID": "W_000001"}
        self.mApi.runUpdateSQL.return_value = 1
        self.assertTrue(self._run())
        self.mApiCls.assert_called_once_with(verbose=False)
        self.mApi.getObject.assert_called_once_with("D_1", "Annotate", "W_000001")
        self.mApi.saveObject.assert_not_called()
        self.mApi.runUpdateSQL.assert_called_once_with(EXPECTED_SQL)
        self.mApi.updateStatus.assert_called_once_with(EXPECTED_INST, "open")
        self.assertEqual(self.log.getvalue(), "")

    def testMissingRecordIsInserted(self) -> None:
        cases: Tuple[Optional[Dict[str, str]], ...] = (None, {})
        for missing in cases:
            with self.subTest(missing=missing):
                self.mApi.reset_mock()
                self.mApi.getObject.return_value = missing
                self.mApi.runUpdateSQL.return_value = 1
                self.assertTrue(self._run())
                self.mApi.saveObject.assert_called_once_with(EXPECTED_INST, "insert")
                self.assertIn("no status records for depId D_1", self.log.getvalue())

    def testUpdateNotOwnedFails(self) -> None:
        self.mApi.getObject.return_value = {"x": 1}
        self.mApi.runUpdateSQL.return_value = 0
        self.assertFalse(self._run())
        self.mApi.updateStatus.assert_not_called()
        self.assertIn("current task does not control the workflow", self.log.getvalue())

    @unittest.expectedFailure
    def testUpdateDbErrorFails(self) -> None:
        # Library bug: runUpdateSQL returns None on a DB error and "None < 1" raises TypeError instead of returning False
        self.mApi.getObject.return_value = {"x": 1}
        self.mApi.runUpdateSQL.return_value = None
        self.assertFalse(self._run())

    def testVerboseVerifiesStatus(self) -> None:
        self.mApi.getObject.side_effect = [{"x": 1}, {"INST_STATUS": "open"}]
        self.mApi.runUpdateSQL.return_value = 1
        self.mApi.getStatus.return_value = "open"
        self.assertTrue(self._run(verbose=True))
        self.mApiCls.assert_called_once_with(verbose=True)
        self.assertEqual(self.mApi.getObject.call_count, 2)
        self.mApi.getStatus.assert_called_once_with({"INST_STATUS": "open"})
        self.assertIn("verified new status is: 'open'", self.log.getvalue())


if __name__ == "__main__":
    unittest.main()

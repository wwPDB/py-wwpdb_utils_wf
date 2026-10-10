##
# File: StatusDbApiTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for StatusDbApi with ConfigInfo and the database layer mocked"""

import io
import sys
import unittest
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

# A real MySQLdb.connect() imports MySQLdb.cursors as a side effect; with connect mocked, import it explicitly
import MySQLdb.cursors  # noqa: F401 pylint: disable=unused-import

from wwpdb.utils.wf.dbapi.StatusDbApi import StatusDbApi

MODULE = "wwpdb.utils.wf.dbapi.StatusDbApi"

SITE_CONFIG: Dict[str, Optional[str]] = {
    "SITE_DB_SERVER": "mysql",
    "SITE_DB_HOST_NAME": "dbhost",
    "SITE_DB_DATABASE_NAME": "status",
    "SITE_DB_USER_NAME": "wfuser",
    "SITE_DB_PASSWORD": "secret",
    "SITE_DB_SOCKET": None,
    "SITE_DB_PORT_NUMBER": "3306",
}


def _configInfo() -> MagicMock:
    cI = MagicMock()
    cI.return_value.get.side_effect = SITE_CONFIG.get
    return cI


class StatusDbApiTests(unittest.TestCase):
    """StatusDbApi against a mocked DbApiUtil"""

    def setUp(self) -> None:
        cIPatcher = patch(MODULE + ".ConfigInfo", new=_configInfo())
        self.mCI = cIPatcher.start()
        self.addCleanup(cIPatcher.stop)
        utilPatcher = patch(MODULE + ".DbApiUtil")
        self.mUtilCls = utilPatcher.start()
        self.addCleanup(utilPatcher.stop)
        self.mUtil = self.mUtilCls.return_value
        self.log = io.StringIO()
        self.api = StatusDbApi(siteId="WWPDB_DEPLOY_TEST", verbose=True, log=self.log)

    def testConstructor(self) -> None:
        self.mCI.assert_called_once_with("WWPDB_DEPLOY_TEST")
        self.mUtilCls.assert_called_once_with(
            dbServer="mysql", dbHost="dbhost", dbName="status", dbUser="wfuser", dbPw="secret", dbSocket=None, dbPort=3306, verbose=True, log=self.log
        )
        schemaMap = self.mUtil.setSchemaMap.call_args.args[0]
        self.assertEqual(set(schemaMap.keys()), {"GET_GROUP_ID", "GET_DEP_ID"})

    def testGetGroupId(self) -> None:
        self.mUtil.selectData.return_value = ({"group_id": "G_1002001"},)
        self.assertEqual(self.api.getGroupId("D_1000000001"), "G_1002001")
        self.mUtil.selectData.assert_called_once_with(key="GET_GROUP_ID", parameter="D_1000000001")

    def testGetGroupIdNoResult(self) -> None:
        self.mUtil.selectData.return_value = ()
        self.assertIsNone(self.api.getGroupId("D_1000000001"))
        self.mUtil.selectData.return_value = ({"group_id": None},)
        self.assertIsNone(self.api.getGroupId("D_1000000001"))

    def testGetGroupIdNoDepId(self) -> None:
        self.assertIsNone(self.api.getGroupId(None))
        self.assertIsNone(self.api.getGroupId(""))
        self.mUtil.selectData.assert_not_called()

    def testGetEntryIdList(self) -> None:
        self.mUtil.selectData.return_value = ({"dep_set_id": "D_1"}, {"dep_set_id": None}, {"other": 1}, {"dep_set_id": "D_2"})
        self.assertEqual(self.api.getEntryIdList("G_1"), ["D_1", "D_2"])
        self.mUtil.selectData.assert_called_once_with(key="GET_DEP_ID", parameter="G_1")

    def testGetEntryIdListNoGroup(self) -> None:
        self.assertEqual(self.api.getEntryIdList(None), [])
        self.mUtil.selectData.assert_not_called()

    def testRunUpdate(self) -> None:
        self.mUtil.runUpdate.return_value = "OK"
        self.assertEqual(self.api.runUpdate(table="t", where={"a": "1"}, data={"b": "2"}), "OK")
        self.mUtil.runUpdate.assert_called_once_with(table="t", where={"a": "1"}, data={"b": "2"})


class StatusDbApiSqlTests(unittest.TestCase):
    """StatusDbApi through the real DbApiUtil, with only the connection mocked"""

    def setUp(self) -> None:
        cIPatcher = patch(MODULE + ".ConfigInfo", new=_configInfo())
        cIPatcher.start()
        self.addCleanup(cIPatcher.stop)
        connPatcher = patch("wwpdb.utils.wf.dbapi.DbApiUtil.DbConnection")
        mConnCls = connPatcher.start()
        self.addCleanup(connPatcher.stop)
        self.curs = mConnCls.return_value.connect.return_value.cursor.return_value
        self.api = StatusDbApi(log=io.StringIO())

    def testGetGroupIdSql(self) -> None:
        self.curs.fetchall.return_value = ({"group_id": "G_1"},)
        self.assertEqual(self.api.getGroupId("D_1"), "G_1")
        self.curs.execute.assert_called_once_with("select group_id from group_deposition_information where dep_set_id = 'D_1'")

    def testGetEntryIdListSql(self) -> None:
        self.curs.fetchall.return_value = ({"dep_set_id": "D_1"}, {"dep_set_id": "D_2"})
        self.assertEqual(self.api.getEntryIdList("G_1"), ["D_1", "D_2"])
        self.curs.execute.assert_called_once_with("select dep_set_id from group_deposition_information where group_id = 'G_1'")


if __name__ == "__main__":
    unittest.main()

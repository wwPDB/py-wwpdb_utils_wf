##
# File: DbApiUtilTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for DbApiUtil with the DbConnection collaborator mocked"""

import io
import sys
import unittest
from typing import Any, List
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

import MySQLdb
import MySQLdb.cursors

from wwpdb.utils.wf.dbapi.DbApiUtil import DbApiUtil

MODULE = "wwpdb.utils.wf.dbapi.DbApiUtil"


class DbApiUtilTests(unittest.TestCase):
    def setUp(self) -> None:
        dbConnPatcher = patch(MODULE + ".DbConnection")
        self.mDbConnCls = dbConnPatcher.start()
        self.addCleanup(dbConnPatcher.stop)
        timePatcher = patch(MODULE + ".time")
        self.mTime = timePatcher.start()
        self.addCleanup(timePatcher.stop)
        self.myDb = self.mDbConnCls.return_value
        self.con = MagicMock(name="con1")
        self.myDb.connect.return_value = self.con
        self.log = io.StringIO()
        self.api = DbApiUtil(dbServer="mysql", dbHost="h", dbName="n", dbUser="u", dbPw="p", dbSocket="/s", dbPort=3306, log=self.log)

    def _executed(self, con: MagicMock) -> List[Any]:
        return [c.args[0] for c in con.cursor.return_value.execute.call_args_list]

    def testConstructorConnects(self) -> None:
        self.mDbConnCls.assert_called_once_with(dbServer="mysql", dbHost="h", dbName="n", dbUser="u", dbPw="p", dbPort=3306, dbSocket="/s")
        self.myDb.connect.assert_called_once_with()

    def testRunSelectSQL(self) -> None:
        rows = ({"a": 1}, {"a": 2})
        self.con.cursor.return_value.fetchall.return_value = rows
        self.assertEqual(self.api.runSelectSQL("select a from t"), rows)
        self.con.commit.assert_called_once_with()
        self.con.cursor.assert_called_once_with(MySQLdb.cursors.DictCursor)
        self.con.cursor.return_value.execute.assert_called_once_with("select a from t")

    def testRunSelectSQLErrorReturnsEmpty(self) -> None:
        self.con.cursor.return_value.execute.side_effect = MySQLdb.ProgrammingError(1146, "no table")
        self.assertEqual(self.api.runSelectSQL("select a from t"), ())
        self.assertIn("Database error 1146: no table", self.log.getvalue())

    @unittest.expectedFailure
    def testRunSelectSQLRetriesAfterLostConnection(self) -> None:
        # Library bug: the private select returns () rather than None on error, so the retry/reconnect loop never runs
        self.con.cursor.return_value.execute.side_effect = MySQLdb.OperationalError(2006, "gone away")
        con2 = MagicMock(name="con2")
        con2.cursor.return_value.fetchall.return_value = ({"a": 1},)
        self.myDb.connect.return_value = con2
        self.assertEqual(self.api.runSelectSQL("select a from t"), ({"a": 1},))

    def testRunUpdateSQL(self) -> None:
        self.assertEqual(self.api.runUpdateSQL("update t set a=1"), "OK")
        self.assertEqual(self._executed(self.con), ["set autocommit=0", "update t set a=1", "set autocommit=1"])
        self.con.commit.assert_called_once_with()
        self.con.cursor.return_value.close.assert_called_once_with()

    def testRunUpdateSQLReconnectsAndRetries(self) -> None:
        def _execute(query: str) -> int:
            if query.startswith("update"):
                raise MySQLdb.OperationalError(2006, "gone away")
            return 0

        self.con.cursor.return_value.execute.side_effect = _execute
        con2 = MagicMock(name="con2")
        self.myDb.connect.return_value = con2
        self.assertEqual(self.api.runUpdateSQL("update t set a=1"), "OK")
        self.con.rollback.assert_called_once_with()
        self.myDb.close.assert_called_once_with(self.con)
        self.assertEqual(self.myDb.connect.call_count, 2)
        self.assertIn("update t set a=1", self._executed(con2))
        self.mTime.sleep.assert_called_once_with(2)

    def testRunUpdateSQLReconnectFails(self) -> None:
        self.con.cursor.return_value.execute.side_effect = MySQLdb.OperationalError(2006, "gone away")
        self.myDb.close.side_effect = MySQLdb.OperationalError(2006, "gone away")
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "cannot connect")
        self.assertIsNone(self.api.runUpdateSQL("update t set a=1"))
        self.assertIn("DB connection lost - cannot close", self.log.getvalue())
        self.assertIn("Cannot get re-connection", self.log.getvalue())
        # 1 initial connect + 4 reconnection attempts
        self.assertEqual(self.myDb.connect.call_count, 5)

    def testRunUpdateSQLUnhandledError(self) -> None:
        self.con.cursor.return_value.execute.side_effect = MySQLdb.Error(0, "odd")
        self.assertIsNone(self.api.runUpdateSQL("update t set a=1"))
        self.myDb.close.assert_not_called()
        self.mTime.sleep.assert_not_called()

    def testRunUpdateMissingArgs(self) -> None:
        self.assertIsNone(self.api.runUpdate(table=None, where={"a": "1"}))
        self.assertIsNone(self.api.runUpdate(table="t"))
        self.con.cursor.assert_not_called()

    def testRunUpdateRowExistsNoData(self) -> None:
        self.con.cursor.return_value.fetchall.return_value = ({"a": "1"},)
        self.assertEqual(self.api.runUpdate(table="t", where={"a": "1"}), "OK")
        self.assertEqual(self._executed(self.con), ["select * from t where a = '1'"])

    def testRunUpdateRowExistsUpdates(self) -> None:
        self.con.cursor.return_value.fetchall.return_value = ({"a": "1"},)
        self.assertEqual(self.api.runUpdate(table="t", where={"a": "1", "b": "x'y"}, data={"c": "it's"}), "OK")
        executed = self._executed(self.con)
        self.assertEqual(executed[0], "select * from t where a = '1' and b = 'x\\'y'")
        self.assertIn("update t set c = 'it\\'s' where a = '1' and b = 'x\\'y'", executed)

    def testRunUpdateInsertsNewRow(self) -> None:
        self.con.cursor.return_value.fetchall.return_value = ()
        self.assertEqual(self.api.runUpdate(table="t", where={"a": "1"}, data={"c": "o'k", "d": "2"}), "OK")
        self.assertIn("insert into t (a,c,d) values ('1','o\\'k','2')", self._executed(self.con))

    @unittest.expectedFailure
    def testRunUpdateDataOnlyInserts(self) -> None:
        # Library bug: with data but no where clause the insert branch iterates where.items() on None
        self.assertEqual(self.api.runUpdate(table="t", data={"c": "1"}), "OK")

    def testSelectDataAndUpdateWithKey(self) -> None:
        self.assertIsNone(self.api.selectData(key="Q"))
        self.assertIsNone(self.api.runUpdateSQLwithKey(key="U"))
        self.api.setSchemaMap({"Q": "select * from t where id = '%s'", "U": "delete from t", "Q2": "select 1"})
        self.assertIsNone(self.api.selectData(key=None))
        self.assertIsNone(self.api.selectData(key="missing"))
        self.assertIsNone(self.api.runUpdateSQLwithKey(key=None))
        self.con.cursor.return_value.fetchall.return_value = ({"id": "7"},)
        self.assertEqual(self.api.selectData(key="Q", parameter=("7",)), ({"id": "7"},))
        self.assertEqual(self.api.selectData(key="Q2"), ({"id": "7"},))
        self.assertEqual(self.api.runUpdateSQLwithKey(key="U"), "OK")
        executed = self._executed(self.con)
        self.assertIn("select * from t where id = '7'", executed)
        self.assertIn("select 1", executed)
        self.assertIn("delete from t", executed)


if __name__ == "__main__":
    unittest.main()

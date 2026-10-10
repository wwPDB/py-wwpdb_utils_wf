##
# File: dbAPITests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the dbAPI SQL wrapper using a mocked WfDbApi connection"""

import contextlib
import io
import sys
import unittest
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.dbapi import dbAPI as dbAPIModule
from wwpdb.utils.wf.dbapi.dbAPI import dbAPI

MODULE = "wwpdb.utils.wf.dbapi.dbAPI"
LOGGER = "wwpdb.utils.wf.dbapi.dbAPI"


class dbAPIConstructionTests(unittest.TestCase):
    def testDefaultConnectionUsesWfDbApi(self) -> None:
        with patch(MODULE + ".WfDbApi") as mApi:
            api = dbAPI("D_1")
        mApi.assert_called_once_with(verbose=False)
        self.assertIs(api.con, mApi.return_value)
        self.assertEqual(api.depID, "D_1")
        self.assertTrue(api.verbose)

    def testSuppliedConnectionAndClose(self) -> None:
        con = MagicMock()
        with patch(MODULE + ".WfDbApi") as mApi:
            api = dbAPI("D_1", connection=con, verbose=False)
            api.close()
        mApi.assert_not_called()
        con.close.assert_called_once_with()


class dbAPISelectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.con = MagicMock()
        self.con.exist.return_value = True
        self.api = dbAPI("D_1", connection=self.con, verbose=False)

    def testMissingTableOrSelect(self) -> None:
        with self.assertLogs(LOGGER, level="INFO") as cm:
            self.assertEqual(self.api.runSelect(select=["a"]), [])
            self.assertEqual(self.api.runSelect(table="t"), [])
        self.assertIn("Undefined table", cm.output[0])
        self.assertIn("Undefined select", cm.output[1])
        self.con.exist.assert_not_called()

    def testFullSqlNotRun(self) -> None:
        sql = self.api.runSelect(
            table="deposition,wf_instance",
            select=["a", "b"],
            where={"x": "'1'", "y": "z"},
            join="deposition.dep_set_id=wf_instance.dep_set_id",
            order=["a", "b"],
            reverse=True,
            ordinal=5,
            limit=10,
            run=False,
        )
        self.assertEqual(
            sql,
            "select a,b from deposition,wf_instance  where x = '1' and y = z and deposition.dep_set_id=wf_instance.dep_set_id and ordinal >= 5 order by a,b desc  limit 10",
        )
        self.con.exist.assert_called_once_with({"DEP_SET_ID": "D_1"})
        self.con.runSelectSQL.assert_not_called()

    def testRunReturnsRows(self) -> None:
        self.con.runSelectSQL.return_value = [["D_1"]]
        self.assertEqual(self.api.runSelect(table="t", select=["dep_set_id"]), [["D_1"]])
        self.con.runSelectSQL.assert_called_once_with("select dep_set_id from t ")

    def testVerboseLogsSql(self) -> None:
        self.api.verbose = True
        with self.assertLogs(LOGGER, level="INFO") as cm:
            self.api.runSelect(table="t", select=["a"], run=False)
        self.assertIn("select a from t", cm.output[0])

    def testDepositionMissing(self) -> None:
        self.con.exist.return_value = False
        self.assertEqual(self.api.runSelect(table="t", select=["a"]), [])
        self.con.runSelectSQL.assert_not_called()

    def testExceptionReturnsEmpty(self) -> None:
        self.con.exist.side_effect = RuntimeError("db gone")
        with self.assertLogs(LOGGER, level="ERROR"):
            self.assertEqual(self.api.runSelect(table="t", select=["a"]), [])

    def testRunSelectNQQuotesWhere(self) -> None:
        where = {"dep_set_id": "D_1"}
        sql = self.api.runSelectNQ(table="t", select=["a"], where=where, run=False)
        self.assertEqual(sql, "select a from t  where dep_set_id = 'D_1'")
        self.assertEqual(where, {"dep_set_id": "'D_1'"})


class dbAPIUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.con = MagicMock()
        self.api = dbAPI("D_1", connection=self.con, verbose=False)

    def testRunUpdateOnOrdinal(self) -> None:
        with self.assertLogs(LOGGER, level="INFO"):
            self.assertFalse(self.api.runUpdateOnOrdinal(ordinal=1, data={"a": "1"}))
            self.assertFalse(self.api.runUpdateOnOrdinal(table="t", data={"a": "1"}))
        self.assertEqual(self.api.runUpdateOnOrdinal(table="t", ordinal=17, data={"a": "'x'", "b": "2"}, run=False), "update t set a = 'x',b = 2 where ordinal = 17")
        self.con.runUpdateSQL.return_value = 1
        self.assertEqual(self.api.runUpdateOnOrdinal(table="t", ordinal=17, data={"a": "1"}), 1)
        self.con.runUpdateSQL.assert_called_once_with("update t set a = 1 where ordinal = 17")

    def testRunUpdateOnOrdinalFailures(self) -> None:
        self.con.runUpdateSQL.return_value = 0
        with self.assertLogs(LOGGER, level="INFO") as cm:
            self.assertEqual(self.api.runUpdateOnOrdinal(table="t", ordinal=17, data={"a": "1"}), 0)
            # data=None raises inside and is reported as False
            self.assertFalse(self.api.runUpdateOnOrdinal(table="t", ordinal=17, data=None))
        self.assertIn("False to update/insert", cm.output[0])
        self.assertIn("Exception", cm.output[1])

    def testRunInsertWithDepId(self) -> None:
        sql = self.api.runInsert(table="t", depID="D_2", data={"a": "'x'", "b": "3"}, run=False)
        self.assertEqual(sql, "insert into t (dep_set_id,a,b) values ('D_2','x',3)")

    def testRunInsertWithWhere(self) -> None:
        self.con.runInsertSQL.return_value = 1
        self.assertEqual(self.api.runInsert(table="t", where={"k": "'1'"}, data={"a": "2"}), 1)
        self.con.runInsertSQL.assert_called_once_with("insert into t (k,a) values ('1',2)")
        self.assertEqual(self.api.runInsert(table="t", where={"k": "'1'"}, run=False), "insert into t (k) values ('1')")

    def testRunInsertWithoutKeyFails(self) -> None:
        with self.assertLogs(LOGGER, level="ERROR"):
            self.assertFalse(self.api.runInsert(table="t", data={"a": "1"}))
        self.con.runInsertSQL.assert_not_called()

    def testRunInsertNQ(self) -> None:
        where = {"k": "1"}
        data = {"a": "2"}
        self.assertEqual(self.api.runInsertNQ(table="t", where=where, data=data, run=False), "insert into t (k,a) values ('1','2')")

    def testRunUpdate(self) -> None:
        self.assertEqual(self.api.runUpdate(table="t", depID="D_2", data={"a": "'x'"}, run=False), "update t set a = 'x' where dep_set_id = 'D_2'")
        self.assertEqual(self.api.runUpdate(table="t", where={"k": "1", "j": "2"}, data={"a": "3"}, run=False), "update t set a = 3 where k = 1 and j = 2")
        self.con.runUpdateSQL.return_value = 1
        self.assertEqual(self.api.runUpdate(table="t", depID="D_2", data={"a": "1"}), 1)
        self.con.runUpdateSQL.assert_called_once_with("update t set a = 1 where dep_set_id = 'D_2'")

    def testRunUpdateException(self) -> None:
        with self.assertLogs(LOGGER, level="ERROR"):
            self.assertFalse(self.api.runUpdate(table="t", depID="D_2", data=None))

    def testRunInsertUpdateByDepId(self) -> None:
        self.con.exist.return_value = True
        self.assertEqual(self.api.runInsertUpdate(table="t", depID="D_2", data={"a": "1"}, run=False), "update t set a = 1 where dep_set_id = 'D_2'")
        self.con.exist.assert_called_once_with({"DEP_SET_ID": "D_2"})
        self.con.exist.return_value = False
        self.assertEqual(self.api.runInsertUpdate(table="t", depID="D_2", data={"a": "1"}, run=False), "insert into t (dep_set_id,a) values ('D_2',1)")

    def testRunInsertUpdateByWhere(self) -> None:
        self.con.runSelectSQL.return_value = [[12]]
        self.assertEqual(self.api.runInsertUpdate(table="t", where={"k": "'1'"}, data={"a": "2"}, run=False), "update t set a = 2 where k = '1'")
        self.con.runSelectSQL.assert_called_once_with("select ordinal from t where k = '1'")
        self.con.runSelectSQL.return_value = []
        self.con.runInsertSQL.return_value = 1
        self.assertEqual(self.api.runInsertUpdate(table="t", where={"k": "'1'"}, data={"a": "2"}), 1)
        self.con.runInsertSQL.assert_called_once_with("insert into t (k,a) values ('1',2)")

    def testRunInsertUpdateFailures(self) -> None:
        with self.assertLogs(LOGGER, level="INFO") as cm:
            self.assertFalse(self.api.runInsertUpdate(depID="D_2", data={"a": "1"}))
            # no key at all: insert cannot build SQL and reports False
            self.assertFalse(self.api.runInsertUpdate(table="t", data={"a": "1"}))
            self.con.exist.return_value = True
            self.con.runUpdateSQL.return_value = 0
            self.assertEqual(self.api.runInsertUpdate(table="t", depID="D_2", data={"a": "1"}), 0)
        joined = "\n".join(cm.output)
        self.assertIn("Undefined table", joined)
        self.assertIn("Undefined key", joined)
        self.assertIn("False to update/insert data", joined)

    def testRunInsertUpdateNQ(self) -> None:
        self.con.runSelectSQL.return_value = []
        sql = self.api.runInsertUpdateNQ(table="t", where={"k": "1"}, data={"a": "2"}, run=False)
        self.con.runSelectSQL.assert_called_once_with("select ordinal from t where k = '1'")
        self.assertEqual(sql, "insert into t (k,a) values ('1','2')")


class dbAPIMainTests(unittest.TestCase):
    def testMainRunsQueries(self) -> None:
        out = io.StringIO()
        with patch(MODULE + ".WfDbApi") as mApi, contextlib.redirect_stdout(out):
            mApi.return_value.exist.return_value = True
            mApi.return_value.runSelectSQL.return_value = [["D_1100201819"]]
            dbAPIModule.main([])
        text = out.getvalue()
        self.assertTrue(text.startswith("starting DBAPI test"))
        self.assertIn("[['D_1100201819']]", text)
        self.assertTrue(text.rstrip().endswith("finished"))
        self.assertGreaterEqual(mApi.return_value.runSelectSQL.call_count, 7)


if __name__ == "__main__":
    unittest.main()

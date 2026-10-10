##
# File: WfDbApiMockTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for WfDbApi with ConfigInfo, DbConnection and DbCommand mocked"""

import io
import sys
import unittest
from decimal import Decimal
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, call, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

import MySQLdb

from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi

MODULE = "wwpdb.utils.wf.dbapi.WfDbApi"
NOW = Decimal("845000000.5")

SITE_CONFIG: Dict[str, Optional[str]] = {
    "SITE_DB_SERVER": "mysql",
    "SITE_DB_HOST_NAME": "dbhost",
    "SITE_DB_DATABASE_NAME": "status",
    "SITE_DB_USER_NAME": "wfuser",
    "SITE_DB_PASSWORD": "secret",
    "SITE_DB_SOCKET": "/var/mysql.sock",
    "SITE_DB_PORT_NUMBER": "3306",
}


def _table(tableDef: Any) -> str:
    """Table name of a tableDef passed to the mocked DbCommand"""
    return str(tableDef["TABLE_NAME"])


class WfDbApiTestBase(unittest.TestCase):
    def setUp(self) -> None:
        cI = MagicMock()
        cI.return_value.get.side_effect = SITE_CONFIG.get
        patchers = {
            "ConfigInfo": patch(MODULE + ".ConfigInfo", new=cI),
            "DbConnection": patch(MODULE + ".DbConnection"),
            "DbCommand": patch(MODULE + ".DbCommand"),
            "time": patch(MODULE + ".time"),
            "getTimeNow": patch(MODULE + ".getTimeNow", return_value=NOW),
        }
        self.mocks: Dict[str, MagicMock] = {}
        for name, p in patchers.items():
            self.mocks[name] = p.start()
            self.addCleanup(p.stop)
        self.mCI = cI
        self.myDb = self.mocks["DbConnection"].return_value
        self.con = MagicMock(name="con")
        self.con.__str__.return_value = "<_mysql.connection open to 'dbhost' at 0x1>"  # type: ignore[attr-defined]
        self.myDb.connect.return_value = self.con
        self.cmd = self.mocks["DbCommand"].return_value
        self.cmd.dbState = 0
        self.log = io.StringIO()
        self.api = WfDbApi(log=self.log, verbose=True, siteId="WWPDB_DEPLOY_TEST")

    def _lostConnection(self) -> None:
        """Mark the mocked DbCommand as having lost the server connection"""
        self.cmd.dbState = 2006


class WfDbApiConnectionTests(WfDbApiTestBase):
    def testConstructor(self) -> None:
        self.mCI.assert_called_once_with(siteId="WWPDB_DEPLOY_TEST")
        self.mocks["DbConnection"].assert_called_once_with(
            dbServer="mysql", dbHost="dbhost", dbName="status", dbUser="wfuser", dbPw="secret", dbPort=3306, dbSocket="/var/mysql.sock"
        )
        self.mocks["DbCommand"].assert_called_once_with(self.con, self.log, True)

    def testIsConnectedAndClose(self) -> None:
        self.assertTrue(self.api.isConnected())
        self.api.close()
        self.myDb.close.assert_called_once_with(self.con)

    def testClosedConnection(self) -> None:
        self.con.__str__.return_value = "<_mysql.connection closed at 0x1>"  # type: ignore[attr-defined]
        self.assertFalse(self.api.isConnected())
        self.api.close()
        self.myDb.close.assert_not_called()
        self.api.testConnection()
        self.assertEqual(self.myDb.connect.call_count, 2)
        self.assertIn("Re-connecting to the database", self.log.getvalue())

    def testTestConnectionOpenDoesNothing(self) -> None:
        self.api.testConnection()
        self.assertEqual(self.myDb.connect.call_count, 1)

    def testReConnect(self) -> None:
        self.myDb.close.side_effect = MySQLdb.OperationalError(2006, "gone")
        self.assertTrue(self.api.reConnect())
        self.assertIn("cannot close", self.log.getvalue())
        self.assertEqual(self.mocks["DbCommand"].call_count, 2)

    def testReConnectFails(self) -> None:
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertFalse(self.api.reConnect())
        self.assertEqual(self.myDb.connect.call_count, 5)
        self.assertEqual(self.mocks["time"].sleep.call_args_list, [call(2), call(4), call(6), call(8)])


class WfDbApiRunSqlTests(WfDbApiTestBase):
    def testRunSqlSuccess(self) -> None:
        self.cmd.runInsertSQL.return_value = 1
        self.cmd.runUpdateSQL.return_value = 2
        self.cmd.runSelectSQL.return_value = [["a"]]
        self.assertEqual(self.api.runInsertSQL("insert x", ("a",)), 1)
        self.assertEqual(self.api.runUpdateSQL("update x"), 2)
        self.assertEqual(self.api.runSelectSQL("select x"), [["a"]])
        self.cmd.runInsertSQL.assert_called_once_with("insert x", ("a",))
        self.cmd.runUpdateSQL.assert_called_once_with("update x", None)
        self.cmd.runSelectSQL.assert_called_once_with("select x")

    def testRunSqlRetriesAfterLostConnection(self) -> None:
        self._lostConnection()
        self.cmd.runInsertSQL.side_effect = [None, 1]
        self.cmd.runUpdateSQL.side_effect = [None, 2]
        self.cmd.runSelectSQL.side_effect = [None, [["a"]]]
        self.assertEqual(self.api.runInsertSQL("insert x"), 1)
        self.assertEqual(self.api.runUpdateSQL("update x"), 2)
        self.assertEqual(self.api.runSelectSQL("select x"), [["a"]])
        self.assertEqual(self.myDb.close.call_count, 3)
        self.assertEqual(self.mocks["time"].sleep.call_args_list, [call(2)] * 3)

    def testRunSqlUnhandledError(self) -> None:
        self.cmd.runInsertSQL.return_value = None
        self.cmd.runUpdateSQL.return_value = None
        self.cmd.runSelectSQL.return_value = None
        self.assertIsNone(self.api.runInsertSQL("insert x"))
        self.assertIsNone(self.api.runUpdateSQL("update x"))
        self.assertIsNone(self.api.runSelectSQL("select x"))
        self.myDb.close.assert_not_called()

    def testRunSqlGivesUpWhenReconnectFails(self) -> None:
        self._lostConnection()
        self.cmd.runSelectSQL.return_value = None
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.runSelectSQL("select x"))
        self.cmd.runSelectSQL.assert_called_once_with("select x")

    def testRunSqlAllRetriesExhausted(self) -> None:
        self._lostConnection()
        self.cmd.runUpdateSQL.return_value = None
        self.assertIsNone(self.api.runUpdateSQL("update x"))
        self.assertEqual(self.cmd.runUpdateSQL.call_count, 4)

    def testProcessStatus(self) -> None:
        self.cmd.runSelectSQL.return_value = [["open"], ["closed(0)"]]
        self.assertEqual(self.api.processStatus("D_1", "W_1", "Annotate"), "open")
        self.cmd.runSelectSQL.assert_called_once_with("select inst_status from dep_last_instance where dep_set_id = 'D_1' AND inst_id = 'W_1' AND class_id = 'Annotate'")
        self.myDb.close.assert_called_once_with(self.con)

    def testProcessStatusNoRowsOrError(self) -> None:
        self.cmd.runSelectSQL.return_value = []
        self.assertIsNone(self.api.processStatus("D_1", "W_1", "Annotate"))
        self.cmd.runSelectSQL.return_value = None
        self.assertIsNone(self.api.processStatus("D_1", "W_1", "Annotate"))
        self.assertIn("Exception in processOwner", self.log.getvalue())


class WfDbApiObjectTests(WfDbApiTestBase):
    def testCheckId(self) -> None:
        self.assertIsNone(self.api.checkId(""))
        self.assertIsNone(self.api.checkId(None))
        self.assertEqual(self.api.checkId("D_1"), "D_1")

    def testGetTableDef(self) -> None:
        cases = [
            ({"DEP_SET_ID": 1, "WF_CLASS_ID": 1, "WF_INST_ID": 1, "WF_TASK_ID": 1}, "wf_task"),
            ({"DEP_SET_ID": 1, "WF_CLASS_ID": 1, "WF_INST_ID": 1}, "wf_instance"),
            ({"WF_CLASS_ID": 1}, "wf_class_dict"),
            ({"DEP_SET_ID": 1, "PDB_ID": "1abc"}, "deposition"),
        ]
        for dataObj, table in cases:
            with self.subTest(table=table):
                self.assertEqual(_table(self.api.getTableDef(dataObj)), table)
        self.assertEqual(self.api.getTableDef({"DEP_SET_ID": 1, "WF_CLASS_ID": 1}), {})

    def testGetObjectTables(self) -> None:
        self.cmd.selectRows.return_value = {"x": 1}
        self.assertEqual(self.api.getObject("D_1", "Annotate", "W_1", "T_1"), {"x": 1})
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(_table(args[0]), "wf_task")
        self.assertEqual(args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "WF_INST_ID": "W_1", "WF_TASK_ID": "T_1"})
        self.assertEqual(args[2], ["ORDINAL"])

        self.api.getObject("D_1", "Annotate", "W_1", "")
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(_table(args[0]), "wf_instance")
        self.assertEqual(args[2], ["ORDINAL"])

        self.api.getObject(None, "Annotate")
        args = self.cmd.selectRows.call_args.args
        self.assertEqual((_table(args[0]), args[1], len(args)), ("wf_class_dict", {"WF_CLASS_ID": "Annotate"}, 2))

        self.api.getObject("D_1")
        args = self.cmd.selectRows.call_args.args
        self.assertEqual((_table(args[0]), args[1], len(args)), ("deposition", {"DEP_SET_ID": "D_1"}, 2))

    def testGetObjectBadParameters(self) -> None:
        self.assertEqual(self.api.getObject("D_1", None, "W_1"), {})
        self.assertEqual(self.api.getObject(), {})
        self.cmd.selectRows.assert_not_called()
        self.assertIn("Wrong parameters", self.log.getvalue())

    def testGetObjectRetryAndErrors(self) -> None:
        self._lostConnection()
        self.cmd.selectRows.side_effect = [None, {"x": 1}]
        self.assertEqual(self.api.getObject("D_1"), {"x": 1})
        self.myDb.close.assert_called_once_with(self.con)
        self.cmd.selectRows.side_effect = None
        self.cmd.selectRows.return_value = None
        self.cmd.dbState = 0
        self.assertIsNone(self.api.getObject("D_1"))

    def testExist(self) -> None:
        self.assertFalse(self.api.exist({}))
        self.assertFalse(self.api.exist({"PDB_ID": "1abc"}))
        self.cmd.selectRows.assert_not_called()
        self.cmd.selectRows.return_value = {"DEP_SET_ID": "D_1"}
        self.assertTrue(self.api.exist({"DEP_SET_ID": "D_1"}))
        self.cmd.selectRows.return_value = {}
        self.assertFalse(self.api.exist({"DEP_SET_ID": "D_1", "WF_CLASS_ID": "A", "WF_INST_ID": "W", "WF_TASK_ID": "T"}))
        self.assertEqual(self.cmd.selectRows.call_args.args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "A", "WF_INST_ID": "W", "WF_TASK_ID": "T"})

    def testSaveObject(self) -> None:
        self.cmd.update.return_value = "ok"
        dataObj = {"DEP_SET_ID": "D_1", "PDB_ID": "1abc"}
        self.assertEqual(self.api.saveObject(dataObj, "update", {"DEP_SET_ID": "D_1"}), "ok")
        args = self.cmd.update.call_args.args
        self.assertEqual((args[0], _table(args[1]), args[2], args[3]), ("update", "deposition", dataObj, {"DEP_SET_ID": "D_1"}))

    def testSaveObjectNotRecognised(self) -> None:
        self.assertEqual(self.api.saveObject({"PDB_ID": "1abc"}), "bad-code")
        self.cmd.update.assert_not_called()

    def testSaveObjectEmptyIdExits(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.saveObject({"DEP_SET_ID": ""})
        self.assertIn("DEP_SET_ID can not be None", self.log.getvalue())

    def testSaveObjectErrors(self) -> None:
        self.cmd.update.return_value = None
        self.assertIsNone(self.api.saveObject({"DEP_SET_ID": "D_1"}))
        self._lostConnection()
        self.assertIsNone(self.api.saveObject({"DEP_SET_ID": "D_1"}))
        self.assertEqual(self.cmd.update.call_count, 5)

    def testGetStatus(self) -> None:
        task = {"DEP_SET_ID": 1, "WF_CLASS_ID": 1, "WF_INST_ID": 1, "WF_TASK_ID": 1, "TASK_STATUS": "finished"}
        inst = {"DEP_SET_ID": 1, "WF_CLASS_ID": 1, "WF_INST_ID": 1, "INST_STATUS": "open"}
        dep = {"DEP_SET_ID": 1, "STATUS_CODE": "PROC"}
        self.assertEqual(self.api.getStatus(task), "finished")
        self.assertEqual(self.api.getStatus(inst), "open")
        self.assertEqual(self.api.getStatus(dep), "PROC")
        self.assertEqual(self.api.getStatus([dep, inst]), "open")
        self.assertEqual(self.api.getStatus({"WF_CLASS_ID": 1}), "")
        self.assertEqual(self.api.getStatus("D_1"), "")

    def testAssignStatus(self) -> None:
        inst = self.api.getTableDef({"DEP_SET_ID": 1, "WF_CLASS_ID": 1, "WF_INST_ID": 1})
        self.assertEqual(self.api.assignStatus(inst, "open"), {"INST_STATUS": "open", "STATUS_TIMESTAMP": NOW})
        dep = self.api.getTableDef({"DEP_SET_ID": 1})
        self.assertEqual(self.api.assignStatus(dep, "PROC"), {"STATUS_CODE": "PROC"})

    def testUpdateStatus(self) -> None:
        self.cmd.update.return_value = "ok"
        dataObj = {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "WF_INST_ID": "W_1", "OWNER": "x"}
        self.assertEqual(self.api.updateStatus(dataObj, "closed(0)"), "ok")
        args = self.cmd.update.call_args.args
        self.assertEqual(args[0], "update")
        self.assertEqual(_table(args[1]), "wf_instance")
        self.assertEqual(args[2], {"INST_STATUS": "closed(0)", "STATUS_TIMESTAMP": NOW})
        self.assertEqual(args[3], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "WF_INST_ID": "W_1"})

    def testUpdateStatusFailures(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.updateStatus({"DEP_SET_ID": "D_1"}, "")
        self.assertEqual(self.api.updateStatus({"PDB_ID": "1"}, "x"), "code-bad")
        self.cmd.update.return_value = None
        self.assertIsNone(self.api.updateStatus({"DEP_SET_ID": "D_1"}, "x"))
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.updateStatus({"DEP_SET_ID": "D_1"}, "x"))

    def testMakeDataDict(self) -> None:
        dep = self.api.getTableDef({"DEP_SET_ID": 1})
        self.assertEqual(self.api.makeDataDict(dep, {"DEP_SET_ID": "D_1", "BOGUS": 1}), {"DEP_SET_ID": "D_1"})
        self.assertEqual(self.api.makeDataDict(dep, ["DEP_SET_ID"]), {})
        self.assertIn("not a dictionary", self.log.getvalue())


class WfDbApiReferenceTests(WfDbApiTestBase):
    def testGetReference(self) -> None:
        self.cmd.selectRows.return_value = [{"HASH_ID": "a"}, {"HASH_ID": "b"}]
        self.assertEqual(self.api.getReference("D_1", "", "W_1"), [{"HASH_ID": "a"}, {"HASH_ID": "b"}])
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(_table(args[0]), "wf_reference")
        self.assertEqual(args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "None", "WF_INST_ID": "W_1", "WF_TASK_ID": "None"})

    def testGetReferenceErrors(self) -> None:
        self.cmd.selectRows.return_value = None
        self.assertIsNone(self.api.getReference(None, "A", None, "T"))
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.getReference("D_1"))

    def testAddReferenceInsert(self) -> None:
        self.cmd.update.return_value = "done"
        self.assertEqual(self.api.addReference("INSERT", "D_1", "Annotate", None, "", "depSelect", "3"), "ok")
        args = self.cmd.update.call_args.args
        self.assertEqual(args[0], "insert")
        self.assertEqual(_table(args[1]), "wf_reference")
        self.assertEqual(args[2], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "HASH_ID": "depSelect", "VALUE": "3"})
        self.assertEqual(args[3], {})

    def testAddReferenceUpdate(self) -> None:
        self.cmd.update.return_value = "done"
        self.assertEqual(self.api.addReference("update", "D_1", None, "W_1", None, "instSelect", "4"), "ok")
        args = self.cmd.update.call_args.args
        self.assertEqual(args[0], "update")
        self.assertEqual(args[2], {"VALUE": "4"})
        self.assertEqual(args[3], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "None", "WF_INST_ID": "W_1", "WF_TASK_ID": "None", "HASH_ID": "instSelect"})

    def testAddReferenceErrors(self) -> None:
        self.cmd.update.return_value = None
        self.assertIsNone(self.api.addReference("insert", "D_1"))
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.addReference("insert", "D_1"))

    def testReferenceExist(self) -> None:
        self.cmd.selectRows.return_value = {"VALUE": "3"}
        self.assertTrue(self.api.referenceExist("D_1", hashId="h", hashVal="3"))
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "None", "WF_INST_ID": "None", "WF_TASK_ID": "None", "HASH_ID": "h"})
        self.assertEqual(args[3], {"VALUE": "3"})
        self.cmd.selectRows.return_value = {}
        self.assertFalse(self.api.referenceExist("D_1", "A", "W", "T"))
        self.cmd.selectRows.return_value = None
        self.assertIsNone(self.api.referenceExist("D_1"))

    def testAddReferenceOverwrite(self) -> None:
        self.cmd.update.return_value = "done"
        self.cmd.selectRows.return_value = {"VALUE": "1"}
        self.api.addReferenceOverwrite("D_1", hashId="h", hashVal="2")
        self.assertEqual(self.cmd.update.call_args.args[0], "update")
        self.cmd.selectRows.return_value = {}
        self.api.addReferenceOverwrite("D_1", hashId="h", hashVal="2")
        self.assertEqual(self.cmd.update.call_args.args[0], "insert")
        self.assertEqual(self.cmd.update.call_args.args[2], {"DEP_SET_ID": "D_1", "HASH_ID": "h", "VALUE": "2"})


class WfDbApiLastObjectTests(WfDbApiTestBase):
    def testInstanceWithState(self) -> None:
        self.cmd.selectRows.return_value = [{"WF_INST_ID": "W_000003"}, {"WF_INST_ID": "W_000002"}]
        self.assertEqual(self.api.getLastObjectOfState("open", "D_1", "Annotate"), {"WF_INST_ID": "W_000003"})
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(_table(args[0]), "wf_instance")
        self.assertEqual(args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "INST_STATUS": "open"})
        self.assertEqual(args[2], ["ordinal desc"])

    def testTaskWithState(self) -> None:
        self.cmd.selectRows.return_value = {"WF_TASK_ID": "T_1"}
        self.assertEqual(self.api.getLastObjectOfState("finished", "D_1", "Annotate", "W_1"), {"WF_TASK_ID": "T_1"})
        args = self.cmd.selectRows.call_args.args
        self.assertEqual(_table(args[0]), "wf_task")
        self.assertEqual(args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "WF_INST_ID": "W_1", "TASK_STATUS": "finished"})

    def testMissingIdsExit(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.getLastObjectOfState(None, "", "Annotate")
        with self.assertRaises(SystemExit):
            self.api.getLastObjectOfState(None, "D_1", None)

    def testErrors(self) -> None:
        self.cmd.selectRows.return_value = None
        self.assertIsNone(self.api.getLastObjectOfState(None, "D_1", "Annotate"))
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.getLastObjectOfState(None, "D_1", "Annotate"))

    def testGetNextWfInstId(self) -> None:
        self.cmd.selectRows.return_value = {}
        self.assertEqual(self.api.getNextWfInstId("D_1", "Annotate"), 1)
        self.cmd.selectRows.return_value = {"WF_INST_ID": "W_000007"}
        self.assertEqual(self.api.getNextWfInstId("D_1", "Annotate"), 8)
        self.assertEqual(self.cmd.selectRows.call_args.args[1], {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate"})


class WfDbApiQueryTests(WfDbApiTestBase):
    def testGetAll(self) -> None:
        self.cmd.selectCrossTables.return_value = [{"deposition.dep_set_id": "D_1"}]
        self.assertEqual(self.api.getAll("D_1", "Annotate", "W_1"), [{"deposition.dep_set_id": "D_1"}])
        selectList, joinStr, orderBy, constraintList, constraintDef = self.cmd.selectCrossTables.call_args.args
        self.assertEqual(selectList[0], "deposition.dep_set_id")
        self.assertTrue(joinStr.startswith(" FROM wf_instance left join wf_class_dict"))
        self.assertIn("order by deposition.dep_set_id", orderBy)
        self.assertEqual(constraintList["DEP_SET_ID"], "deposition.dep_set_id")
        self.assertEqual(constraintDef, {"DEP_SET_ID": "D_1", "WF_CLASS_ID": "Annotate", "WF_INST_ID": "W_1"})

    def testGetAllInvalidIdsExit(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.getAll(None, "Annotate")
        with self.assertRaises(SystemExit):
            self.api.getAll("D_1", None, "W_1")

    def testGetAllErrors(self) -> None:
        self.cmd.selectCrossTables.return_value = None
        self.assertIsNone(self.api.getAll())
        self.assertEqual(self.cmd.selectCrossTables.call_args.args[4], {})
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.getAll("D_1"))

    def testDoQueryLevel2(self) -> None:
        self.cmd.selectCrossTables.return_value = [{"a": 1}]
        self.assertEqual(self.api.doQuery(2, {"DEP_SET_ID": "D_1"}), [{"a": 1}])
        self.assertIn("order by deposition.dep_set_id", self.cmd.selectCrossTables.call_args.args[2])
        self.cmd.makeOrderStr.return_value = " ORDER BY x"
        self.api.doQuery(2, {"OWNER": "me"}, ["PDB_ID", "OWNER"])
        self.cmd.makeOrderStr.assert_called_once_with(["PDB_ID", "OWNER"])
        self.assertEqual(self.cmd.selectCrossTables.call_args.args[2], " ORDER BY x")
        self.assertEqual(self.cmd.selectCrossTables.call_args.args[4], {"OWNER": "me"})

    def testDoQueryLevel2Invalid(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.doQuery(2, {"BOGUS": 1})
        with self.assertRaises(SystemExit):
            self.api.doQuery(2, {}, ["BOGUS"])
        with self.assertRaises(SystemExit):
            self.api.doQuery(2, {}, otherOpt="AUTHOR_CORRECTIONS")
        self.cmd.selectCrossTables.assert_not_called()

    def testDoQueryLevel2Errors(self) -> None:
        self.cmd.selectCrossTables.return_value = None
        self.assertIsNone(self.api.doQuery(2, {}))
        self._lostConnection()
        self.assertIsNone(self.api.doQuery(2, {}))
        self.assertEqual(self.cmd.selectCrossTables.call_count, 5)

    def testDoQueryLevel1WithOtherOption(self) -> None:
        def _selectRows(tableDef: Any, constDict: Any, _orderList: Any = None, selectList: Any = None) -> Any:
            table = _table(tableDef)
            if table == "deposition":
                return {"DEP_SET_ID": "D_1", "PDB_ID": "1abc"}
            results: Dict[str, Any] = {
                "database_ref": [{"DATABASE_CODE": "PDB"}, {"DATABASE_CODE": "EMDB"}],
                "database_PDB_obs_spr": {"REPLACE_PDB_ID": "9xyz"},
                "database_related": [{"DB_ID": "D_2"}, {"DB_ID": "D_3"}],
                "dep_with_problems": {"PROBLEM_TYPE": "ligand", "PROBLEM_DETAILS": "bad geometry"},
            }
            self.assertEqual(constDict["DEP_SET_ID"], "D_1")
            result = results[table]
            if isinstance(result, dict):
                # Like the real query, only the selected column is returned
                return {k: v for k, v in result.items() if k in selectList}
            return result

        self.cmd.selectRows.side_effect = _selectRows
        rows = self.api.doQuery(1, {"STATUS_CODE": "PROC"}, otherOpt="DEP_WITH_PROBLEMS")
        self.assertEqual(
            rows,
            [
                {
                    "DEP_SET_ID": "D_1",
                    "PDB_ID": "1abc",
                    "ASSESSION_CODE": "PDB, EMDB",
                    "RELATIONSHIP": "SPR/OBS, SPLIT",
                    "ASSOCIATED_IDS": "9xyz, D_2, D_3",
                    "PROBLEM_TYPE": "ligand",
                    "PROBLEM_DETAILS": "bad geometry",
                }
            ],
        )
        mainCall = self.cmd.selectRows.call_args_list[0].args
        self.assertEqual(mainCall[1], {"STATUS_CODE": "PROC"})
        self.assertEqual(mainCall[2], ["author_release_status_code", "initial_deposition_date"])
        self.assertEqual(mainCall[3][0], "DEP_SET_ID")

    def testDoQueryLevel1Invalid(self) -> None:
        with self.assertRaises(SystemExit):
            self.api.doQuery(1, {"BOGUS": 1}, otherOpt="RELEASE_REQUEST")

    def testDoQueryLevel1Errors(self) -> None:
        self.cmd.selectRows.return_value = None
        self.assertIsNone(self.api.doQuery(1, {}, otherOpt="RELEASE_REQUEST"))

    @unittest.expectedFailure
    def testDoQueryLevel1WithoutOtherOption(self) -> None:
        # Library bug: WfDbApi.doQuery tests "otherOpt is None" instead of "is not None", so plain level-1 queries always sys.exit
        self.cmd.selectRows.return_value = []
        self.assertEqual(self.api.doQuery(1, {"STATUS_CODE": "PROC"}), [])

    def testGetValueString(self) -> None:
        refDef = {"TABLE_NAME": "database_ref", "ATTRIBUTES": {}}
        self.cmd.selectRows.return_value = {"DATABASE_CODE": "PDB"}
        self.assertEqual(self.api.getValueString(refDef, {"DEP_SET_ID": "D_1"}, "DATABASE_CODE"), "PDB")
        self.cmd.selectRows.assert_called_once_with(refDef, {"DEP_SET_ID": "D_1"}, [], ["DATABASE_CODE"])
        self.cmd.selectRows.return_value = [{"DB_ID": "a"}, {"DB_ID": "b"}, {"OTHER": "c"}]
        self.assertEqual(self.api.getValueString(refDef, {}, "NOT_CHECKED"), "a, b")
        self.assertEqual(self.cmd.selectRows.call_args.args[3], [])

    def testGetValueStringErrors(self) -> None:
        self.cmd.selectRows.return_value = None
        self.assertIsNone(self.api.getValueString({}, {}, "DB_ID"))
        self._lostConnection()
        self.myDb.connect.side_effect = MySQLdb.OperationalError(2003, "no server")
        self.assertIsNone(self.api.getValueString({}, {}, "DB_ID"))


if __name__ == "__main__":
    unittest.main()

##
# File: DbCommandTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for DbCommand SQL builders and executors using a mocked DB connection"""

import io
import sys
import unittest
from typing import Any, List, Optional, Tuple
from unittest.mock import MagicMock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

import MySQLdb

from wwpdb.utils.wf.dbapi.DbCommand import DbCommand
from wwpdb.utils.wf.schema.SchemaMapTypes import SchemaTableDef

ATTRIBS = {"DEP_SET_ID": "dep_set_id", "PDB_ID": "pdb_id", "STATUS_CODE": "status_code"}
TABLEDEF: SchemaTableDef = {"TABLE_NAME": "deposition", "ATTRIBUTES": ATTRIBS}


def _failOn(match: str, code: int = 1146) -> Any:
    """Return a cursor.execute side effect raising a MySQLdb error when the query contains match"""

    def _execute(query: str, *_args: Any) -> int:
        if match in query:
            raise MySQLdb.ProgrammingError(code, "Table missing")
        return 1

    return _execute


class DbCommandBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.log = io.StringIO()
        self.cmd = DbCommand(MagicMock(), log=self.log, verbose=True)

    def testMakeSqlSet(self) -> None:
        s = self.cmd.makeSqlSet(ATTRIBS, {"DEP_SET_ID": "D_1", "PDB_ID": None, "STATUS_CODE": "None", "BOGUS": "x"})
        self.assertEqual(s, " SET  dep_set_id = 'D_1' ,  pdb_id = NULL ,  status_code = NULL ")
        self.assertIn("BOGUS is not defined", self.log.getvalue())

    def testMakeSqlSetNonDict(self) -> None:
        self.assertEqual(self.cmd.makeSqlSet(ATTRIBS, [("a", "b")]), "")
        self.assertEqual(self.cmd.makeSqlSet(ATTRIBS, {}), "")

    def testMakeConstraintCross(self) -> None:
        cl = {"DEP_SET_ID": "deposition.dep_set_id", "OWNER": "wf_instance.owner"}
        s = self.cmd.makeConstraintCross(cl, {"DEP_SET_ID": "D_1", "OWNER": None, "X": "1"})
        self.assertEqual(s, " WHERE  deposition.dep_set_id = 'D_1'  AND  wf_instance.owner is NULL ")
        self.assertIn("X is not a key", self.log.getvalue())
        self.assertEqual(self.cmd.makeConstraintCross(cl, {}), "")

    def testMakeSqlConstraintDict(self) -> None:
        s = self.cmd.makeSqlConstraint(ATTRIBS, {"DEP_SET_ID": "D_1", "PDB_ID": "None", "EXTERNAL_TABLE": "dep_set_id in (select x)", "Z": 1})
        self.assertEqual(s, " WHERE  dep_set_id = 'D_1'  AND  pdb_id is NULL  AND   dep_set_id in (select x) ")
        self.assertIn("Z is not defined", self.log.getvalue())

    def testMakeSqlConstraintList(self) -> None:
        cdef = [
            ("GROUP", "BEGIN"),
            ("eq", "dep_set_id", "D_1", "char"),
            ("LOGOP", "or"),
            ("GT", "pdb_id", 5, "int"),
            ("GROUP", "END"),
            ("LOGOP", "AND"),
            ("LIKE", "status_code", "HP%"),
            ("BAD",),
        ]
        s = self.cmd.makeSqlConstraint(ATTRIBS, cdef)
        self.assertEqual(s, " WHERE ( dep_set_id = 'D_1'  OR  pdb_id > 5 ) AND  status_code LIKE 'HP%' ")
        self.assertIn("Constraint error: ('BAD',)", self.log.getvalue())

    def testMakeSqlConstraintEmptyListAndNone(self) -> None:
        self.assertEqual(self.cmd.makeSqlConstraint(ATTRIBS, []), "")
        self.assertEqual(self.cmd.makeSqlConstraint(ATTRIBS, None), "")
        self.assertIn("constraint type error", self.log.getvalue())

    def testMakeOrderStr(self) -> None:
        self.assertEqual(self.cmd.makeOrderStr([]), "")
        self.assertEqual(self.cmd.makeOrderStr(["a"]), " ORDER BY a")
        self.assertEqual(self.cmd.makeOrderStr(["a", "b desc"]), " ORDER BY a, b desc")


class DbCommandExecuteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.log = io.StringIO()
        self.con = MagicMock()
        self.curs = self.con.cursor.return_value
        self.cmd = DbCommand(self.con, log=self.log, verbose=True)

    def _setRows(self, rows: List[Optional[Tuple[Any, ...]]]) -> None:
        self.curs.fetchone.side_effect = [*rows, None]

    def _executed(self) -> List[Any]:
        return [c.args for c in self.curs.execute.call_args_list]

    def testRunUpdateSQL(self) -> None:
        self.curs.execute.side_effect = [0, 3, 0]
        self.assertEqual(self.cmd.runUpdateSQL("update t set a=1"), 3)
        self.assertEqual(self._executed(), [("set autocommit=0",), ("update t set a=1",), ("set autocommit=1",)])
        self.con.commit.assert_called_once_with()
        self.curs.close.assert_called_once_with()

    def testRunUpdateSQLWithArgs(self) -> None:
        self.curs.execute.side_effect = [0, 1, 0]
        self.assertEqual(self.cmd.runInsertSQL("insert into t values (%s)", ("a'b",)), 1)
        self.assertEqual(self._executed()[1], ("insert into t values (%s)", ("a'b",)))

    def testRunUpdateSQLError(self) -> None:
        self.curs.execute.side_effect = _failOn("update", 2006)
        self.assertIsNone(self.cmd.runUpdateSQL("update t set a=1"))
        self.con.rollback.assert_called_once_with()
        self.con.commit.assert_not_called()
        self.assertEqual(self.cmd.dbState, 2006)

    def testRunSelectSQL(self) -> None:
        self._setRows([(1, "a"), (2, "b")])
        self.assertEqual(self.cmd.runSelectSQL("select x, y from t"), [[1, "a"], [2, "b"]])
        self.con.commit.assert_called_once_with()
        self.curs.execute.assert_called_once_with("select x, y from t")
        self.assertIn("result length is 2", self.log.getvalue())

    def testRunSelectSQLNoneQuery(self) -> None:
        self.assertEqual(self.cmd.runSelectSQL(None), [])
        self.con.cursor.assert_not_called()

    def testRunSelectSQLError(self) -> None:
        self.curs.execute.side_effect = _failOn("select")
        self.assertIsNone(self.cmd.runSelectSQL("select * from t"))
        self.con.close.assert_called_once_with()
        self.assertEqual(self.cmd.dbState, 1146)
        self.assertIn("Failing on query select * from t", self.log.getvalue())

    def testSelectRowsMultiple(self) -> None:
        self._setRows([("D_1", "1abc", "REL"), ("D_2", "2abc", "HPUB")])
        rows = self.cmd.selectRows(TABLEDEF, {"STATUS_CODE": "REL"}, ["dep_set_id", "pdb_id"])
        self.assertEqual(
            rows,
            [
                {"DEP_SET_ID": "D_1", "PDB_ID": "1abc", "STATUS_CODE": "REL"},
                {"DEP_SET_ID": "D_2", "PDB_ID": "2abc", "STATUS_CODE": "HPUB"},
            ],
        )
        self.curs.execute.assert_called_once_with("SELECT dep_set_id,pdb_id,status_code FROM deposition WHERE  status_code = 'REL'  ORDER BY dep_set_id, pdb_id")

    def testSelectRowsSingleReturnsDict(self) -> None:
        self._setRows([("1abc",)])
        row = self.cmd.selectRows(TABLEDEF, {"DEP_SET_ID": "D_1"}, selectList=["PDB_ID"])
        self.assertEqual(row, {"PDB_ID": "1abc"})
        self.curs.execute.assert_called_once_with("SELECT pdb_id FROM deposition WHERE  dep_set_id = 'D_1' ")

    def testSelectRowsNoneReturnsEmptyDict(self) -> None:
        self._setRows([])
        self.assertEqual(self.cmd.selectRows(TABLEDEF, {}), {})

    def testSelectRowsError(self) -> None:
        self.curs.execute.side_effect = _failOn("SELECT", 2013)
        self.assertIsNone(self.cmd.selectRows(TABLEDEF, {}))
        self.assertEqual(self.cmd.dbState, 2013)
        self.con.close.assert_called_once_with()

    def testUpdateInsert(self) -> None:
        self.assertEqual(self.cmd.update("insert", TABLEDEF, {"DEP_SET_ID": "D_1", "PDB_ID": "it's"}), "ok")
        self.assertEqual(
            self._executed(),
            [("set autocommit=0",), ("INSERT INTO deposition SET  dep_set_id = 'D_1' ,  pdb_id = 'it\\'s' ",), ("set autocommit=1",)],
        )
        self.con.commit.assert_called_once_with()

    def testUpdateUpdateWithConstraint(self) -> None:
        self.assertEqual(self.cmd.update("UPDATE", TABLEDEF, {"PDB_ID": 'a"b', "STATUS_CODE": None}, {"DEP_SET_ID": "D_1"}), "ok")
        self.assertEqual(self._executed()[1], ("UPDATE deposition SET  pdb_id = 'a\\\"b' ,  status_code = NULL  WHERE  dep_set_id = 'D_1' ",))

    def testUpdateError(self) -> None:
        self.curs.execute.side_effect = _failOn("UPDATE")
        self.assertIsNone(self.cmd.update("update", TABLEDEF, {"PDB_ID": "x"}, {"DEP_SET_ID": "D_1"}))
        self.con.rollback.assert_called_once_with()
        self.con.close.assert_called_once_with()
        self.assertEqual(self.cmd.dbState, 1146)

    def testSelectCrossTables(self) -> None:
        self._setRows([("D_1", "W_1")])
        rows = self.cmd.selectCrossTables(
            ["deposition.dep_set_id", "wf_instance.wf_inst_id"], " FROM j", " order by 1", {"DEP_SET_ID": "deposition.dep_set_id"}, {"DEP_SET_ID": "D_1"}
        )
        self.assertEqual(rows, [{"deposition.dep_set_id": "D_1", "wf_instance.wf_inst_id": "W_1"}])
        self.curs.execute.assert_called_once_with("SELECT DISTINCT deposition.dep_set_id,wf_instance.wf_inst_id FROM j WHERE  deposition.dep_set_id = 'D_1'  order by 1")

    def testSelectCrossTablesError(self) -> None:
        self.curs.execute.side_effect = _failOn("SELECT")
        self.assertIsNone(self.cmd.selectCrossTables(["a"], " FROM j", "", {}, {}))
        self.assertEqual(self.cmd.dbState, 1146)


if __name__ == "__main__":
    unittest.main()

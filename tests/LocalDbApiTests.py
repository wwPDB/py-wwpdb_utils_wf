##
# File: LocalDbApiTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for LocalDbApi with the DbConnection collaborator mocked"""

import io
import sys
import unittest
from unittest.mock import patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

import MySQLdb

from wwpdb.utils.wf.dbapi.LocalDbApi import LocalDbApi

MODULE = "wwpdb.utils.wf.dbapi.LocalDbApi"


class LocalDbApiTests(unittest.TestCase):
    def setUp(self) -> None:
        connPatcher = patch(MODULE + ".DbConnection")
        self.mConnCls = connPatcher.start()
        self.addCleanup(connPatcher.stop)
        self.con = self.mConnCls.return_value.connect.return_value
        self.curs = self.con.cursor.return_value
        self.log = io.StringIO()

    def testConstructorConnects(self) -> None:
        LocalDbApi(log=self.log)
        self.mConnCls.assert_called_once_with(dbServer="mysql", dbHost="somehome", dbName="unknown", dbUser="user", dbPw="password", dbPort=3306)
        self.mConnCls.return_value.connect.assert_called_once_with()

    def testGetNewDepositedIds(self) -> None:
        self.curs.fetchone.side_effect = [("1abc",), ("2xyz",), None]
        api = LocalDbApi(log=self.log)
        self.assertEqual(api.getNewDepositedIds(7), ["1abc", "2xyz"])
        self.con.commit.assert_called_once_with()
        self.curs.execute.assert_called_once_with(
            "select lcase(structure_id) from rcsb_status where initial_deposition_date>=DATE_SUB(curdate(), interval 7 day) order by structure_id"
        )

    def testGetNewDepositedIdsEmpty(self) -> None:
        self.curs.fetchone.return_value = None
        self.assertEqual(LocalDbApi(log=self.log).getNewDepositedIds(1), [])

    def testGetNewDepositedIdsErrorExits(self) -> None:
        self.curs.execute.side_effect = MySQLdb.ProgrammingError(1146, "no table")
        api = LocalDbApi(log=self.log)
        with self.assertRaises(SystemExit) as cm:
            api.getNewDepositedIds(1)
        self.assertEqual(cm.exception.code, 1)
        self.curs.close.assert_called_once_with()
        self.con.close.assert_called_once_with()
        self.assertIn("Database error 1146: no table", self.log.getvalue())


if __name__ == "__main__":
    unittest.main()

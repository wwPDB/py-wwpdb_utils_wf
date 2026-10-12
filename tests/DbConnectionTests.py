##
# File: DbConnectionTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for DbConnection with MySQLdb.connect mocked"""

import io
import os
import sys
import unittest
from typing import Dict
from unittest.mock import MagicMock, patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

import MySQLdb

from wwpdb.utils.wf.dbapi.DbConnection import DbConnection

CONNECT = "wwpdb.utils.wf.dbapi.DbConnection.MySQLdb.connect"

ENV_VARS = {
    "MYSQL_DB_NAME": "envdb",
    "MYSQL_DB_USER": "envuser",
    "MYSQL_DB_PW": "envpw",
    "MYSQL_DB_HOST": "envhost",
    "MYSQL_DB_PORT": "3310",
    "MYSQL_DB_SOCKET": "/tmp/env.sock",  # noqa: S108
}


def _cleanEnv() -> Dict[str, str]:
    """Environment without any MYSQL_DB_* variables"""
    return {k: v for k, v in os.environ.items() if not k.startswith("MYSQL_DB_")}


class DbConnectionTests(unittest.TestCase):
    def testConnectExplicitArgs(self) -> None:
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            mConnect.return_value = MagicMock(name="conn")
            dbc = DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort=3306)
            con = dbc.connect()
        self.assertIs(con, mConnect.return_value)
        mConnect.assert_called_once_with(db="db1", user="u1", passwd="p1", port=3306, host="h1", local_infile=1)

    def testPortStringIsConvertedToInt(self) -> None:
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort="3307").connect()
        self.assertEqual(mConnect.call_args.kwargs["port"], 3307)

    def testNonNumericPortIsKept(self) -> None:
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort="abc").connect()
        self.assertEqual(mConnect.call_args.kwargs["port"], "abc")

    def testExplicitSocket(self) -> None:
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort=1, dbSocket="/var/my.sock").connect()
        mConnect.assert_called_once_with(db="db1", user="u1", passwd="p1", port=1, host="h1", unix_socket="/var/my.sock", local_infile=1)

    def testEnvironmentFallbacks(self) -> None:
        env = _cleanEnv()
        env.update(ENV_VARS)
        with patch.dict(os.environ, env, clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost=None).connect()
        mConnect.assert_called_once_with(db="envdb", user="envuser", passwd="envpw", port=3310, host="envhost", unix_socket="/tmp/env.sock", local_infile=1)  # noqa: S108

    def testExplicitArgsOverrideEnvironment(self) -> None:
        env = _cleanEnv()
        env.update(ENV_VARS)
        with patch.dict(os.environ, env, clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort=1, dbSocket="/s").connect()
        mConnect.assert_called_once_with(db="db1", user="u1", passwd="p1", port=1, host="h1", unix_socket="/s", local_infile=1)

    def testDefaultHostIsLocalhostAndMissingEnvGivesNone(self) -> None:
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection().connect()
        mConnect.assert_called_once_with(db="None", user="None", passwd="None", port=None, host="localhost", local_infile=1)

    def testUnsupportedServerExits(self) -> None:
        log = io.StringIO()
        with self.assertRaises(SystemExit) as cm:
            DbConnection(dbServer="oracle", log=log)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("unsupported server oracle", log.getvalue())

    def testConnectErrorExits(self) -> None:
        log = io.StringIO()
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            mConnect.side_effect = MySQLdb.OperationalError(2003, "Can't connect")
            dbc = DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort=3306, log=log)
            with self.assertRaises(SystemExit) as cm:
                dbc.connect()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Connection error 2003: Can't connect", log.getvalue())
        self.assertIn("host h1 dsn db1 user u1", log.getvalue())

    def testConnectErrorWithoutPortExits(self) -> None:
        # With no port configured, the failure message shows an empty port and the connection exits cleanly
        log = io.StringIO()
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            mConnect.side_effect = MySQLdb.OperationalError(2003, "Can't connect")
            dbc = DbConnection(dbName="db1", log=log)
            with self.assertRaises(SystemExit) as cm:
                dbc.connect()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(" port  socket ", log.getvalue())

    def testClose(self) -> None:
        con = MagicMock()
        with patch.dict(os.environ, _cleanEnv(), clear=True):
            DbConnection().close(con)
        con.close.assert_called_once_with()

    def testCommitUsesConnection(self) -> None:
        # commit() acts on the connection opened by connect()
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            dbc = DbConnection(dbPort=1)
            con = dbc.connect()
            dbc.commit()
        mConnect.return_value.commit.assert_called_once_with()
        mConnect.return_value.rollback.assert_not_called()
        self.assertIsNotNone(con)

    def testRollbackUsesConnection(self) -> None:
        # rollback() acts on the connection opened by connect()
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            dbc = DbConnection(dbPort=1)
            dbc.connect()
            dbc.rollback()
        mConnect.return_value.rollback.assert_called_once_with()
        mConnect.return_value.commit.assert_not_called()

    def testCommitAndRollbackBeforeConnectDoNothing(self) -> None:
        # With no stored connection, commit() and rollback() return quietly
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            dbc = DbConnection(dbPort=1)
            dbc.commit()
            dbc.rollback()
        mConnect.assert_not_called()

    def testCommitAndRollbackAfterCloseDoNothing(self) -> None:
        # close() clears the stored connection, so the closed connection is not used afterwards
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            dbc = DbConnection(dbPort=1)
            con = dbc.connect()
            dbc.close(con)
            dbc.commit()
            dbc.rollback()
        mConnect.return_value.close.assert_called_once_with()
        mConnect.return_value.commit.assert_not_called()
        mConnect.return_value.rollback.assert_not_called()

    @unittest.expectedFailure
    def testMissingPortIsNotPassedToDriver(self) -> None:
        # Library bug: with no port configured, port=None is passed to MySQLdb.connect(); mysqlclient then raises a
        # TypeError (not a MySQLdb.Error), which escapes connect() instead of exiting cleanly.  See ERRORS.md #4
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1").connect()
        self.assertIsInstance(mConnect.call_args.kwargs.get("port", 3306), int)

    @unittest.expectedFailure
    def testNonNumericPortIsNotPassedToDriver(self) -> None:
        # Library bug: a non-numeric port is passed through unchanged, and mysqlclient raises TypeError.  See ERRORS.md #4
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbHost="h1", dbName="db1", dbUser="u1", dbPw="p1", dbPort="abc").connect()
        self.assertIsInstance(mConnect.call_args.kwargs.get("port", 3306), int)

    @unittest.expectedFailure
    def testUnsetCredentialsAreNotStringNone(self) -> None:
        # Library bug: unset db/user/password are formatted with "%s", so the driver receives the string "None".  See ERRORS.md #5
        with patch.dict(os.environ, _cleanEnv(), clear=True), patch(CONNECT) as mConnect:
            DbConnection(dbPort=3306).connect()
        kwargs = mConnect.call_args.kwargs
        for key in ("db", "user", "passwd"):
            with self.subTest(key=key):
                self.assertNotEqual(kwargs.get(key), "None")


if __name__ == "__main__":
    unittest.main()

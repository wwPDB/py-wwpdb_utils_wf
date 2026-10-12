##
# File:  DbApiUtil.py
# Date:  04-May-2015
# Updates:
##
"""
Providing general APIs for database access

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2015 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import datetime
import os
import sys
import time
from typing import Any, Dict, Optional, TextIO, Tuple, Union, cast

import MySQLdb

#
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection

# A row from a MySQLdb DictCursor: {column name: value}
DbApiDictRow = Dict[str, Any]
# Result of a DictCursor fetchall()
DbApiDictRows = Tuple[DbApiDictRow, ...]
# Arguments for %-substitution into a schema map SQL template: a single value or a tuple of values
DbApiSqlParameter = Union[str, Tuple[Any, ...]]


class DbApiUtil:
    def __init__(
        self,
        dbServer: Optional[str] = None,
        dbHost: Optional[str] = None,
        dbName: Optional[str] = None,
        dbUser: Optional[str] = None,
        dbPw: Optional[str] = None,
        dbSocket: Optional[str] = None,
        dbPort: Optional[Union[int, str]] = None,
        verbose: bool = False,
        log: TextIO = sys.stderr,
    ) -> None:
        """ """
        self.__debug = False
        self.__Nretry = 5
        self.__dbServer = dbServer
        self.__dbHost = dbHost
        self.__dbName = dbName
        self.__dbUser = dbUser
        self.__dbPw = dbPw
        self.__dbSocket = dbSocket
        self.__dbPort = dbPort
        self.__verbose = verbose  # pylint: disable=unused-private-member
        self.__lfh = log
        self.__schemaMap: Dict[str, str] = {}
        self.__dbState = 0

        if self.__debug:
            self.__lfh.write("\n+DbApiUtil.__init__() using socket %r\n" % self.__dbSocket)
            self.__lfh.write("+DbApiUtil.__init__() using socket environment reference %r\n" % os.getenv("SITE_DB_SOCKET", None))

        self.__myDb = DbConnection(
            dbServer=self.__dbServer,
            dbHost=self.__dbHost,
            dbName=self.__dbName,
            dbUser=self.__dbUser,
            dbPw=self.__dbPw,
            dbPort=self.__dbPort,
            dbSocket=self.__dbSocket,
        )

        self.__dbcon = self.__myDb.connect()

    def __reConnect(self) -> bool:
        """ """
        try:
            self.__myDb.close(self.__dbcon)
        except MySQLdb.Error:
            self.__lfh.write("+DbApiUtil.reConnect() DB connection lost - cannot close\n")
            self.__lfh.write("+DbApiUtil.reConnect() Re-connecting to the database ..\n")
            self.__lfh.write("+DbApiUtil.reConnect() UTC time = %s\n" % datetime.datetime.utcnow())  # noqa: DTZ003

        for i in range(1, self.__Nretry):
            try:
                self.__dbcon = self.__myDb.connect()
                self.__dbState = 0
                return True
            except MySQLdb.Error:
                self.__lfh.write("+DbApiUtil.reConnect() Cannot get re-connection : trying again\n")
                time.sleep(2 * i)

        return False

    def __runSelectSQL(self, query: str) -> DbApiDictRows:
        """ """
        rows: DbApiDictRows = ()
        try:
            self.__dbcon.commit()  # type: ignore[no-untyped-call]
            curs = self.__dbcon.cursor(MySQLdb.cursors.DictCursor)
            curs.execute(query)
            rows = curs.fetchall()
        except MySQLdb.Error as e:
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %s: %s\n" % (e.args[0], e.args[1]))

        return rows

    def __runUpdateSQL(self, query: str) -> Optional[str]:
        """ """
        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
            _nrows = curs.execute(query)  # noqa: F841
            self.__dbcon.commit()  # type: ignore[no-untyped-call]
            curs.execute("set autocommit=1")
            curs.close()
            return "OK"
        except MySQLdb.Error as e:
            self.__dbcon.rollback()  # type: ignore[no-untyped-call]
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %s: %s\n" % (e.args[0], e.args[1]))
        #
        return None

    def setSchemaMap(self, schemaMap: Dict[str, str]) -> None:
        """ """
        self.__schemaMap = schemaMap

    def runSelectSQL(self, sql: str) -> Optional[DbApiDictRows]:
        """method to run a query"""
        for retry in range(1, self.__Nretry):
            ret = self.__runSelectSQL(sql)
            if ret is None:
                if self.__dbState > 0:
                    time.sleep(retry * 2)
                    if not self.__reConnect():
                        return None
                else:
                    return None
                #
            else:
                return ret
            #
        #
        return None

    def runUpdateSQL(self, sql: str) -> Optional[str]:
        """method to run a query"""
        for retry in range(1, self.__Nretry):
            ret = self.__runUpdateSQL(sql)
            if ret is None:
                if self.__dbState > 0:
                    time.sleep(retry * 2)
                    if not self.__reConnect():
                        return None
                else:
                    return None
                #
            else:
                return ret
            #
        #
        return None

    def runUpdate(self, table: Optional[str] = None, where: Optional[Dict[str, str]] = None, data: Optional[Dict[str, str]] = None) -> Optional[str]:
        if not table:
            return None
        #
        if (not where) and (not data):
            return None
        #
        rowExists = False
        if where:
            sql = (
                "select * from "  # noqa: S608
                + str(table)
                + " where "
                + " and ".join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.items()])
            )  # noqa: S608
            rows = self.runSelectSQL(sql)
            if rows and len(rows) > 0:
                rowExists = True
            #
        #
        if rowExists and (not data):
            return "OK"
        #
        if rowExists:
            sql = (
                "update "  # noqa: S608
                + str(table)
                + " set "
                + ",".join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in cast("Dict[str, str]", data).items()])  # data is set: "rowExists and not data" returned above
            )  # noqa: S608
            if where:
                sql += " where " + " and ".join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.items()])
            #
        else:
            sql = "insert into " + str(table) + " (" + ",".join(["%s" % (k) for k, v in where.items()])  # type: ignore[union-attr]  # see ERRORS.md #6
            if data:
                sql += "," + ",".join(["%s" % (k) for k, v in data.items()])
            #
            sql += ") values (" + ",".join(["'%s'" % (v.replace("'", "\\'")) for k, v in where.items()])  # type: ignore[union-attr]  # see ERRORS.md #6
            if data:
                sql += "," + ",".join(["'%s'" % (v.replace("'", "\\'")) for k, v in data.items()])
            #
            sql += ")"
        #
        return self.runUpdateSQL(sql)

    def runUpdateSQLwithKey(self, key: Optional[str] = None, parameter: DbApiSqlParameter = ()) -> Optional[str]:
        """ """
        if not key or not self.__schemaMap or (key not in self.__schemaMap):
            return None
        #
        sql = self.__schemaMap[key]
        if parameter:
            sql = self.__schemaMap[key] % parameter
        #
        return self.runUpdateSQL(sql)

    def selectData(self, key: Optional[str] = None, parameter: DbApiSqlParameter = ()) -> Optional[DbApiDictRows]:
        """ """
        if key is None or not self.__schemaMap or (key not in self.__schemaMap):
            return None
        #
        sql = self.__schemaMap[key]
        if parameter:
            sql = self.__schemaMap[key] % parameter
        #
        return self.runSelectSQL(sql)

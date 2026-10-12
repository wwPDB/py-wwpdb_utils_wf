"""
    File: DbConnection

 Database connection class (MYSQL only)

 __author__    = "Li Chen"
 __email__     = "lchen@rcsb.rutgers.edu"
 __version__   = "V0.01"
 __Date__      = "April 21, 2010"

Updated:

   07-Feb-2014  jdw  -  Add socket support --
   23-Mar-2016  jdw  -  make ports ints.
"""

import contextlib
import os
import sys
from typing import TYPE_CHECKING, Optional, TextIO, Union

import MySQLdb

if TYPE_CHECKING:
    from MySQLdb.connections import Connection


class DbConnection:
    """Class to encapsulate rdbms DBI connection ..."""

    def __init__(
        self,
        dbServer: Optional[str] = "mysql",
        dbHost: Optional[str] = "localhost",
        dbName: Optional[str] = None,
        dbUser: Optional[str] = None,
        dbPw: Optional[str] = None,
        dbPort: Optional[Union[int, str]] = None,
        dbSocket: Optional[str] = None,
        log: TextIO = sys.stderr,
        verbose: bool = True,
    ) -> None:
        self.__lfh = log
        self.__verbose = verbose  # pylint: disable=unused-private-member
        self.__debug = False
        if self.__debug:
            self.__lfh.write(
                "\n\n+DbConnection.connect(): Connection using server %s host %s dsn %s user %s pw %s port %s socket %s\n"
                % (dbServer, dbHost, dbName, dbUser, dbPw, dbPort if dbPort is not None else "", dbSocket)
            )

        self.__dbName: Optional[str]
        self.__dbUser: Optional[str]
        self.__dbPw: Optional[str]
        self.__dbHost: Optional[str]
        self.__dbPort: Optional[Union[int, str]]
        self.__dbSocket: Optional[str]
        if dbName is None:
            self.__dbName = os.getenv("MYSQL_DB_NAME")
        else:
            self.__dbName = dbName

        if dbUser is None:
            self.__dbUser = os.getenv("MYSQL_DB_USER")
        else:
            self.__dbUser = dbUser

        if dbPw is None:
            self.__dbPw = os.getenv("MYSQL_DB_PW")
        else:
            self.__dbPw = dbPw

        if dbHost is None:
            self.__dbHost = os.getenv("MYSQL_DB_HOST")
        else:
            self.__dbHost = dbHost

        if dbPort is None:
            self.__dbPort = os.getenv("MYSQL_DB_PORT")
        else:
            self.__dbPort = dbPort

        with contextlib.suppress(Exception):
            self.__dbPort = int(self.__dbPort)  # type: ignore[arg-type]  # None (no port configured) raises TypeError, suppressed on purpose

        if dbSocket is None:
            # try from the environment -
            tS = os.getenv("MYSQL_DB_SOCKET")
            if self.__debug:
                self.__lfh.write("+DbConnection.__init__ MYSQL_DB_SOCKET is %r\n" % tS)
            if tS is not None:
                self.__dbSocket = tS
            else:
                self.__dbSocket = None
        else:
            self.__dbSocket = dbSocket

        self.__dbServer = dbServer

        if dbServer != "mysql":
            self.__lfh.write("DbConnection::__init__(): unsupported server %s\n" % dbServer)
            sys.exit(1)

        self.__dbcon: Optional[Connection] = None

    def connect(self) -> "Connection":
        """Consistent db connection method...

        Return a connection object
        """
        try:
            if self.__dbSocket is None:
                dbcon = MySQLdb.connect(
                    db="%s" % self.__dbName,
                    user="%s" % self.__dbUser,
                    passwd="%s" % self.__dbPw,
                    port=self.__dbPort,
                    host="%s" % self.__dbHost,
                    local_infile=1,
                )
            else:
                dbcon = MySQLdb.connect(
                    db="%s" % self.__dbName,
                    user="%s" % self.__dbUser,
                    passwd="%s" % self.__dbPw,
                    port=self.__dbPort,
                    host="%s" % self.__dbHost,
                    unix_socket="%s" % self.__dbSocket,
                    local_infile=1,
                )

        except MySQLdb.Error as e:
            self.__lfh.write("+DbConnection.connect(): Connection error %s: %s\n" % (e.args[0], e.args[1]))
            self.__lfh.write(
                "+DbConnection.connect(): Connection failed using server %s host %s dsn %s user %s pw %s port %s socket %s\n"
                % (
                    self.__dbServer,
                    self.__dbHost,
                    self.__dbName,
                    self.__dbUser,
                    self.__dbPw,
                    self.__dbPort if self.__dbPort is not None else "",
                    self.__dbSocket,
                )
            )
            sys.exit(1)

        self.__dbcon = dbcon
        return dbcon

    def close(self, dbcon: "Connection") -> None:
        """
        Consistent db close connection method...
        """
        dbcon.close()  # type: ignore[no-untyped-call]
        self.__dbcon = None

    def commit(self) -> None:
        """
        Consistent db commit() method...
        """
        if self.__dbcon:
            self.__dbcon.commit()  # type: ignore[no-untyped-call]

    def rollback(self) -> None:
        """
        Consistent db rollback() method...
        """
        if self.__dbcon:
            self.__dbcon.rollback()  # type: ignore[no-untyped-call]

"""
   File: DbCommand

   Methods to build and execute relational database queries
   Part of original version written by jdw

   __author__    = "Li Chen"
   __email__     = "lchen@rcsb.rutgers.edu"
   __version__   = "V0.01"
   __Date__      = "April 21, 2010"


Updates :

       16-Dec-2016  jdw - fix string conversion of None values
       26-sep-2017  ep  - runInsertSQL/runUpdateSQL allow for parameterized arguments
                          to pass to db execute to handle quoting
"""

import sys
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, TextIO, Tuple, Union, cast

import MySQLdb

if TYPE_CHECKING:
    from MySQLdb.connections import Connection

    from wwpdb.utils.wf.schema.SchemaMapTypes import SchemaTableDef

# Logical attribute name -> SQL column (or qualified column) name
DbCommandAttribDict = Dict[str, str]
# Simple {logical name: value} constraint, ANDed together
DbCommandConstraintDict = Dict[str, Any]
# Compact constraint list: ('EQ'|..., attrib, value[, type]), ('LOGOP', 'AND'|'OR'|'NOT'), ('GROUP', 'BEGIN'|'END')
DbCommandConstraintList = List[Tuple[Any, ...]]
DbCommandDictRow = Dict[str, Any]


class DbCommand:
    """
    Parameterized SQL queries using Python DBI protocol...
    """

    def __init__(self, dbcon: Optional["Connection"], log: TextIO = sys.stderr, verbose: bool = False) -> None:
        # Tom : put in dbState to store the error code
        self.dbState = 0
        self.__dbcon: Connection = dbcon  # type: ignore[assignment]  # None only accepted for construction (tests/DbImportTests); all queries need a connection
        self.__lfh = log
        self.__verbose = verbose
        self.__ops = ["EQ", "GE", "GT", "LT", "LE", "LIKE", "NOT LIKE"]
        self.__opDict = {
            "EQ": "=",
            "GE": ">=",
            "GT": ">",
            "LT": "<",
            "LE": "<=",
            "LIKE": "LIKE",
            "NOT LIKE": "NOT LIKE",
        }
        self.__logOps = ["AND", "OR", "NOT"]
        self.__grpOps = ["BEGIN", "END"]
        self.__debug = True

    #

    def makeSqlSet(self, attribDict: DbCommandAttribDict, constraintDef: Union[DbCommandConstraintDict, DbCommandConstraintList]) -> str:
        """
        construct syntext in use of SQL commands like 'update' and 'insert'.
        e.g. SET key1 = value1 and key2 = value2 and ...

        Input: attribDict{} defined in WfSchemaMap and constraintDef{}
        Return: a string
        """

        changingVal = ""
        cType = str(type(constraintDef))

        if cType.find("dict") > 0:
            ld: List[str] = []
            for k, v in cast("DbCommandConstraintDict", constraintDef).items():
                if k in attribDict:
                    if v is None or v == "None":
                        c = " %s = NULL " % (attribDict[k])
                    else:
                        c = " %s = '%s' " % (attribDict[k], v)
                    ld.append(c)
                elif self.__verbose:
                    self.__lfh.write("DbCommand::makeSqlSet(): Warning -- %s is not defined in the database.\n" % (k))
                if len(ld) > 0:
                    changingVal = " SET " + ld[0]
                    for c in ld[1:]:
                        changingVal += ", " + c

        return changingVal

    def makeConstraintCross(self, constraintList: DbCommandAttribDict, constraintDef: DbCommandConstraintDict) -> str:
        """
        construct constraint syntext in use of SQL commands for
        querying multiple tables
        e.g. WHERE key1 = value1 and key2 > value2 and ...

        Input: constraintList[] defined in WfSchemaMap and constraintDef{}
        Return: a string

        """
        constraint = ""
        ld: List[str] = []
        for k, v in constraintDef.items():
            if k in constraintList:
                if v is None or v == "None":
                    c = " %s is NULL " % (constraintList[k])
                else:
                    c = " %s = '%s' " % (constraintList[k], v)
                ld.append(c)
            elif self.__verbose:
                self.__lfh.write("DbCommand::makeConstraintCross(): Warning -- %s is not a key in WfSchemaMap::_constraintList.\n" % (k))

            if len(ld) > 0:
                constraint = " WHERE " + ld[0]
                for c in ld[1:]:
                    constraint += " AND " + c

        return constraint

    def makeSqlConstraint(self, attribDict: DbCommandAttribDict, constraintDef: Union[DbCommandConstraintDict, DbCommandConstraintList, None]) -> str:
        """
        construct constraint syntext in use for SQL commands.
        e.g. WHERE key1 = value1 and key2 > value2 and ...

        Input: attribDict{} columns defined in WfSchemaMap and
               constraintDef is {} or []
        Return: a string
        """

        constraint = ""
        cType = str(type(constraintDef))
        c: Any  # reused: a SQL fragment (str) in the dict branch, a constraint tuple in the list branch

        if cType.find("dict") > 0:
            ld: List[str] = []
            for k, v in cast("DbCommandConstraintDict", constraintDef).items():
                if k in attribDict:
                    if v == "None" or v is None:
                        c = " %s is NULL " % (attribDict[k])
                    else:
                        c = " %s = '%s' " % (attribDict[k], v)
                    ld.append(c)

                elif k == "EXTERNAL_TABLE":
                    # "EXTERNAL_TABLE" is special designed for SQL syntax
                    # like " column in (select column from another table)"
                    c = "  %s " % (v)
                    ld.append(c)
                elif self.__verbose:
                    self.__lfh.write("DbCommand::makeSqlConstraint(): Warning -- %s is not defined in the database.\n" % (k))
                if len(ld) > 0:
                    constraint = " WHERE " + ld[0]
                    for c in ld[1:]:
                        constraint += " AND " + c
        elif cType.find("list") > 0:
            #
            # List of tuples with the following syntax:
            #
            # ('EQ'|'GE'|'GT'|'LT'|'LE'|'LIKE', AttribName, Value, type)
            # ('AND'|'OR')
            # ('GROUP', 'BEGIN|END')

            if len(cast("DbCommandConstraintList", constraintDef)) > 0:
                constraint += " WHERE "
                for c in cast("DbCommandConstraintList", constraintDef):
                    if len(c) == 4 and str(c[0]).upper() in self.__ops:  # noqa: PLR2004
                        if str(c[3]).upper() == "CHAR":
                            constraint += " %s %s '%s' " % (
                                attribDict[str(c[1]).upper()],
                                self.__opDict[str(c[0]).upper()],
                                str(c[2]),
                            )
                        else:
                            constraint += " %s %s %s " % (
                                attribDict[str(c[1]).upper()],
                                self.__opDict[str(c[0]).upper()],
                                str(c[2]),
                            )

                    elif len(c) == 3 and str(c[0]).upper() in self.__ops:  # noqa: PLR2004
                        constraint += " %s %s '%s' " % (
                            attribDict[str(c[1]).upper()],
                            self.__opDict[str(c[0]).upper()],
                            str(c[2]),
                        )
                    elif len(c) == 2 and str(c[0]).upper() == "GROUP" and str(c[1]).upper() in self.__grpOps:  # noqa: PLR2004
                        if str(c[1]).upper() == "BEGIN":
                            constraint += "("
                        else:
                            constraint += ")"
                    elif len(c) == 2 and str(c[0]).upper() == "LOGOP" and str(c[1]).upper() in self.__logOps:  # noqa: PLR2004
                        constraint += " %s " % str(c[1]).upper()
                    elif self.__lfh:
                        self.__lfh.write("Constraint error: %s\n" % str(c))

        else:
            #           Just ignore if constraints are entered as None
            #           if(self.__verbose):
            self.__lfh.write("DbCommand::makeSqlConstraint(): Warning -- constraint type error: %s\n" % str(cType))

        return constraint

    def makeOrderStr(self, orderList: List[str]) -> str:
        """
        construct a string "ORDER BY ..." in SQL command for cross tables search

        """
        orderBy = ""
        if len(orderList) > 0:
            orderBy = " ORDER BY " + orderList[0]
            for c in orderList[1:]:
                orderBy += ", " + c

        return orderBy

    def runInsertSQL(self, query: str, args: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None) -> Optional[int]:
        return self.runUpdateSQL(query, args)

    def runUpdateSQL(self, query: str, args: Optional[Union[Tuple[Any, ...], List[Any], Dict[str, Any]]] = None) -> Optional[int]:
        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
            nrows: int
            if args:
                nrows = curs.execute(query, args)
            else:
                nrows = curs.execute(query)
            self.__dbcon.commit()
            curs.execute("set autocommit=1")
            curs.close()
            return nrows
        except MySQLdb.Error as e:
            self.__dbcon.rollback()
            # TOm : no curs defined
            #            curs.execute("set autocommit=1")
            #            curs.close()
            self.dbState = e.args[0]
            return None

    def runSelectSQL(self, query: Optional[str]) -> Optional[List[List[Any]]]:
        """
        method to run a SQL query : no checking - just a simple method to
        get things working
        note that this does not use attrib list = but returns a list of lists.
        """
        returnList: List[List[Any]] = []

        if self.__debug:
            self.__lfh.write("\n+DbCommand.runSelectSQL - input query %r\n" % query)
        if query is not None:
            row: List[Any] = []
            try:
                self.__dbcon.commit()
                curs = self.__dbcon.cursor()
                curs.execute(query)
                while True:
                    result = curs.fetchone()
                    if result is not None:
                        row = []
                        ir = 0
                        for _k in result:
                            row.append(result[ir])
                            ir += 1  # noqa: SIM113
                        returnList.append(row)
                    else:
                        break
            except MySQLdb.Error as e:
                self.__lfh.write("DbCommand::runSelectSQL(): Database error %s: %s\n" % (e.args[0], e.args[1]))
                self.__lfh.write("DbCommand::runSelectSQL(): Failing on query %s\n" % query)
                # no curs defined here
                #                curs.close()
                self.__dbcon.close()
                self.dbState = e.args[0]
                return None
        #            sys.exit (1)
        #
        if self.__debug:
            self.__lfh.write("+DbCommand.runSelectSQL - result length is %s\n" % len(returnList))

        return returnList

    def selectRows(
        self,
        tableDef: "SchemaTableDef",
        constraintDef: Union[DbCommandConstraintDict, DbCommandConstraintList, None],
        orderList: Optional[List[str]] = None,
        selectList: Optional[List[str]] = None,
    ) -> Optional[Union[List[DbCommandDictRow], DbCommandDictRow]]:
        """
        Execute query on the table described by "tableDef"
        subject to the conditions in constraintDef and
        sorted by the list of attributes in orderList [(attrib,type),..].
        An optional selectList=[attrib,attrib] can be provided to limit
        the query selection.

        ConstraintDef can be a simple of dictionary of key == value pairs
        which are logically AND'd together, or a more general constraint
        can be constructed using the compact constraint specification list
        decoded in method makeSqlConstraint() above.

        Return a <row list or row dictionary>.
        """
        if orderList is None:
            orderList = []
        if selectList is None:
            selectList = []

        tableName = tableDef["TABLE_NAME"]
        attribDict = tableDef["ATTRIBUTES"]
        attribs: Iterable[str]
        if len(selectList) > 0:
            attribsCsv = ",".join(["%s" % attribDict[k] for k in selectList])
            attribs = selectList
        else:
            attribsCsv = ",".join(["%s" % v for v in attribDict.values()])
            attribs = attribDict.keys()

        #
        #  Build selection constraints ...
        #
        constraint = self.makeSqlConstraint(attribDict, constraintDef)

        order = ""
        if len(orderList) > 0:
            order = " ORDER BY " + orderList[0]
            for a in orderList[1:]:
                order += ", " + a
            # order += " desc "

        #
        query = "SELECT " + attribsCsv + " FROM " + tableName + constraint + order  # noqa: S608
        # Tom added verbose check
        if self.__verbose:
            self.__lfh.write("DB command --\n%s\n" % query)

        ##
        returnList: List[DbCommandDictRow] = []
        row: DbCommandDictRow = {}
        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor()
            curs.execute(query)
            while True:
                result = curs.fetchone()
                if result is not None:
                    row = {}
                    for ir, k in enumerate(attribs):
                        row[k] = result[ir]
                    returnList.append(row)
                else:
                    break
        except MySQLdb.Error as e:
            self.__lfh.write("DbCommand::selectRows(): Database error %s: %s\n" % (e.args[0], e.args[1]))
            self.__lfh.write("DbCommand::selectRows(): Failing on query %s\n" % query)
            # Tom : no curs defined here
            #            curs.close()
            self.__dbcon.close()
            self.dbState = e.args[0]
            return None
        #            sys.exit (1)

        if len(returnList) > 1:
            return returnList
        return row

    def update(  # noqa: A002  pylint: disable=redefined-builtin
        self,
        type: str,  # noqa: A002  pylint: disable=redefined-builtin
        tableDef: "SchemaTableDef",
        updateVal: Dict[str, Any],
        constraintDef: Union[DbCommandConstraintDict, DbCommandConstraintList, None] = None,  # noqa: A002
    ) -> Optional[str]:
        """
        Update value for any column(s) in a giving table.
        type may be 'insert' or 'update', default is 'insert'.
        tableDef in WfSchemaMap, updateVal{} and constraintDef{}
        for "update"
        """

        tableName = tableDef["TABLE_NAME"]
        attribDict = tableDef["ATTRIBUTES"]
        # modify the specicial characters like "'",""" in the updateVal
        updateValMod: Dict[str, Optional[str]] = {}
        v2: Optional[str] = ""
        for k, v in updateVal.items():
            if str(v).find("'") != -1:
                v2 = str(v).replace("'", "\\'")
            elif str(v).find('"') != -1:
                v2 = v.replace('"', '\\"')
            elif v is not None:
                v2 = str(v)
            else:
                v2 = v
            updateValMod[k] = v2

        updateSet = self.makeSqlSet(attribDict, updateValMod)
        constraint = ""
        if constraintDef is not None:
            constraint = self.makeSqlConstraint(attribDict, constraintDef)
        if type.lower() == "update":
            command = "UPDATE "
        else:
            command = "INSERT INTO "
        command += tableName + updateSet
        if constraint != "":
            command += constraint
        # Tom - added verbose check
        if self.__verbose:
            self.__lfh.write("DB command --\n%s\n" % command)

        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
            curs.execute(command)

        except MySQLdb.Error as e:
            self.__lfh.write("DbCommand::update(): Database error %s: %s\n" % (e.args[0], e.args[1]))

            self.__dbcon.rollback()
            # no curs defined here
            #            curs.execute("set autocommit=1")
            #            curs.close()
            self.__dbcon.close()
            self.dbState = e.args[0]
            return None

        self.__dbcon.commit()
        curs.execute("set autocommit=1")
        if self.__verbose:
            self.__lfh.write("DbCommand::update(): SQL command successfully executed.\n")
        curs.close()

        return "ok"

    def selectCrossTables(
        self, selectList: List[str], sqlJoinStr: str, orderBy: str, constraintList: DbCommandAttribDict, constraintDef: Optional[DbCommandConstraintDict] = None
    ) -> Optional[List[DbCommandDictRow]]:
        """
        This function is specially for some complicate queries. The
        "sql join" is used.

        Input selectList, sqlJoinStr, orderBy will be
        specially defined in WfSchemaMap. constraintDict is {}

        Return a list of rows {dictionaries)

        """

        attribsCsv = ",".join(["%s" % k for k in selectList])

        constraint = self.makeConstraintCross(constraintList, constraintDef)  # type: ignore[arg-type]  # latent bug: the None default crashes in makeConstraintCross
        query = "SELECT DISTINCT " + attribsCsv + sqlJoinStr + constraint + orderBy
        # Tom - added verbose check
        if self.__verbose:
            self.__lfh.write("DB command --\n%s\n" % query)

        returnList: List[DbCommandDictRow] = []
        row: DbCommandDictRow = {}

        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor()
            curs.execute(query)
            while True:
                result = curs.fetchone()
                if result is not None:
                    row = {}
                    ir = 0
                    for k in selectList:
                        row[k] = result[ir]
                        ir += 1  # noqa: SIM113
                    returnList.append(row)
                else:
                    break
        except MySQLdb.Error as e:
            self.__lfh.write("DbCommand::selectRows(): Database error %s: %s\n" % (e.args[0], e.args[1]))
            # Tom : no curs defined here
            #          curs.close()
            self.dbState = e.args[0]
            return None

        return returnList

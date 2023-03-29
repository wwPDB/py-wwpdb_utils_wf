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
import MySQLdb


class DbCommand:
    """
    Parameterized SQL queries using Python DBI protocol...
    """

    def __init__(self, dbcon, log=sys.stderr, verbose=False):
        # Tom : put in dbState to store the error code
        self.dbState = 0
        self.__dbcon = dbcon
        self.__lfh = log
        self.__verbose = verbose
        self.__ops = ["EQ", "GE", "GT", "LT", "LE", "LIKE", "NOT LIKE"]
        self.__opDict = {"EQ": "=", "GE": ">=", "GT": ">", "LT": "<", "LE": "<=", "LIKE": "LIKE", "NOT LIKE": "NOT LIKE"}
        self.__logOps = ["AND", "OR", "NOT"]
        self.__grpOps = ["BEGIN", "END"]
        self.__debug = True

    #

    def makeSqlSet(self, attribDict, constraintDef):
        """
        construct syntext in use of SQL commands like 'update' and 'insert'.
        e.g. SET key1 = value1 and key2 = value2 and ...

        Input: attribDict{} defined in WfSchemaMap and constraintDef{}
        Return: a string
        """

        changingVal = ""
        cType = str(type(constraintDef))

        if cType.find("dict") > 0:
            ld = []
            for k, v in constraintDef.items():
                if k in attribDict.keys():
                    if v is None or v == "None":
                        c = " %s = NULL " % (attribDict[k])
                    else:
                        c = " %s = '%s' " % (attribDict[k], v)
                    ld.append(c)
                else:
                    if self.__verbose:
                        self.__lfh.write("DbCommand::makeSqlSet(): Warning -- %s is not defined in the database.\n" % (k))
                if len(ld) > 0:
                    changingVal = " SET " + ld[0]
                    for c in ld[1:]:
                        changingVal += ", " + c

        return changingVal

    def makeConstraintCross(self, constraintList, constraintDef):
        """
        construct constraint syntext in use of SQL commands for
        querying multiple tables
        e.g. WHERE key1 = value1 and key2 > value2 and ...

        Input: constraintList[] defined in WfSchemaMap and constraintDef{}
        Return: a string

        """
        constraint = ""
        ld = []
        for k, v in constraintDef.items():
            if k in constraintList.keys():
                if v is None or v == "None":
                    c = " %s is NULL " % (constraintList[k])
                else:
                    c = " %s = '%s' " % (constraintList[k], v)
                ld.append(c)
            else:
                if self.__verbose:
                    self.__lfh.write("DbCommand::makeConstraintCross(): Warning -- %s is not a key in WfSchemaMap::_constraintList.\n" % (k))

            if len(ld) > 0:
                constraint = " WHERE " + ld[0]
                for c in ld[1:]:
                    constraint += " AND " + c

        return constraint

    def makeSqlConstraint(self, attribDict, constraintDef):
        """
        construct constraint syntext in use for SQL commands.
        e.g. WHERE key1 = value1 and key2 > value2 and ...

        Input: attribDict{} columns defined in WfSchemaMap and
               constraintDef is {} or []
        Return: a string
        """

        constraint = ""
        cType = str(type(constraintDef))

        if cType.find("dict") > 0:
            ld = []
            for k, v in constraintDef.items():
                if k in attribDict.keys():
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
                else:
                    if self.__verbose:
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

            if len(constraintDef) > 0:
                constraint += " WHERE "
                for c in constraintDef:
                    if len(c) == 4 and str(c[0]).upper() in self.__ops:

                        if str(c[3]).upper() == "CHAR":
                            constraint += " %s %s '%s' " % (attribDict[str(c[1]).upper()], self.__opDict[str(c[0]).upper()], str(c[2]))
                        else:
                            constraint += " %s %s %s " % (attribDict[str(c[1]).upper()], self.__opDict[str(c[0]).upper()], str(c[2]))

                    elif len(c) == 3 and str(c[0]).upper() in self.__ops:
                        constraint += " %s %s '%s' " % (attribDict[str(c[1]).upper()], self.__opDict[str(c[0]).upper()], str(c[2]))
                    elif len(c) == 2 and str(c[0]).upper() == "GROUP" and str(c[1]).upper() in self.__grpOps:  # noqa: W504
                        if str(c[1]).upper() == "BEGIN":
                            constraint += "("
                        else:
                            constraint += ")"
                    elif len(c) == 2 and str(c[0]).upper() == "LOGOP" and str(c[1]).upper() in self.__logOps:  # noqa: W504
                        constraint += " %s " % str(c[1]).upper()
                    else:
                        if self.__lfh:
                            self.__lfh.write("Constraint error: %s\n" % str(c))

        else:
            #           Just ignore if constraints are entered as None
            #           if(self.__verbose):
            self.__lfh.write("DbCommand::makeSqlConstraint(): Warning -- constraint type error: %s\n" % str(cType))

        return constraint

    def makeOrderStr(self, orderList):
        """
        construct a string "ORDER BY ..." in SQL command for cross tables search

        """
        orderBy = ""
        if len(orderList) > 0:
            orderBy = " ORDER BY " + orderList[0]
            for c in orderList[1:]:
                orderBy += ", " + c

        return orderBy

    def runInsertSQL(self, query, args=None):
        return self.runUpdateSQL(query, args)

    def runUpdateSQL(self, query, args=None):
        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
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

    def runSelectSQL(self, query):
        """
        method to run a SQL query : no checking - just a simple method to
        get things working
        note that this does not use attrib list = but returns a list of lists.
        """
        returnList = []

        if self.__debug:
            self.__lfh.write("\n+DbCommand.runSelectSQL - input query %r\n" % query)
        if query is not None:
            row = []
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
                            ir += 1
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

    def selectRows(self, tableDef, constraintDef, orderList=None, selectList=None):
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
        query = "SELECT " + attribsCsv + " FROM " + tableName + constraint + order
        # Tom added verbose check
        if self.__verbose:
            self.__lfh.write("DB command --\n%s\n" % query)

        ##
        returnList = []
        row = {}
        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor()
            curs.execute(query)
            while True:
                result = curs.fetchone()
                if result is not None:
                    row = {}
                    ir = 0
                    for k in attribs:
                        row[k] = result[ir]
                        ir += 1
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
        else:
            return row

    def update(self, type, tableDef, updateVal, constraintDef=None):  # pylint: disable=redefined-builtin
        """
        Update value for any column(s) in a giving table.
        type may be 'insert' or 'update', default is 'insert'.
        tableDef in WfSchemaMap, updateVal{} and constraintDef{}
        for "update"
        """

        tableName = tableDef["TABLE_NAME"]
        attribDict = tableDef["ATTRIBUTES"]
        # modify the specicial characters like "'",""" in the updateVal
        updateValMod = {}
        v2 = ""
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

    def selectCrossTables(self, selectList, sqlJoinStr, orderBy, constraintList, constraintDef=None):
        """
        This function is specially for some complicate queries. The
        "sql join" is used.

        Input selectList, sqlJoinStr, orderBy will be
        specially defined in WfSchemaMap. constraintDict is {}

        Return a list of rows {dictionaries)

        """

        attribsCsv = ",".join(["%s" % k for k in selectList])

        constraint = self.makeConstraintCross(constraintList, constraintDef)
        query = "SELECT DISTINCT " + attribsCsv + sqlJoinStr + constraint + orderBy
        # Tom - added verbose check
        if self.__verbose:
            self.__lfh.write("DB command --\n%s\n" % query)

        returnList = []
        row = {}

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
                        ir += 1
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

"""

    File:    WfDbApi.py

    Providing APIs for workflow engine and workflow manager in D&A tool

   __author__    = "Li Chen"
   __email__     = "lchen@rcsb.rutgers.edu"
   __version__   = "V0.01"
   __Date__      = "April 21, 2010"

 Updates:
  07-Feb-2014  to  add processStatus()
  07-Feb-2014  jdw add socket support
   4-Aug-2014  jdw add debug flag to minimize connection tracking logging
  26-sep-2017  ep  runInsertSQL/runUpdateSQL allow for parameterized arguments
                   to pass to db execute to handle quoting
  15-Jul-2019  ep  add siteId as optional argument to __init__

"""

import os
import sys
import time
import datetime
import MySQLdb

#
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection
from wwpdb.utils.wf.dbapi.DbCommand import DbCommand
from wwpdb.utils.wf.schema.WfSchemaMap import WfSchemaMap
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.wf.dbapi.WFEtime import getTimeNow


class WfDbApi:
    """
    Sample of WfSchemaMap class:

     _schemaMap = {
       "DEPOSITION" : {
                 "ATTRIBUTES"{dictionary of columns}
                 "TABLE_NAME"  : "deposition"
                      }
       "WF_TASK"    : {
                 "ATTRIBUTES"{dictionary of columns}
                 "TABLE_NAME"  : "wf_task"
                      }
                  }

    """

    # This could be rewritten wih inheritance - later
    # pylint is picking up on shared data among instances and thinks unused
    __schemaWf = WfSchemaMap._schemaMap  # pylint: disable=protected-access,unused-private-member
    __selectList = WfSchemaMap._selectColumns  # pylint: disable=protected-access,unused-private-member
    __constraintList = WfSchemaMap._constraintList  # pylint: disable=protected-access,unused-private-member
    # __statusList = WfSchemaMap._columnForStatus
    __statusList = WfSchemaMap._usefulItems[0:3]  # pylint: disable=protected-access,unused-private-member
    __columnList = WfSchemaMap._usefulItems  # pylint: disable=protected-access,unused-private-member
    __tableList = WfSchemaMap._tables  # pylint: disable=protected-access,unused-private-member
    __idList = WfSchemaMap._objIds  # pylint: disable=protected-access,unused-private-member
    __refList = WfSchemaMap._referencePairs  # pylint: disable=protected-access,unused-private-member
    __sqlJoinStr = WfSchemaMap._tableJoinSyntext  # pylint: disable=protected-access,unused-private-member
    __orderBy = WfSchemaMap._orderBy  # pylint: disable=protected-access,unused-private-member
    __userInfo = WfSchemaMap._userInfo  # pylint: disable=protected-access,unused-private-member

    def __init__(self, log=sys.stderr, verbose=False, siteId=None):
        """
        Either siteId needs to be specified or Environmental variable WWPDB_SITE_ID needs to be set
        for ConfigInfo() to obtain the correct details -

        """

        self.__Nretry = 5
        self.__lfh = log
        self.__verbose = verbose
        self.__debug = False
        cI = ConfigInfo(siteId=siteId)
        self.__dbServer = cI.get("SITE_DB_SERVER")
        self.__dbHost = cI.get("SITE_DB_HOST_NAME")
        self.__dbName = cI.get("SITE_DB_DATABASE_NAME")
        self.__dbUser = cI.get("SITE_DB_USER_NAME")
        self.__dbPw = cI.get("SITE_DB_PASSWORD")
        self.__dbSocket = cI.get("SITE_DB_SOCKET")
        self.__dbPort = int("%s" % cI.get("SITE_DB_PORT_NUMBER"))

        if self.__debug:
            self.__lfh.write("\n+WfDbApi.__init__() using socket %r\n" % self.__dbSocket)
            self.__lfh.write("+WfDbApi.__init__() using socket environment reference %r\n" % os.getenv("SITE_DB_SOCKET", None))

        self.__myDb = DbConnection(
            dbServer=self.__dbServer, dbHost=self.__dbHost, dbName=self.__dbName, dbUser=self.__dbUser, dbPw=self.__dbPw, dbPort=self.__dbPort, dbSocket=self.__dbSocket
        )

        self.__dbcon = self.__myDb.connect()
        self.__db = DbCommand(self.__dbcon, self.__lfh, self.__verbose)

    def reConnect(self):
        """
        Tom : Method to re connect on error with connection
        """
        try:
            self.__myDb.close(self.__dbcon)
        except MySQLdb.Error:
            self.__lfh.write("+WfDbApi.reConnect() DB connection lost - cannot close\n")
            self.__lfh.write("+WfDbApi.reConnect() Re-connecting to the database ..\n")
            self.__lfh.write("+WfDbApi.reConnect() UTC time = %s\n" % datetime.datetime.utcnow())

        for i in range(1, 5):
            try:
                self.__dbcon = self.__myDb.connect()
                self.__db = DbCommand(self.__dbcon, self.__lfh, self.__verbose)
                return True
            except MySQLdb.Error:
                self.__lfh.write("+WfDbApi.reConnect() Cannot get re-connection : trying again\n")
                time.sleep(2 * i)

        return False

    def testConnection(self):
        """
        Test if connection is lost. if yes, rebuild the connection
        """

        if str(self.__dbcon).find("closed") > 0:

            self.__lfh.write("+WfDbApi::testConnection(): Re-connecting to the database.\n")
            self.__dbcon = self.__myDb.connect()
            self.__db = DbCommand(self.__dbcon, self.__lfh, self.__verbose)

    def isConnected(self):
        """Return boolean flag for connection status -"""
        try:
            if str(self.__dbcon).find("open") > 0:
                return True
        except Exception as _e:  # noqa: F841
            pass
        return False

    def close(self):
        """
        This function is only for detecting the connection problem
        """

        if str(self.__dbcon).find("open") > 0:
            self.__myDb.close(self.__dbcon)
            if self.__debug:
                self.__lfh.write("WfDbApi::close(): Closing a connection\n")

    def runInsertSQL(self, sql, args=None):
        """
        method to run a query
        """
        #        self.testConnection()
        for retry in range(1, self.__Nretry):
            ret = self.__db.runInsertSQL(sql, args)
            if ret is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                    # loop again
                else:
                    # unhandled DB error
                    return None
            else:
                return ret

    def runUpdateSQL(self, sql, args=None):
        """
        method to run a query
        """
        # self.testConnection()
        for retry in range(1, self.__Nretry):
            ret = self.__db.runUpdateSQL(sql, args)
            if ret is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                else:
                    # unhandled DB error
                    return None
            else:
                return ret

        # all retries gone bad
        return None

    def runSelectSQL(self, sql):
        """
        method to run a query
        """

        # self.testConnection()
        for retry in range(1, self.__Nretry):
            ret = self.__db.runSelectSQL(sql)
            if ret is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                    # Fall through to loop
                else:
                    # unhandled DB error
                    return None
            else:
                return ret

        # all retries gone bad
        return None

    def getObject(self, depId=None, classId=None, instId=None, taskId=None):
        """
        Get an object by the depId,,classId,instId,taskId
        return a dictionary of table content
        the table is depended on giving depId,classId,instId and taskId

        If all 4 ids are provided, table is wf_task
        if depId,classId,instId provided, but not taskId, table is wf_instance
        if only depId, go to the table deposition
        if classId is provide, depId is empty, the table is wf_class_dict

        Return a dictionary
        The keys are ATTRIBUTES defined in WfSchemaMap._schemaMap and
        The table name is one of (deposition,wf_class_dict,wf_instance,wf_task)

        """

        tableDef = {}
        rDict = {}
        constraintDict = {}
        orderList = []
        depId = self.checkId(depId)
        classId = self.checkId(classId)
        instId = self.checkId(instId)
        taskId = self.checkId(taskId)

        if depId is not None and classId is not None and instId is not None and taskId is not None:
            # table wf_task
            tableDef = self.__schemaWf[self.__tableList[3]]
        elif depId is not None and classId is not None and instId is not None and taskId is None:
            # table wf_instance
            tableDef = self.__schemaWf[self.__tableList[2]]
        elif depId is None and classId is not None and instId is None and taskId is None:
            # table wf_class_dict (depId must be None)
            tableDef = self.__schemaWf[self.__tableList[1]]
        elif depId is not None and classId is None and instId is None and taskId is None:
            # table deposition
            tableDef = self.__schemaWf[self.__tableList[0]]
        else:
            if self.__verbose:
                self.__lfh.write("WfDbApi::getObject(): Wrong parameters, check all input ids\n")
            return rDict

        if depId is not None:
            constraintDict[self.__idList[0]] = depId
        if classId is not None:
            constraintDict[self.__idList[1]] = classId
        if instId is not None:
            constraintDict[self.__idList[2]] = instId
        if taskId is not None:
            constraintDict[self.__idList[3]] = taskId

        if tableDef == self.__schemaWf[self.__tableList[3]] or tableDef == self.__schemaWf[self.__tableList[2]]:
            orderList.append("ORDINAL")

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            if len(orderList) > 0:
                rDict = self.__db.selectRows(tableDef, constraintDict, orderList)
            else:
                rDict = self.__db.selectRows(tableDef, constraintDict)

            if rDict is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                    # Fall through
                else:
                    # unhandle DB error
                    return None
            else:
                return rDict

        # Retried loop all gone bad
        return None

    def saveObject(self, dataObj, type="insert", constraintDict=None):  # pylint: disable=redefined-builtin
        """
        insert/update a new record in the database
        This method currently is for save one of objects in following list
        deposition, class, instance, task
        """

        for i in [3, 2, 1, 0]:
            if self.__idList[i] in dataObj.keys():
                dataObj[self.__idList[i]] = self.checkId(dataObj[self.__idList[i]])
                if dataObj[self.__idList[i]] is None:
                    self.__lfh.write("WfDbApi::saveObject(): %s can not be None or empty string." % self.__idList[i])
                    exit(1)

        tableDef = self.getTableDef(dataObj)
        if len(tableDef) > 0:

            for retry in range(1, self.__Nretry):

                ret = self.__db.update(type, tableDef, dataObj, constraintDict)

                if ret is None:
                    # database error -
                    if self.__db.dbState > 0:
                        # 2006 : database went away
                        time.sleep(retry * 2)  # backoff for increasing waits
                        if not self.reConnect():
                            return None
                        # else loop
                    else:
                        # unhandled DB error
                        return None
                else:
                    return ret

            # retry limit - all gone bad
            return None

        else:
            self.__lfh.write("WfDbApi::saveObject(): The data object is not the one of deposition, class, instance, task\nNothing is done.\n")
            return "bad-code"

    def getStatus(self, dataObj):
        """
        Get status from a dataObj(could be a deposition, instance or task obj)
        return a string. if dataObj is not a right type, return an empty str.
        """

        returnObj = {}
        oType = str(type(dataObj))
        if oType.find("dict") > 0:
            returnObj = dataObj
        elif oType.find("list") > 0:
            num = len(dataObj)
            # get the last record
            returnObj = dataObj[num - 1]

        for _k, _v in returnObj.items():  # Not clear why for loop
            # a task
            if self.__idList[3] in returnObj.keys() and self.__idList[2] in returnObj.keys() and self.__idList[1] in returnObj.keys() and self.__idList[0] in returnObj.keys():
                return returnObj[self.__statusList[2]]
            # a instance
            elif (
                self.__idList[3] not in returnObj.keys() and self.__idList[2] in returnObj.keys() and self.__idList[1] in returnObj.keys() and self.__idList[0] in returnObj.keys()
            ):
                return returnObj[self.__statusList[1]]
            # a deposition
            elif (
                self.__idList[0] in returnObj.keys()
                and self.__idList[1] not in returnObj.keys()
                and self.__idList[2] not in returnObj.keys()
                and self.__idList[3] not in returnObj.keys()
            ):
                return returnObj[self.__statusList[0]]

            else:
                pass

        return ""

    def updateStatus(self, dataObj, status=None):
        """
        Change status for one entry in table deposition, wf_instance or wf_task

        """
        stype = "update"
        if status is None or status == "":
            self.__lfh.write("WfDbApi::updateStatus(): Failing - no status code given\n")
            exit(1)

        tableDef = self.getTableDef(dataObj)
        if len(tableDef) > 0:
            updateVal = {}
            updateVal = self.assignStatus(tableDef, status)

            rDict = {}
            constraintDict = {}
            if self.__idList[0] in dataObj.keys() and dataObj[self.__idList[0]] is not None and dataObj[self.__idList[0]] != "":
                constraintDict[self.__idList[0]] = dataObj[self.__idList[0]]
            if self.__idList[1] in dataObj.keys() and dataObj[self.__idList[1]] is not None and dataObj[self.__idList[1]] != "":
                constraintDict[self.__idList[1]] = dataObj[self.__idList[1]]
            if self.__idList[2] in dataObj.keys() and dataObj[self.__idList[2]] is not None and dataObj[self.__idList[2]] != "":
                constraintDict[self.__idList[2]] = dataObj[self.__idList[2]]
            if self.__idList[3] in dataObj.keys() and dataObj[self.__idList[3]] is not None and dataObj[self.__idList[3]] != "":
                constraintDict[self.__idList[3]] = dataObj[self.__idList[3]]

            # self.testConnection()
            for retry in range(1, self.__Nretry):

                rDict = self.__db.update(stype, tableDef, updateVal, constraintDict)

                if rDict is None:
                    # database error -
                    if self.__db.dbState > 0:
                        # 2006 : database went away
                        time.sleep(retry * 2)  # backoff for increasing waits
                        if not self.reConnect():
                            return None
                        # else loop
                    else:
                        # unhandle DB error
                        return None
                else:
                    return "ok"

            # retried - all gone bad
            return None

        else:
            self.__lfh.write("+WfDbApi::updateStatus(): The data object is not the one of deposition, instance, task. Nothing is updated.\n")
            return "code-bad"

    def processStatus(self, depID, instID, classID):
        """
        status owner of process
        None : this depID/instID/classID does NOT own the current process
        <value> : the status
        """

        try:
            sql = "select inst_status from dep_last_instance where dep_set_id = '" + str(depID) + "' AND inst_id = '" + str(instID) + "' AND class_id = '" + str(classID) + "'"
            print(sql)
            rows = self.runSelectSQL(sql)
            self.close()
            for row in rows:
                return row[0]

            return None
        except Exception as e:
            print("Exception in processOwner " + str(e))
            return None

    def getReference(self, depId=None, classId=None, instId=None, taskId=None):
        """
        Get a list of reference data from table wf_reference
        An empty id will be treated as None.

        Return a row list or dictionary (if only one record)
        """

        tableDef = self.__schemaWf[self.__tableList[4]]
        depId = self.checkId(depId)
        classId = self.checkId(classId)
        instId = self.checkId(instId)
        taskId = self.checkId(taskId)
        constraintDict = {}
        if depId is not None:
            constraintDict[self.__idList[0]] = depId
        else:
            constraintDict[self.__idList[0]] = "None"
        if classId is not None:
            constraintDict[self.__idList[1]] = classId
        else:
            constraintDict[self.__idList[1]] = "None"
        if instId is not None:
            constraintDict[self.__idList[2]] = instId
        else:
            constraintDict[self.__idList[2]] = "None"
        if taskId is not None:
            constraintDict[self.__idList[3]] = taskId
        else:
            constraintDict[self.__idList[3]] = "None"

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            results = self.__db.selectRows(tableDef, constraintDict)

            if results is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                    # loop
                else:
                    # unhandled DB error
                    return None
            else:
                return results

        # retried all gone bad
        return None

    def addReference(self, type, depId=None, classId=None, instId=None, taskId=None, hashId=None, hashVal=None):  # pylint: disable=redefined-builtin
        """
        Add or update reference record in the table wf_reference

        requirement:
        For a deposition level reference,the classId, instId and taskId should be None
        For a class level reference the instId, taskId should be None
        For a instance level reference taskId should be None
        For a task level reference all ids should be Non-null.


        """

        tableDef = self.__schemaWf[self.__tableList[4]]
        constraintDict = {}
        updateVal = {}
        depId = self.checkId(depId)
        classId = self.checkId(classId)
        instId = self.checkId(instId)
        taskId = self.checkId(taskId)

        type = type.lower()
        if type == "update":
            if depId is not None:
                constraintDict[self.__idList[0]] = depId
            else:
                constraintDict[self.__idList[0]] = "None"
            if classId is not None:
                constraintDict[self.__idList[1]] = classId
            else:
                constraintDict[self.__idList[1]] = "None"
            if instId is not None:
                constraintDict[self.__idList[2]] = instId
            else:
                constraintDict[self.__idList[2]] = "None"
            if taskId is not None:
                constraintDict[self.__idList[3]] = taskId
            else:
                constraintDict[self.__idList[3]] = "None"
            if hashId is not None and self.__refList[0] in tableDef["ATTRIBUTES"].keys():
                constraintDict[self.__refList[0]] = hashId
        else:
            if depId is not None:
                updateVal[self.__idList[0]] = depId
            if classId is not None:
                updateVal[self.__idList[1]] = classId
            if instId is not None:
                updateVal[self.__idList[2]] = instId
            if taskId is not None:
                updateVal[self.__idList[3]] = taskId

            if hashId is not None and self.__refList[0] in tableDef["ATTRIBUTES"].keys():
                updateVal[self.__refList[0]] = hashId

        if hashVal is not None and self.__refList[1] in tableDef["ATTRIBUTES"].keys():
            updateVal[self.__refList[1]] = hashVal

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            ret = self.__db.update(type, tableDef, updateVal, constraintDict)

            if ret is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                else:
                    # unhandled DB error
                    return None
            else:
                return "ok"

        # all bad
        return None

    def checkId(self, str):  # pylint: disable=redefined-builtin
        """
        Test if an object id is empty.
        If yes return None, else return str.
        """
        if str == "":
            return None
        else:
            return str

    def exist(self, dataObj):
        """
        Test if a dataObj exists in the Database based on IDs
        dataObj is only for one of objects(deposition, class, instance, task).
        Return Ture or False
        """

        existObj = False
        depId = None
        classId = None
        instId = None
        taskId = None
        rd = {}

        if len(dataObj) == 0:
            existObj = False
        else:
            if self.__idList[3] in dataObj.keys():
                taskId = dataObj[self.__idList[3]]
            if self.__idList[2] in dataObj.keys():
                instId = dataObj[self.__idList[2]]
            if self.__idList[1] in dataObj.keys():
                classId = dataObj[self.__idList[1]]
            if self.__idList[0] in dataObj.keys():
                depId = dataObj[self.__idList[0]]
            if depId is None and classId is None and instId is None and taskId is None:
                existObj = False
            else:
                rd = self.getObject(depId, classId, instId, taskId)

                if len(rd) > 0:
                    existObj = True
                else:
                    existObj = False

        return existObj

    def getTableDef(self, dataObj):
        """
        Determine which table to use in the database

        If all 4 ids are in the dataObj, table is wf_task
        if instId is provided, but not taskId, table is wf_instance
        if only depId, go to the table deposition
        if classId is provide, depId is empty, the table is wf_class_dict
        Return table dict in __schemaWf
        """

        tableDef = {}
        if self.__idList[3] in dataObj.keys() and self.__idList[2] in dataObj.keys() and self.__idList[1] in dataObj.keys() and self.__idList[0] in dataObj.keys():
            tableDef = self.__schemaWf[self.__tableList[3]]
        if self.__idList[3] not in dataObj.keys() and self.__idList[2] in dataObj.keys() and self.__idList[1] in dataObj.keys() and self.__idList[0] in dataObj.keys():
            tableDef = self.__schemaWf[self.__tableList[2]]
        if self.__idList[3] not in dataObj.keys() and self.__idList[2] not in dataObj.keys() and self.__idList[1] in dataObj.keys() and self.__idList[0] not in dataObj.keys():
            tableDef = self.__schemaWf[self.__tableList[1]]
        if self.__idList[3] not in dataObj.keys() and self.__idList[2] not in dataObj.keys() and self.__idList[1] not in dataObj.keys() and self.__idList[0] in dataObj.keys():
            tableDef = self.__schemaWf[self.__tableList[0]]

        return tableDef

    def assignStatus(self, tableDef, status):
        """
        Set status value for table in tableDef

        Return: a dictionary of update Values

        """

        attribDict = tableDef["ATTRIBUTES"]
        updateDict = {}
        for k in range(len(self.__statusList)):
            if self.__statusList[k] in attribDict.keys():
                updateDict[self.__statusList[k]] = status
                # Tom : added change to timestamp when we make a status change
                # Tom : only valid for task and instance : check schema.usefulItems ending in status
                if self.__statusList[k].endswith("STATUS"):
                    updateDict["STATUS_TIMESTAMP"] = getTimeNow()

        return updateDict

    def makeDataDict(self, tableDef, dataObj):
        """
        Make a dictionary to hold update status using table columns as keys

        Return: a dictionary of update values

        """

        attribDict = tableDef["ATTRIBUTES"]
        dataDict = {}
        objType = str(type(dataObj))

        if objType.find("dict") > 0:
            for k, v in dataObj.items():
                if k in attribDict.keys():
                    dataDict[k] = v
        else:
            self.__lfh.write("WfDbApi::makeDataDict(): Failing, input data object is not a dictionary.\n")

        return dataDict

    def getAll(self, depId=None, classId=None, instId=None):
        """
        Get info from WF table deposition, wf_class_dict, wf_instance.

        Return a list of rows (python dictionaries)
        The Keys in the result dictionary is defined in
        WfSchemaMap._selectColumns, could be in the following:
            deposition.dep_set_id
            deposition.pdb_id
            deposition.status_code
            deposition.author_release_status_code
            deposition.exp_method
            deposition.annotator_initials
            wf_class_dict.wf_class_id
            wf_class_dict.wf_class_name
            wf_class_dict.version
            wf_instance.wf_inst_id
            wf_instance.owner
            wf_instance.inst_status
            wf_instance.status_timestamp
            wf_task.wf_task_id
            wf_task.task_name
            wf_task.task_status
            wf_task.status_timestamp
        """

        #
        #   Assumption is that you can't choose classId or instId without
        #   depId. Also any instId must have depId and classId.

        constraintDef = {}

        depId = self.checkId(depId)
        classId = self.checkId(classId)
        instId = self.checkId(instId)

        if depId is None and (classId is not None or instId is not None):
            self.__lfh.write("+WfDbApi::getAll(): Failing, no deposition id provided\n")
            exit(1)
        if depId is not None and classId is None and instId is not None:
            self.__lfh.write("+WfDbApi::getAll(): Failing, no class id provided\n")
            exit(1)

        if depId is not None:
            constraintDef[self.__idList[0]] = depId
        if classId is not None:
            constraintDef[self.__idList[1]] = classId
        if instId is not None:
            constraintDef[self.__idList[2]] = instId

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            results = self.__db.selectCrossTables(self.__selectList[2], self.__sqlJoinStr, self.__orderBy[2], self.__constraintList, constraintDef)

            if results is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                    # next loop
                else:
                    # unhandled DB error
                    return None
            else:
                return results

        # all gone bad
        return None

    def doQuery(self, level, parameterDict, orderList=None, otherOpt=None):
        """
        Function for determining which table to query based on level.

        Level 1 id for summary information; level 2 is for instance/task
        information.

        parameterDict{} holds parameters that user select from the front end.
        The keys should match the keys in WfSchemaMap._constraintList.

        orderList should also match the keys _schemaMap._orderBy
        or WfSchemaMap._constraintList{} for level 2

        otherOpt could be one of ['AUTHOR_CORRECTIONS','DEP_WITH_PROBLEMS',
        'RELEASE_REQUEST'].

        Return a list of rows (dictionaries)
        The Keys in the result dictionary could be in the following:
        Level 1:
           DEP_SET_ID
           EXP_METHOD
           PDB_ID
           STATUS_CODE
           AUTHOR_RELEASE_STATUS_CODE
           INITIAL_DEPOSITION_DATE
           STATUS_CODE_EXP
           ANNOTATOR_INITIALS
           AUTHOR_LIST
           SG_CENTER
           ASSESSION_CODE
           RELATIONSHIP
           ASSOCIATED_IDS
           CORRECTIONS ( for Author's Corrections)
           REQ_CITATION ( for entries requested for release)
           PROBLEM_TYPE ( for Problem/Error entries)
           PROBLEM_DETAILS ( for Problem/Error entries)
        Level 2:
           deposition.dep_set_id
           deposition.pdb_id
           deposition.status_code
           deposition.author_release_status_code
           deposition.exp_method
           deposition.annotator_initials
           wf_class_dict.wf_class_id
           wf_class_dict.wf_class_name
           wf_class_dict.version
           wf_instance.wf_inst_id
           wf_instance.owner
           wf_instance.inst_status
           wf_instance.status_timestamp
           wf_task.wf_task_id
           wf_task.task_name
           wf_task.task_status
           wf_task.status_timestamp
        """
        if orderList is None:
            orderList = []

        tableDef = ""
        rList = []
        if level == 2:
            # Multiple tables selected
            # The selectList and query are fixed
            if otherOpt is not None:
                self.__lfh.write("+WfDbApi::doQuery(): Failing, otherOpt is only for level 1\n")
                exit(1)
            for k, _v in parameterDict.items():
                if k not in self.__constraintList.keys():
                    self.__lfh.write("+WfDbApi::doQuery(): Failing, no matched columns in the database for %s\n" % k)
                    exit(1)
            if len(orderList) > 0:
                for k in orderList:
                    if k not in self.__constraintList.keys():
                        self.__lfh.write("+WfDbApi::doQuery(): Failing, no matched columns in the database for %s\n" % k)
                        exit(1)
                orderBy = self.__db.makeOrderStr(orderList)
            else:
                # use default
                orderBy = self.__orderBy[2]

            # self.testConnection()
            ok = False
            for retry in range(1, self.__Nretry):

                rList = self.__db.selectCrossTables(self.__selectList[2], self.__sqlJoinStr, orderBy, self.__constraintList, parameterDict)

                if rList is None:
                    # database error -
                    if self.__db.dbState > 0:
                        # 2006 : database went away
                        time.sleep(retry * 2)  # backoff for increasing waits
                        if not self.reConnect():
                            return None
                        # loop
                    else:
                        # unhandled DB error
                        return None
                else:
                    ok = True
                    break

            # all gone bad
            if not ok:
                return None
        else:
            # level 1, query single tables,
            # first get data from the table "DEPOSITION"
            tableDef = self.__schemaWf[self.__tableList[0]]
            for k in parameterDict.keys():
                if k not in tableDef["ATTRIBUTES"]:
                    self.__lfh.write("+WfDbApi::doQuery(): Failing, no matched columns in the database for %s\n" % (k))
                    exit(1)
            if otherOpt is None:
                if otherOpt in (self.__tableList[9], self.__tableList[10], self.__tableList[11]):
                    sqlStr = self.__idList[0] + " in (select " + self.__idList[0] + " from " + self.__schemaWf[otherOpt]["TABLE_NAME"] + ")"
                    parameterDict["EXTERNAL_TABLE"] = sqlStr
                    #  EXTERNAL_TABLE is for special SQL syntext
                else:
                    self.__lfh.write(
                        "+WfDbApi::doQuery(): Failing, otherOpt should be in the list [%s,%s,%s]\n" % (self.__tableList[9], self.__tableList[10], self.__tableList[11])
                    )
                    exit(1)

            orderList = self.__orderBy[3]
            # self.testConnection()

            ok = False
            for retry in range(1, self.__Nretry):

                results = self.__db.selectRows(tableDef, parameterDict, orderList, self.__selectList[1])

                if results is None:
                    # database error -
                    if self.__db.dbState > 0:
                        # 2006 : database went away
                        time.sleep(retry * 2)  # backoff for increasing waits
                        if not self.reConnect():
                            return None
                    else:
                        # unhandled DB error
                        return None
                else:
                    ok = True
                    break

            # all gone bad
            if not ok:
                return None

            # convert dict to list if there is only one record.
            if str(type(results)).find("dict") > 0:
                rList.append(results)
            else:
                rList = results

            # get info other then the main table

            for k in rList:
                Relations = ""
                associatedIds = ""
                constDict = {}
                DepId = k[self.__selectList[1][0]]
                DepId = self.checkId(DepId)
                if DepId is not None:
                    constDict[self.__idList[0]] = DepId
                    # get 'ASSESSION_CODE' from the table "DATABASE_REF"
                    accessionIds = self.getValueString(self.__schemaWf[self.__tableList[7]], constDict, self.__columnList[3])
                    if accessionIds is not None and accessionIds != "":
                        # fill in 'ASSESSION_CODE' in the result
                        k[self.__columnList[11]] = accessionIds

                    # get 'REPLACE_PDB_ID' from table "DATABASE_PDB_OBS_SPR"
                    obsIds = self.getValueString(self.__schemaWf[self.__tableList[6]], constDict, self.__columnList[4])
                    if obsIds is not None and obsIds != "":
                        Relations += "SPR/OBS"
                        associatedIds += obsIds

                    # get related 'DB_ID' from table "DATABASE_RELATED"
                    # only "SPLIT" is interested
                    constDict[self.__columnList[6]] = "SPLIT"
                    relatedIds = self.getValueString(self.__schemaWf[self.__tableList[8]], constDict, self.__columnList[7])

                    if relatedIds is not None and relatedIds != "":
                        if Relations != "":
                            Relations += ", SPLIT"
                            associatedIds += ", " + relatedIds
                        else:
                            Relations += "SPLIT"
                            associatedIds += relatedIds

                    if Relations is not None and Relations != "":
                        # fill in RELATIONSHIP and ASSOCIATED_IDS in the result
                        k[self.__columnList[9]] = Relations
                        k[self.__columnList[10]] = associatedIds

                    if otherOpt is not None:
                        constDict = {}
                        constDict[self.__idList[0]] = DepId
                        selectItem = ""
                        if otherOpt == self.__tableList[9]:
                            # AUTHOR_CORRECTIONS.CORRECTIONS
                            selectItem = self.__columnList[12]
                        if otherOpt == self.__tableList[10]:
                            # RELEASE_REQUEST.CITATION
                            selectItem = self.__columnList[13]
                        if otherOpt == self.__tableList[11]:
                            # DEP_WITH_PROBLEMS.PROBLEM_TYPE
                            selectItem = self.__columnList[14]

                        resultString = self.getValueString(self.__schemaWf[otherOpt], constDict, selectItem)
                        if resultString is not None and resultString != "":
                            # fill selectItem in the result
                            k[selectItem] = resultString

                        if otherOpt == self.__tableList[11]:
                            # one more items: DEP_WITH_PROBLEMS.PROBLEM_DETAILS
                            selectItem = self.__columnList[15]
                            resultString = self.getValueString(self.__schemaWf[otherOpt], constDict, selectItem)
                            if resultString is not None and resultString != "":
                                k[selectItem] = resultString

        return rList

    def getValueString(self, tableDef, constDict, selectItem):
        """
        Query a single table for a giving DEP_SET_ID
        selectItem is the selected column for query

        return a string (if there are multiple results
        the string is concatenated by ", "
        """

        returnString = ""

        # define the check list 'DATABASE_CODE','REPLACE_PDB_ID','DB_ID'
        # 'CORRECTIONS','REQ_CITATION','PROBLEM_TYPE','PROBLEM_DETAILS',
        # 'PUBMED_ID'
        checkList = [
            self.__columnList[3],
            self.__columnList[4],
            self.__columnList[7],
            self.__columnList[12],
            self.__columnList[13],
            self.__columnList[14],
            self.__columnList[15],
            self.__columnList[16],
        ]
        selectList = []
        if selectItem is not None and selectItem in checkList:
            selectList.append(selectItem)
        else:
            # print "WfDbApi::getValueString(): Warning -- There is not selectItem"
            pass

        # self.testConnection()
        ok = False
        for retry in range(1, self.__Nretry):

            results = self.__db.selectRows(tableDef, constDict, [], selectList)

            if results is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                else:
                    # unhandles DB error
                    return None
            else:
                ok = True
                break

        if not ok:
            return None

        if str(type(results)).find("dict") > 0:
            for checkItem in checkList:
                if checkItem in results.keys():
                    returnString = results[checkItem]
        else:
            for k in results:
                for checkItem in checkList:
                    if checkItem in k.keys():
                        if returnString == "":
                            returnString = k[checkItem]
                        else:
                            returnString += ", " + k[checkItem]

        return returnString

    def getNextWfInstId(self, depId, classId):
        """
        get a WF instance ID in highest number

        return a integer (instId+1)
        """

        rDict = {}
        returnId = 0
        rDict = self.getLastObjectOfState(None, depId, classId)
        if len(rDict) == 0:
            # no instance
            return 1
        else:
            returnId = rDict[self.__idList[2]]
            return int("%s" % returnId[2:]) + 1

    def referenceExist(self, depId=None, classId=None, instId=None, taskId=None, hashId=None, hashVal=None):
        """
        Check to see if the reference data still exists

        """

        tableDef = self.__schemaWf[self.__tableList[4]]
        constraintDict = {}
        selectList = {}
        orderList = {}
        depId = self.checkId(depId)
        classId = self.checkId(classId)
        instId = self.checkId(instId)
        taskId = self.checkId(taskId)

        if depId is not None:
            constraintDict[self.__idList[0]] = depId
        else:
            constraintDict[self.__idList[0]] = "None"
        if classId is not None:
            constraintDict[self.__idList[1]] = classId
        else:
            constraintDict[self.__idList[1]] = "None"
        if instId is not None:
            constraintDict[self.__idList[2]] = instId
        else:
            constraintDict[self.__idList[2]] = "None"
        if taskId is not None:
            constraintDict[self.__idList[3]] = taskId
        else:
            constraintDict[self.__idList[3]] = "None"

        if hashId is not None and self.__refList[0] in tableDef["ATTRIBUTES"].keys():
            constraintDict[self.__refList[0]] = hashId
        if hashVal is not None and self.__refList[1] in tableDef["ATTRIBUTES"].keys():
            selectList[self.__refList[1]] = hashVal

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            results = self.__db.selectRows(tableDef, constraintDict, orderList, selectList)

            if results is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                else:
                    # unhandle DB error
                    return None
            else:
                if len(results) > 0:
                    return True
                else:
                    return False

        # all gone bad
        return None

    def addReferenceOverwrite(self, depId=None, classId=None, instId=None, taskId=None, hashId=None, hashVal=None):
        """
        This method will insert if the data is new, or update if the data exists

        Add or update reference record in the table wf_reference
        requirement:
        For a deposition level reference,the classId, instId and taskId should be None
        For a class level reference the instId, taskId should be None
        For a instance level reference taskId should be None
        For a task level reference all ids should be Non-null.
        """

        refExist = self.referenceExist(depId, classId, instId, taskId, hashId, hashVal)

        if refExist:
            self.addReference("update", depId, classId, instId, taskId, hashId, hashVal)
        else:
            self.addReference("insert", depId, classId, instId, taskId, hashId, hashVal)

    def getLastObjectOfState(self, state, depId, classId, instId=None):
        """
        Get the last instance or task by the depId,,classId and instId
        the table is depended on giving depId,classId,instId

        If instId=None get the last instance from wf_instance;
        if instId != None table is wf_task

        State could be any status in wf_instance or wf_task or None
        Return a dictionary of table content

        """

        tableDef = {}
        rDict = {}
        constraintDict = {}
        orderList = []
        depId = self.checkId(depId)
        if depId is None:
            self.__lfh.write("+WfDbApi::getLastObjectOfState(): WARNING -- No depId provided\n")
            sys.exit(1)

        classId = self.checkId(classId)
        if classId is None:
            self.__lfh.write("+WfDbApi::getLastObjectOfState(): WARNING -- No classId provided\n")
            sys.exit(1)

        if instId is not None:
            instId = self.checkId(instId)

        if depId is not None and classId is not None and instId is not None:
            # table wf_task
            tableDef = self.__schemaWf[self.__tableList[3]]

        elif depId is not None and classId is not None and instId is None:
            # table wf_instance
            tableDef = self.__schemaWf[self.__tableList[2]]
        else:
            self.__lfh.write("+WfDbApi::getLastObjectOfState(): WARNING -- Can not decide the table name\n")
            return rDict

        if depId is not None:
            constraintDict[self.__idList[0]] = depId
        if classId is not None:
            constraintDict[self.__idList[1]] = classId
        if instId is not None:
            constraintDict[self.__idList[2]] = instId
        if state is not None:
            if tableDef == self.__schemaWf[self.__tableList[3]]:
                # wf_task
                constraintDict[self.__statusList[2]] = state

            elif tableDef == self.__schemaWf[self.__tableList[2]]:
                # wf_instance
                constraintDict[self.__statusList[1]] = state
            else:
                self.__lfh.write("+WfDbApi::getLastObjectOfState(): WARNING -- Can not decide the column name about state\n")
                return rDict

        orderList.append("ordinal desc")

        # self.testConnection()
        for retry in range(1, self.__Nretry):

            rDict = self.__db.selectRows(tableDef, constraintDict, orderList)

            if rDict is None:
                # database error -
                if self.__db.dbState > 0:
                    # 2006 : database went away
                    time.sleep(retry * 2)  # backoff for increasing waits
                    if not self.reConnect():
                        return None
                else:
                    # unhandled DB error
                    return None
            else:
                if str(type(rDict)).find("list") > 0:
                    return rDict[0]
                else:
                    return rDict

        # all gone bad
        return None


if __name__ == "__main__":
    pass

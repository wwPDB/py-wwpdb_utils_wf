##
# File:  dbApi.py
# Date:  14-Feb-2015
#
# #

import sys
import logging

from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi

logger = logging.getLogger(__name__)
"""

Grab bag of methods to execute SQL commands on various WF status tables -

"""


class dbAPI(object):
    def __init__(self, depID, connection=None, verbose=True):

        if connection:
            self.con = connection
        else:
            self.con = WfDbApi(verbose=False)
        self.depID = depID
        self.verbose = verbose

    def close(self):

        self.con.close()

    def runSelectNQ(self, table=None, join=None, select=None, where=None, order=None, reverse=False, ordinal=0, run=True, limit=0):

        if where:
            for k, v in where.items():
                where[k] = "'" + v + "'"
        return self.runSelect(table=table, join=join, select=select, where=where, order=order, reverse=reverse, ordinal=ordinal, run=run, limit=limit)

    def runSelect(self, table=None, join=None, select=None, where=None, order=None, reverse=False, ordinal=0, run=True, limit=0):
        """
        Very simple select SQL creator - single table
        table = string
        values = list
        where = dictionary of equivalence
        order = list

        Joins are specified with multiple table string , and where clause with inner join defined

        IMPT : all attribute values MUST BE QUOTED if strings

        Returns a list of list  (rows of data columns)
        Returns an empty list if nothing returned
        """

        if not table:
            logger.info("WFE.dbAPI.runSelect : Undefined table")
            return []

        if not select:
            logger.info("WFE.dbAPI.runSelect : Undefined select")
            return []

        depDB = {}
        depDB["DEP_SET_ID"] = self.depID

        try:
            if self.con.exist(depDB):
                #       if True:
                sql = "select " + ",".join(select) + " from " + str(table) + " "
                if where:
                    sql += " where " + " and ".join(["%s = %s" % (k, v) for k, v in where.items()])
                if join:
                    sql += " and " + join
                if ordinal > 0:
                    sql += " and ordinal >= " + str(ordinal)
                if order:
                    sql += " order by " + ",".join(order)
                    if reverse:
                        sql += " desc "
                if limit > 0:
                    sql += " limit " + str(limit)
                if self.verbose:
                    logger.info("WFE.dbAPI.runSelect > %s", str(sql))
                if run:
                    ret = self.con.runSelectSQL(sql)
                    return ret
                else:
                    return sql
            else:
                return []
        except Exception as e:
            logger.exception("WFE.dbAPI.runSelect :Exception %s", str(e))
            return []

    def runUpdateOnOrdinal(self, table=None, ordinal=None, data=None, run=True):
        """
        Very simple update/insert SQL creator base on ordinal
        table = string
        data = values to insert/update
        where clause is hard wired to ordinal (unique) so can only UPDATE
            a bad ordinal returns 0 rows updated

        return number of rows updated
        if run = False : returns the SQL

        IMPT : all attribute values MUST BE QUOTED if strings
        """

        if not table:
            logger.info("WFE.dbAPI.runUpdateOnOrdinal : Undefined table")
            return False

        if not ordinal:
            logger.info("WFE.dbAPI.runUpdateOnOrdinal : Undefined ordinal")
            return False

        try:
            sql = "update " + str(table) + " set " + ",".join(["%s = %s" % (k, v) for k, v in data.items()])
            sql = sql + " where ordinal = " + str(ordinal)
            if self.verbose:
                logger.info("WFE.dbAPI.runInsertUpdate(update) > %s", str(sql))

            if run:
                ok = self.con.runUpdateSQL(sql)
                if not ok:
                    logger.info("WFE.dbAPI.runSelect :False to update/insert data %s", str(sql))
                return ok
            else:
                return sql
        except Exception as e:
            logger.info("WFE.dbAPI.runSelect :Exception %s", str(e))
            return False

    def runInsertUpdateNQ(self, table=None, depID=None, where=None, data=None, run=True):
        """
        wrapper to add quotes to values
        """

        if where:
            for k, v in where.items():
                where[k] = "'" + v + "'"
        if data:
            for k, v in data.items():
                data[k] = "'" + v + "'"
        return self.runInsertUpdate(table, depID, where, data, run)

    def runInsertNQ(self, table=None, depID=None, where=None, data=None, run=True):

        if where:
            for k, v in where.items():
                where[k] = "'" + v + "'"
        if data:
            for k, v in data.items():
                data[k] = "'" + v + "'"
        return self.runInsert(table, depID, where, data, run)

    def runInsert(self, table=None, depID=None, where=None, data=None, run=True):

        try:
            if depID:
                sql = "insert into " + str(table) + " (dep_set_id," + ",".join(["%s" % (k) for k, v in data.items()])
                sql += ") values ('" + str(depID) + "'," + ",".join(["%s" % (v) for k, v in data.items()]) + ")"

            if where:
                sql = "insert into " + str(table) + " (" + ",".join(["%s" % (k) for k, v in where.items()])
                if data:
                    sql += "," + ",".join(["%s" % (k) for k, v in data.items()])
                sql += ") values (" + ",".join(["%s" % (v) for k, v in where.items()])
                if data:
                    sql += "," + ",".join(["%s" % (v) for k, v in data.items()])
                sql += ")"

            if self.verbose:
                logger.info("WFE.dbAPI.runInsertUpdate(insert) > %s", str(sql))

            if run:
                return self.con.runInsertSQL(sql)
            else:
                return sql
        except Exception as e:
            logger.exception("WFE.dbAPI.runInsert :Exception %s", str(e))
            return False

    def runUpdate(self, table=None, depID=None, where=None, data=None, run=True):
        logger.debug("Beginning run update")
        try:
            sql = "update " + str(table) + " set " + ",".join(["%s = %s" % (k, v) for k, v in data.items()])
            if depID:
                sql += " where dep_set_id = '" + str(depID) + "'"
            if where:
                sql += " where " + " and ".join(["%s = %s" % (k, v) for k, v in where.items()])

            if self.verbose:
                logger.info("WFE.dbAPI.runInsertUpdate(update) > %s", str(sql))

            if run:
                return self.con.runUpdateSQL(sql)
            else:
                return sql

        except Exception as e:
            logger.exception("WFE.dbAPI.runUpdate :Exception %s", str(e))
            return False

    def runInsertUpdate(self, table=None, depID=None, where=None, data=None, run=True):
        """
        Very simple update/insert SQL creator
        table = string
        data = values to insert/update
        where clause is hard wired to dep_set_id so can ONLY be used for
            tables with unique rows on dep_set_id
            i.e. if the table contains a row with dep_set_id - then it is update
                 if not - the data is inserted

        return number of rows updated
        if run = False : returns the SQL

        if depID is not none - then we test the existence based on depID and the table MUST BE UNIQUE on depID
          data is added to the row based on the dep_set_id + data
        if unique is not none - then we test the existence on the synthetic key based on the unique dictionary
          data is added to the row based on the where + data


        IMPT : all attribute values MUST BE QUOTED if strings
        """

        if not table:
            logger.info("WFE.dbAPI.runUpdateOnOrdinal : Undefined table")
            return False

        rowExists = False
        if depID:
            # then data is unique on depID
            depDB = {}
            depDB["DEP_SET_ID"] = depID
            if self.con.exist(depDB):
                rowExists = True

        else:
            if where:
                sql = "select ordinal from " + str(table) + " where " + " and ".join(["%s = %s" % (k, v) for k, v in where.items()])
                rows = self.con.runSelectSQL(sql)
                if rows and len(rows) > 0:
                    rowExists = True
            else:
                logger.info("WFE.dbAPI.runUpdate: Undefined key ")

        ok = True
        try:
            if rowExists:
                ok = self.runUpdate(table, depID, where, data, run)

            else:
                ok = self.runInsert(table, depID, where, data, run)

            if not run:
                return ok

            if not ok:
                logger.info("WFE.dbAPI.runSelect :False to update/insert data ")
                return ok
            else:
                return ok
        except Exception as e:
            logger.exception("WFE.dbAPI.runSelect :Exception %s", str(e))
            return False


def main(_argv):

    print("starting DBAPI test")

    depid = "D_1100201819"
    ss = dbAPI(depid, verbose=True)

    # table join test - notice that in the where clause be careful with the key must not repeat - so be carful with the inner join
    ret = ss.runSelect(
        table="deposition,wf_instance",
        select=["deposition.dep_set_id", "wf_instance.wf_inst_id"],
        where={"deposition.dep_set_id": "wf_instance.dep_set_id", "wf_instance.dep_set_id": "'" + depid + "'", "wf_instance.wf_inst_id": "'W_001'"},
        run=True,
    )
    print(str(ret))

    ret = ss.runSelectNQ(table="deposition", select=["ordinal", "dep_set_id", "depPW", "annotator_initials"], where={"dep_set_id": depid})
    print(str(ret))

    # test the orinal updates
    ret = ss.runSelectNQ(table="deposition", select=["ordinal", "dep_set_id", "depPW"], where={"dep_set_id": depid})
    print(str(ret))
    #   ret = ss.runUpdateOnOrdinal(table='deposition',ordinal='17823',data={"depPW":"'abcdef'"},run=True)
    #   print str(ret)
    ret = ss.runSelectNQ(table="deposition", select=["ordinal", "dep_set_id", "depPW"], where={"dep_set_id": depid})
    print(str(ret))
    #   ret = ss.runUpdateOnOrdinal(table='deposition',ordinal='17823',data={"depPW":"'123456'"},run=True)
    print(str(ret))
    ret = ss.runSelectNQ(table="deposition", select=["ordinal", "dep_set_id", "depPW"], where={"dep_set_id": depid})
    print(str(ret))

    ret = ss.runSelectNQ(
        table="deposition,user_data", select=["last_name", "role", "user_data.country"], join="deposition.dep_set_id=user_data.dep_set_id", where={"deposition.dep_set_id": depid}
    )

    # test the dep_set_id updates
    #   ret = ss.runInsertUpdate(table='deposition',depID='D_1000200025',data={"depPW":"'abcdef'"},run=True)
    print(str(ret))
    ret = ss.runSelect(table="deposition", select=["dep_set_id", "depPW"], where={"dep_set_id": "'" + depid + "'"})
    print(str(ret))
    #   ret = ss.runInsertUpdate(table='deposition',depID='D_1000200025',data={"depPW":"'123456'"},run=True)
    print(str(ret))
    ret = ss.runSelect(table="deposition", select=["dep_set_id", "depPW"], where={"dep_set_id": "'" + depid + "'"})
    print(str(ret))

    print("finished")


if __name__ == "__main__":
    main(sys.argv[1:])

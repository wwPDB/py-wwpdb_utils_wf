"""

    File:    LocalDbApi.py

    Providing addintaional APIs for WFE to get info from local database
 
   __author__    = "Li Chen"
   __email__     = "lchen@rcsb.rutgers.edu"
   __version__   = "V0.01"
   __Date__      = "Jun 4, 2010"

     
"""

import os,sys
import MySQLdb
#
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection    
from wwpdb.utils.wf.schema.WfSchemaMap  import WfSchemaMap
from wwpdb.utils.config.ConfigInfo import ConfigInfo

class LocalDbApi(object):
    """
    """
    def __init__(self, log=sys.stderr, verbose=False):
        """
           connect to local database
        """
        self.__lfh = log
        self.__verbose = verbose
        self.__dbServer  = "mysql"
        self.__dbHost    = "pdb-a-linux-5.rutgers.edu"
        self.__dbName    = "msd1"
        self.__dbUser    = "rcsbuser"
        self.__dbPw      = "rcsb0000"
        self.__dbPort    = 3306
        
        self.__myDb  = DbConnection(dbServer=self.__dbServer,dbHost=\
                                    self.__dbHost,dbName=self.__dbName,\
                                    dbUser=self.__dbUser,dbPw=self.__dbPw,\
                                    dbPort=self.__dbPort)
        
        self.__dbcon = self.__myDb.connect()          
        
    
    def getNewDepositedIds(self, interval):
        """
           Get newly deposited ids for RCSB site

           "interval" is a number of days from current time when the python
           code is run.
           
        """
        query = "select lcase(structure_id) from rcsb_status where initial_deposition_date>=DATE_SUB(curdate(), interval %s" % interval +" day) order by structure_id"
        returnList = []
        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor()        
            curs.execute(query)
            while True:
                result = curs.fetchone()
                if (result is not None):
                    returnList.append(result[0])
                else:
                    break
        except MySQLdb.Error as e:
            self.__lfh.write("Database error %d: %s\n" % (e.args[0], e.args[1]))
            curs.close()
            self.__dbcon.close()
            sys.exit (1)

        return returnList

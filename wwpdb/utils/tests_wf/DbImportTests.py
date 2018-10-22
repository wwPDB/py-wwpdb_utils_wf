##
# File: DbImportTests.py
# Date:  10-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for wwpdb.utils.wf - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection
from wwpdb.utils.wf.dbapi.DbCommand import DbCommand
from wwpdb.utils.wf.dbapi.WfTracking import WfTracking
from wwpdb.utils.wf.dbapi.WFEtime import *


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        #vT = WfDbApi()
        vC = DbConnection()
        vC = DbCommand(dbcon = None)
        vC = WfTracking()
        
if __name__ == '__main__':
    unittest.main()


    

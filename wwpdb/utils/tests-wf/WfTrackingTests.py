##
# File:    WfTrackingTests.py
# Date:    28-Apr-2010
#
# Updates:
##
"""
Test cases inserting tracking information in the workflow tracking database.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"


import sys, unittest, traceback
import time, os, os.path

from wwpdb.utils.wf.dbapi.WfTracking      import WfTracking
from wwpdb.utils.testing.Features import Features


@unittest.skipUnless(Features().haveMySqlTestServer(), "Needs MySql test server for testing")
class WfTrackingTests(unittest.TestCase):
    def setUp(self):
        self.__verbose=True
        self.__lfh=sys.stderr
        #
        # Create a session object and session directories for test cases
        #
        # Load up some test data - 
        #
        self.__depDataSetId='D_000001'
        self.__wfInstanceId='W_000001'
        self.__wfClassId   ='seqedTST'

    def tearDown(self):
        pass
    

    def testInstanceUpdateStart(self): 
        """ 
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wft=WfTracking(verbose=self.__verbose,log=self.__lfh)
            wft.setInstanceStatus(depId=self.__depDataSetId,
                                  instId=self.__wfInstanceId,
                                  classId=self.__wfClassId,
                                  status="open")
            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testInstanceUpdateFinish(self): 
        """ 
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wft=WfTracking(verbose=self.__verbose,log=self.__lfh)
            wft.setInstanceStatus(depId=self.__depDataSetId,
                                  instId=self.__wfInstanceId,
                                  classId=self.__wfClassId,
                                  status="closed(0)")
            
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()



def suite():
    return unittest.makeSuite(WfTrackingTests,'test')

if __name__ == '__main__':
    unittest.main()


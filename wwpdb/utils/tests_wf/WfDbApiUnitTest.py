"""

File:    WfDbApiUnitTest.py

     Some test cases ..
     An sample code to use python module unittest

     __author__    = "Li Chen"
     __email__     = "lchen@rcsb.rutgers.edu"
     __version__   = "V0.01"
     __Date__      = "April 21, 2010"

"""
import sys
import unittest
#
if __package__ is None or __package__ == '':
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, mockTopPath  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi
from wwpdb.utils.testing.Features import Features


@unittest.skipUnless(Features().haveMySqlTestServer(), "Needs MySql test server for testing")
class WfDbApiUnitTest(unittest.TestCase):

    def setUp(self):
        self.__verbose = True
        self.__lfh = sys.stderr

    def tearDown(self):
        pass

    def testCase1(self):
        c = WfDbApi(self.__lfh, self.__verbose)
        rd = c.getObject('DA099996')
        # test class object
        # rd = c.getObject(None,'seqedTST')
        for k, v in rd.items():
            self.__lfh.write("%s, %s\n" % (k, v))

        self.__lfh.write("### Test updating function\n")
        constDict = {}
        if c.exist(rd):
            rd['EXP_METHOD'] = 'NMR'
            constDict['DEP_SET_ID'] = 'DA099996'
            c.saveObject(rd, 'update', constDict)
            for k, v in rd.items():
                self.__lfh.write("%s, %s\n" % (k, v))
            self.__lfh.write("### Get status ---\n")
            s = c.getStatus(rd)
            if s == '':
                self.__lfh.write("No status\n")
            else:
                self.__lfh.write("%s\n" % s)

        self.__lfh.write("### Test insertion\n")

        self.__lfh.write("### Test updateStatus()\n")
        rd = c.getObject('DA099996')
        c.updateStatus(rd, 'HOLD')
        rd2 = c.getObject('D_057750')
        self.__lfh.write("Status is %s\n" % c.getStatus(rd2))

        self.__lfh.write("### test getReference()\n")

        #  deposition level
        rd = c.getReference('DA099996')
        self.__lfh.write("%s, %d\n" % (str(type(rd)), len(rd)))
        oType = str(type(rd))

        if oType.find('dict') > 0:
            if len(rd) > 0:
                self.__lfh.write("Key: %s, Value: %s\n" % (rd['HASH_ID'], rd['VALUE']))
            else:
                self.__lfh.write("No result\n")
        else:
            for k in range(len(rd)):
                self.__lfh.write("Key: %s, Value: %s\n" % (rd['HASH_ID'], rd['VALUE']))

        # self.__lfh.write("### test addReference()\n")
        # c.addReference('insert','DA099996','wfc_1',None,None,'depSelect','3')
        # c.addReference('update','DA099996','wfc_1','1',None,'instSelect','4')
        # rd = c.getReference('DA099996','wfc_1','1')
        # oType = str(type(rd))
        # self.__lfh.write("%s\n" % str(type(rd)))
        # if(oType.find('dict') > 0 ):
        #    if(len(rd)>0 ):
        #        self.__lfh.write("Key: %s, Value: %s\n" % (rd['HASH_ID'], rd['VALUE']))
        #    else:
        #       self.__lfh.write("No result\n")
        # else:
        #    for k in range (len(rd)):
        #        self.__lfh.write("Key: %s, Value: %s\n" % (rd['HASH_ID'], rd['VALUE']))
        # self.__lfh.write("\n")


if __name__ == '__main__':
    unittest.main()
    # # optional to use following code
    # suite = unittest.TestLoader().loadTestsFromTestCase(WfDbApiUnitTest)
    # unittest.TextTestRunner(verbosity=2).run(suite)

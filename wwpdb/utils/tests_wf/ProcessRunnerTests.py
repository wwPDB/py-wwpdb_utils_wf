##
# File:    ProcessRunnerTests.py
# Date:    6-April-2010
#
# Updates:
#
# 20-Apr-2010 jdw additional diff test cases added.
##
"""
Test cases for process manager class.  Simple file system tests are included in this module.

"""
import sys
import unittest
import traceback
import logging

if __package__ is None or __package__ == '':
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, mockTopPath  # pylint: disable=import-error
else:
    from .commonsetup import TESTOUTPUT, mockTopPath  # noqa: F401

from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner
from wwpdb.utils.wf.WfDataObject import WfDataObject
from wwpdb.utils.config.ConfigInfo import getSiteId

# Create logger
logger = logging.getLogger()
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class ProcessRunnerTests(unittest.TestCase):
    def setUp(self):
        self.__verbose = True
        self.__lfh = sys.stderr
        self.assertNotEqual(getSiteId(), 'None', "Site ID is not set")
        #
        # Load up some test data -
        #
        self.__depDataSetId = 'D_000001'
        self.__wfInstanceId = 'W_000002'

    def tearDown(self):
        pass

    def testCopyOp(self):
        """Test file copy from archival to workflow instance storage.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp = WfDataObject()
            wfoInp.setDepositionDataSetId(self.__depDataSetId)
            wfoInp.setStorageType('archive')
            wfoInp.setContentTypeAndFormat('model', 'pdbx')
            wfoInp.setVersionId('latest')
            dP = wfoInp.getDirPathReference()
            fP = wfoInp.getFilePathReference()
            vN = wfoInp.getFileVersionNumber()
            self.__lfh.write("Input directory path: %s\n" % dP)
            self.__lfh.write("Input file      path: %s\n" % fP)
            self.__lfh.write("Input file   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setDepositionDataSetId(self.__depDataSetId)
            wfoOut.setWorkflowInstanceId(self.__wfInstanceId)
            wfoOut.setStorageType('wf-instance')
            wfoOut.setContentTypeAndFormat('model', 'pdbx')
            wfoOut.setVersionId(vN)
            # wfoOut.setVersionId('latest')

            dP = wfoOut.getDirPathReference()
            fP = wfoOut.getFilePathReference()
            vN = wfoOut.getFileVersionNumber()
            self.__lfh.write("Output directory path: %s\n" % dP)
            self.__lfh.write("Output file      path: %s\n" % fP)
            self.__lfh.write("Output file   version: %d\n" % vN)

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src", wfoOut)
            op = 'mkdir'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src", wfoInp)
            pR.setOutput("dst", wfoOut)
            op = 'copy'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

        except Exception as _e:  # noqa: F84:
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testSizeOfOp(self):
        """Test obtaining the size of an archival data file.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp = WfDataObject()
            wfoInp.setDepositionDataSetId(self.__depDataSetId)
            wfoInp.setStorageType('archive')
            wfoInp.setContentTypeAndFormat('model', 'pdbx')
            wfoInp.setVersionId('original')
            dP = wfoInp.getDirPathReference()
            fP = wfoInp.getFilePathReference()
            vN = wfoInp.getFileVersionNumber()
            self.__lfh.write("Input directory path: %s\n" % dP)
            self.__lfh.write("Input file      path: %s\n" % fP)
            self.__lfh.write("Input file   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setContainerTypeName('value')
            wfoOut.setValueTypeName('integer')

            self.__lfh.write("Container type setting : %s\n" % wfoOut.getContainerTypeName())
            self.__lfh.write("Value type name setting : %s\n" % wfoOut.getValueTypeName())

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src", wfoInp)
            pR.setOutput("dst", wfoOut)
            op = 'sizeof'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            #
            nBytes = wfoOut.getValue()
            self.__lfh.write("File size: %d\n" % nBytes)
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testMtimeOfOp(self):
        """Test of obtaining the modification time of an archival data file.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp = WfDataObject()
            wfoInp.setDepositionDataSetId(self.__depDataSetId)
            wfoInp.setStorageType('archive')
            wfoInp.setContentTypeAndFormat('model', 'pdbx')
            wfoInp.setVersionId('latest')
            dP = wfoInp.getDirPathReference()
            fP = wfoInp.getFilePathReference()
            vN = wfoInp.getFileVersionNumber()
            self.__lfh.write("Input directory path: %s\n" % dP)
            self.__lfh.write("Input file      path: %s\n" % fP)
            self.__lfh.write("Input file   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setContainerTypeName('value')
            wfoOut.setValueTypeName('datetime')

            self.__lfh.write("Container type setting : %s\n" % wfoOut.getContainerTypeName())
            self.__lfh.write("Value type name setting : %s\n" % wfoOut.getValueTypeName())

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src", wfoInp)
            pR.setOutput("dst", wfoOut)
            op = 'mtime'

            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            dt = wfoOut.getValue()
            self.__lfh.write("Modification time: %r\n" % dt)
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testDiffOp(self):
        """Test of computing the contextual difference between the latest two versions of
           an archival file.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp1 = WfDataObject()
            wfoInp1.setDepositionDataSetId(self.__depDataSetId)
            wfoInp1.setStorageType('archive')
            wfoInp1.setContentTypeAndFormat('model', 'pdbx')
            wfoInp1.setVersionId('latest')

            dP = wfoInp1.getDirPathReference()
            fP = wfoInp1.getFilePathReference()
            vN = wfoInp1.getFileVersionNumber()

            self.__lfh.write(">Directory path: %s\n" % dP)
            self.__lfh.write(">File      path: %s\n" % fP)
            self.__lfh.write(">File   version: %d\n" % vN)

            wfoInp2 = WfDataObject()
            wfoInp2.setDepositionDataSetId(self.__depDataSetId)
            wfoInp2.setStorageType('archive')
            wfoInp2.setContentTypeAndFormat('model', 'pdbx')
            wfoInp2.setVersionId('previous')

            dP = wfoInp2.getDirPathReference()
            fP = wfoInp2.getFilePathReference()
            vN = wfoInp2.getFileVersionNumber()

            self.__lfh.write("<Directory path: %s\n" % dP)
            self.__lfh.write("<File      path: %s\n" % fP)
            self.__lfh.write("<File   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setContainerTypeName('list')
            wfoOut.setValueTypeName('string')

            self.__lfh.write("Container type setting : %s\n" % wfoOut.getContainerTypeName())
            self.__lfh.write("Value type name setting : %s\n" % wfoOut.getValueTypeName())

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src1", wfoInp1)
            pR.setInput("src2", wfoInp2)
            pR.setOutput("dst", wfoOut)
            op = 'diff'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            #
            oL = wfoOut.getValue()
            self.__lfh.write("Difference %s\n" % ''.join(oL))

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testDiffIntOp(self):
        """Test of computing the contextual difference between the latest two versions of
           an archival file.  Files identified by integer versions.
        """

        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp1 = WfDataObject()
            wfoInp1.setDepositionDataSetId(self.__depDataSetId)
            wfoInp1.setStorageType('archive')
            wfoInp1.setContentTypeAndFormat('model', 'pdbx')
            wfoInp1.setVersionId(2)

            dP = wfoInp1.getDirPathReference()
            fP = wfoInp1.getFilePathReference()
            vN = wfoInp1.getFileVersionNumber()

            self.__lfh.write(">Directory path: %s\n" % dP)
            self.__lfh.write(">File      path: %s\n" % fP)
            self.__lfh.write(">File   version: %d\n" % vN)

            wfoInp2 = WfDataObject()
            wfoInp2.setDepositionDataSetId(self.__depDataSetId)
            wfoInp2.setStorageType('archive')
            wfoInp2.setContentTypeAndFormat('model', 'pdbx')
            wfoInp2.setVersionId(3)

            dP = wfoInp2.getDirPathReference()
            fP = wfoInp2.getFilePathReference()
            vN = wfoInp2.getFileVersionNumber()

            self.__lfh.write("<Directory path: %s\n" % dP)
            self.__lfh.write("<File      path: %s\n" % fP)
            self.__lfh.write("<File   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setContainerTypeName('list')
            wfoOut.setValueTypeName('string')

            self.__lfh.write("Container type setting : %s\n" % wfoOut.getContainerTypeName())
            self.__lfh.write("Value type name setting : %s\n" % wfoOut.getValueTypeName())

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src1", wfoInp1)
            pR.setInput("src2", wfoInp2)
            pR.setOutput("dst", wfoOut)
            op = 'diff'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            #
            oL = wfoOut.getValue()
            self.__lfh.write("Difference %s\n" % ''.join(oL))

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testDiffStringOp(self):
        """Test of computing the contextual difference between the latest two versions of
           an archival file.  Files identified by stringified versions.
        """
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
        self.__lfh.write(" -------------------------\n")
        try:
            wfoInp1 = WfDataObject()
            wfoInp1.setDepositionDataSetId(self.__depDataSetId)
            wfoInp1.setStorageType('archive')
            wfoInp1.setContentTypeAndFormat('model', 'pdbx')
            wfoInp1.setVersionId('2')

            dP = wfoInp1.getDirPathReference()
            fP = wfoInp1.getFilePathReference()
            vN = wfoInp1.getFileVersionNumber()

            self.__lfh.write(">Directory path: %s\n" % dP)
            self.__lfh.write(">File      path: %s\n" % fP)
            self.__lfh.write(">File   version: %d\n" % vN)

            wfoInp2 = WfDataObject()
            wfoInp2.setDepositionDataSetId(self.__depDataSetId)
            wfoInp2.setStorageType('archive')
            wfoInp2.setContentTypeAndFormat('model', 'pdbx')
            wfoInp2.setVersionId('3')

            dP = wfoInp2.getDirPathReference()
            fP = wfoInp2.getFilePathReference()
            vN = wfoInp2.getFileVersionNumber()

            self.__lfh.write("<Directory path: %s\n" % dP)
            self.__lfh.write("<File      path: %s\n" % fP)
            self.__lfh.write("<File   version: %d\n" % vN)

            wfoOut = WfDataObject()
            wfoOut.setContainerTypeName('list')
            wfoOut.setValueTypeName('string')

            self.__lfh.write("Container type setting : %s\n" % wfoOut.getContainerTypeName())
            self.__lfh.write("Value type name setting : %s\n" % wfoOut.getValueTypeName())

            pR = ProcessRunner(verbose=self.__verbose, log=self.__lfh)
            pR.setInput("src1", wfoInp1)
            pR.setInput("src2", wfoInp2)
            pR.setOutput("dst", wfoOut)
            op = 'diff'
            #
            ok = pR.setAction(op)
            self.__lfh.write("setAction() for %s returns status %r\n" % (op, ok))
            ok = pR.preCheck()
            self.__lfh.write("preCheck() for %s returns status %r\n" % (op, ok))
            ok = pR.run()
            self.__lfh.write("run() for %s returns status %r\n" % (op, ok))

            #
            oL = wfoOut.getValue()
            self.__lfh.write("Difference %s\n" % ''.join(oL))

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suite():
    return unittest.makeSuite(ProcessRunnerTests, 'test')


if __name__ == '__main__':
    unittest.main()

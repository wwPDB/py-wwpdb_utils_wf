##
# File:    SeqStatsUtils.py
# Date:    29-April-2010
#
# Updates:
#
#   22-March-2013 jdw obsolete -
##
"""
Module of sequence processing utilities.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import  os,sys,traceback
import shutil,datetime,time,difflib
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase

from wwpdb.utils.config.ConfigInfo import ConfigInfo



class SeqStatsUtils(UtilsBase):
    """ Utility class to perform sequence processing operations.

        Current supported operations include:


        Each method in this class implements the method calling interface of the
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParameterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        Each method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """
    def __init__(self, verbose=True,log=sys.stderr):
        super(SeqStatsUtils,self).__init__(verbose,log)
        self.__cleanUp=True
        """Flag to remove any temporary directories created by this class.
        """
        #


    def prepareSequenceDataOp(self,**kwArgs):
        """Prepare sequence data for alignment and selection operations.

           Model file and seqdb-match data files must all be in the source directory.
           Latest versions of these files will be used.
        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)

            ## ------
            ##  This provide all information to define source data --
            #
            pdbxModelPath=inpObjD["src1"].getFilePathReference()
            wfInstanceId=inpObjD["src1"].getWorkflowInstanceId()
            depDataSetId=inpObjD["src1"].getDepositionDataSetId()
            fileSource=inpObjD["src1"].getStorageType()
            ##
            dstSeqFilePath =outObjD["dst"].getFilePathReference()
            dirPath        =outObjD["dst"].getDirPathReference()
            #
            if (self._verbose):
                self._lfh.write("+SeqStatsUtils.prepareSequenceDataOp()  This module is obsolete --- \n")
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False


    def evalSequenceDataOp(self,**kwArgs):
        """Assess sequence data and alignment against correspondence criteria.

           Returns:

           True for corresponding sequence data or False otherwise.

        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)

            ## ------
            ##  This provide all information to define source data --
            #
            seqDataPath =inpObjD["src"].getFilePathReference()
            wfInstanceId=inpObjD["src"].getWorkflowInstanceId()
            depDataSetId=inpObjD["src"].getDepositionDataSetId()
            fileSource  =inpObjD["src"].getStorageType()
            ##
            dirPath     =inpObjD["src"].getDirPathReference()

            testValue=False
            #
            if (self._verbose):
                self._lfh.write("+SeqStatsUtils() assesSequenceDataOp return : %r\n" % testValue)
            outObjD["dst"].setValue(testValue)

            return True
            #

        except:
            traceback.print_exc(file=self._lfh)
            return False


    def updateModelSequenceOp(self,**kwArgs):
        """Update the model sequence with alignment edits and selection data.

           Returns:

           True for success or False otherwise.

        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)

            ## ------
            ##  This provide all information to define source data --
            #
            inpModelFilePath=inpObjD["src1"].getFilePathReference()
            #wfInstanceId   =inpObjD["src1"].getWorkflowInstanceId()
            #depDataSetId   =inpObjD["src1"].getDepositionDataSetId()
            #fileSource     =inpObjD["src1"].getStorageType()
            #modelPath      =inpObjD["src1"].getDirPathReference()
            #
            ##
            seqDataFilePath  =inpObjD["src2"].getFilePathReference()
            seqDataPath      =inpObjD["src2"].getDirPathReference()

            #
            #
            outModelFilePath=outObjD["dst1"].getFilePathReference()
            wfInstanceId    =outObjD["dst1"].getWorkflowInstanceId()
            depDataSetId    =outObjD["dst1"].getDepositionDataSetId()
            fileSource      =outObjD["dst1"].getStorageType()
            outModelPath    =outObjD["dst1"].getDirPathReference()
            if (self._verbose):
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp instance    : %s\n" % outModelPath)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp instance id : %s\n" % wfInstanceId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp dep data id : %s\n" % depDataSetId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp fileSoure   : %s\n" % fileSource)


            outAssignFilePath=outObjD["dst2"].getFilePathReference()

            if (self._verbose):
                self._lfh.write("+SeqStatsUtils.updateModelSequenceOp()  This module is obsolete --- \n")
            return True
            #

        except:
            traceback.print_exc(file=self._lfh)
            return False


    def updateModelSequenceAssignOp(self,**kwArgs):
        """Update model coordinate file with aligmnent mapping information.

           Returns:

           True for success or False otherwise.

        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)

            ## ------
            ##  This provide all information to define source data --
            #
            inpModelFilePath=inpObjD["src1"].getFilePathReference()
            #wfInstanceId   =inpObjD["src1"].getWorkflowInstanceId()
            #depDataSetId   =inpObjD["src1"].getDepositionDataSetId()
            #fileSource     =inpObjD["src1"].getStorageType()
            inpModelPath      =inpObjD["src1"].getDirPathReference()
            #
            ##
            seqDataFilePath  =inpObjD["src2"].getFilePathReference()
            seqDataPath      =inpObjD["src2"].getDirPathReference()

            #
            #
            outModelFilePath=outObjD["dst1"].getFilePathReference()
            wfInstanceId    =outObjD["dst1"].getWorkflowInstanceId()
            depDataSetId    =outObjD["dst1"].getDepositionDataSetId()
            fileSource      =outObjD["dst1"].getStorageType()
            outModelPath    =outObjD["dst1"].getDirPathReference()
            if (self._verbose):
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp instance    : %s\n" % outModelPath)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp instance id : %s\n" % wfInstanceId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp dep data id : %s\n" % depDataSetId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp fileSoure   : %s\n" % fileSource)

            if (self._verbose):
                self._lfh.write("+SeqStatsUtils.updateModelSequenceAssignOp() This module is obsolete --- \n")

            return True
            #

        except:
            traceback.print_exc(file=self._lfh)
            return False


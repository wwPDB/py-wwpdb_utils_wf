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
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase


class SeqStatsUtils(UtilsBase):
    """Utility class to perform sequence processing operations.

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

    def __init__(self, verbose=True, log=sys.stderr):
        super(SeqStatsUtils, self).__init__(verbose, log)
        # Flag to remove any temporary directories created by this class.
        self.__cleanUp = True  # pylint: disable=unused-private-member
        #

    def prepareSequenceDataOp(self, **kwArgs):
        """Prepare sequence data for alignment and selection operations.

        Model file and seqdb-match data files must all be in the source directory.
        Latest versions of these files will be used.
        """
        try:
            (_inpObjD, _outObjD, _uD, _pD) = self._getArgs(kwArgs)

            # ------
            #  This provide all information to define source data --
            #
            if self._verbose:
                self._lfh.write("+SeqStatsUtils.prepareSequenceDataOp()  This module is obsolete --- \n")
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def evalSequenceDataOp(self, **kwArgs):
        """Assess sequence data and alignment against correspondence criteria.

        Returns:

        True for corresponding sequence data or False otherwise.

        """
        try:
            (_inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)

            # ------
            #  This provide all information to define source data --
            testValue = False
            #
            if self._verbose:
                self._lfh.write("+SeqStatsUtils() assesSequenceDataOp return : %r\n" % testValue)
            outObjD["dst"].setValue(testValue)

            return True
            #

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updateModelSequenceOp(self, **kwArgs):
        """Update the model sequence with alignment edits and selection data.

        Returns:

        True for success or False otherwise.

        """
        try:
            (_inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)

            # ------
            #  This provide all information to define source data --
            #
            #
            #
            wfInstanceId = outObjD["dst1"].getWorkflowInstanceId()
            depDataSetId = outObjD["dst1"].getDepositionDataSetId()
            fileSource = outObjD["dst1"].getStorageType()
            outModelPath = outObjD["dst1"].getDirPathReference()
            if self._verbose:
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp instance    : %s\n" % outModelPath)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp instance id : %s\n" % wfInstanceId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp dep data id : %s\n" % depDataSetId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceOp fileSoure   : %s\n" % fileSource)

            if self._verbose:
                self._lfh.write("+SeqStatsUtils.updateModelSequenceOp()  This module is obsolete --- \n")
            return True
            #

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updateModelSequenceAssignOp(self, **kwArgs):
        """Update model coordinate file with alignment mapping information.

        Returns:

        True for success or False otherwise.

        """
        try:
            (_inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)

            # ------
            #  This provide all information to define source data --
            #
            wfInstanceId = outObjD["dst1"].getWorkflowInstanceId()
            depDataSetId = outObjD["dst1"].getDepositionDataSetId()
            fileSource = outObjD["dst1"].getStorageType()
            outModelPath = outObjD["dst1"].getDirPathReference()
            if self._verbose:
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp instance    : %s\n" % outModelPath)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp instance id : %s\n" % wfInstanceId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp dep data id : %s\n" % depDataSetId)
                self._lfh.write("+SeqStatsUtils() updateModelSequenceAssignOp fileSoure   : %s\n" % fileSource)

            if self._verbose:
                self._lfh.write("+SeqStatsUtils.updateModelSequenceAssignOp() This module is obsolete --- \n")

            return True
            #

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

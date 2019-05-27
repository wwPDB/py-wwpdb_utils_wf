##
# File:    AnnotationUtils.py
# Date:    15-Aug-2012
#
# Updates:
#  16-Aug-2012 jdw add dictionary check report
#  17-Dec-2012 jdw add option to calculation derived categories after solvent adjustment.
#  26-Jun-2013 jdw add formatCheckPdbxOp() & formatCheckPdbOp()
#  10-Oct-2013 jdw add miscCheckPdbxOp()
#  15-Jan-2014 jdw add update the content type for assemlby model files
#  16-Mar-2014 jdw add specialPositionCheckOp()
#  11-Jun-2104 jdw ad mergeXyzOp()
#  11-Jun-2104 tjo modified the check for exit status for mergeXYZop - check last line
#  14-Sep-2014 jdw add user parameter "deposit" on mergeXyzOp()
#  14-May-2015 jdw add status load method
#  20-Jan-2017 ep  add assemblyUpdateDepInfoOp()
#  15-Feb-2017 ep  add combineCifFilesOp()
##
"""
Module of annotation utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.dp.PdbxMergeCategory import PdbxMergeCategory

class ReportUtils(UtilsBase):

    """ Utility class to perform annotation utility operations.

        Current supported operations include:

        - Merging of deposition ligand of interest information

        Each method in this class implements the method calling interface of the
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParameterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        Each method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """

    def __init__(self, verbose=False, log=sys.stderr):
        super(ReportUtils, self).__init__(verbose, log)
        self.__cleanUp = False
        """Flag to remove any temporary directories created by this class.
        """
        #

    def combineLigandInfoOp(self, **kwArgs):
        """Merges the first datablock from src1 and selected categories in 
           src2 and output to dst1. Will not overwrite if present
        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            srcPath = inpObjD["src1"].getFilePathReference()
            mrgPath = inpObjD["src2"].getFilePathReference()
            outPath = outObjD["dst"].getFilePathReference()

            if (self._verbose):
                self._lfh.write("+ReportUtils.combineLigandInfoOp() - src1 input  file paths:  %s\n" % srcPath)
                self._lfh.write("+ReportUtils.combineLigandInfoOp() - src2 input  file paths:  %s\n" % mrgPath)
                self._lfh.write("+ReportUtils.combineLigandInfoOp() - output path: %s\n" % outPath)

            pm = PdbxMergeCategory()
            # srcin, src2in, dstoit, mergelist replacelist
            ret = pm.merge(srcPath, mrgPath, outPath, ['pdbx_entry_details'], 
                           ['pdbx_binding_assay', 'pdbx_entity_instance_feature'])

            if (self._verbose):
                self._lfh.write("+ReportUtils.combineLigandInfoOp() - return: %s\n" % ret)

            return ret
        except:
            traceback.print_exc(file=self._lfh)
            return False


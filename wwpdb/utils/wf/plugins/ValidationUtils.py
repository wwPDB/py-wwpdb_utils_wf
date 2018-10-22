##
# File:    ValidationUtils.py
# Date:    4-Sep-2012
#
# Updates:
#  4-Sep-2012  jdw add validation report method
#  13-Dec-2012 jdw added method for version 2 of validation module
#  15-Jan-2014 jdw add annotation context user paramter to validation report
#  24-Jan-2014 jdw add addition report output options
#  21-Sep-2014 jdw update validationReportTestOp() for NMR
#  16-Jan-2015 jdw update validationReportTestOp() to test for experimental files -
#  22-Mar-2015 jdw add entry_id as parameter in validationReportAltOp
#  16-Sep-2015 jdw add validationReportAllOp
#
#  14-Jul-2016 jdw validationReportAllOp() is the only valid entry point here - all others are deprecated.
#  14-Jul-2016 jdw add 'validation_mode' input parameter -
#  18-Dec-2016 ep  remove unused validationReportAltOp and validationReportV2Op
##
"""
Module of annotation utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class ValidationUtils(UtilsBase):

    """ Utility class to run validation operations.

        Current supported operations include:

        - create PDF report and supporting XML data file

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
        super(ValidationUtils, self).__init__(verbose, log)
        self.__cleanUp = False
        """Flag to remove any temporary directories created by this class.
        """
    def validationReportAllOp(self, **kwArgs):
        """Create validation reports, supporting XML data, and image files for the input PDBx model file and
           the current implementation of all experimental methods  with optional input
           of experimental data files --

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            depDataSetId = inpObjD["src1"].getDepositionDataSetId()
            #
            if "src2" in inpObjD:
                sfPath = inpObjD["src2"].getFilePathReference()
            else:
                sfPath = None

            if "src3" in inpObjD:
                csPath = inpObjD["src3"].getFilePathReference()
            else:
                csPath = None

            if "src4" in inpObjD:
                volPath = inpObjD["src4"].getFilePathReference()
            else:
                volPath = None

            validationReportPath = outObjD["dst1"].getFilePathReference()
            xmlReportPath = outObjD["dst2"].getFilePathReference()

            validationFullReportPath = outObjD["dst3"].getFilePathReference()
            pngReportPath = outObjD["dst4"].getFilePathReference()
            svgReportPath = outObjD["dst5"].getFilePathReference()

            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = os.path.join(dirPath, "val-report-all.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            validationMode = str(uD['validation_mode'])
            if validationMode in ["annotate", "deposit", "server", "release", "legacy"]:
                dp.addInput(name="request_validation_mode", value=validationMode)

            #  add an control over the report context
            inAnnotation = str(uD['in_annotation'])
            if inAnnotation in ["yes", "no"]:
                dp.addInput(name="request_annotation_context", value=inAnnotation)
            #
            # add parameters only if these exist --
            #
            if depDataSetId is not None and len(depDataSetId) > 3:
                dp.addInput(name="entry_id", value=depDataSetId)

            if sfPath is not None and os.access(sfPath, os.R_OK):
                dp.addInput(name="sf_file_path", value=sfPath)
            else:
                sfPath = None
            #
            if csPath is not None and os.access(csPath, os.R_OK):
                dp.addInput(name="cs_file_path", value=csPath)
            else:
                csPath = None

            if volPath is not None and os.access(volPath, os.R_OK):
                dp.addInput(name="vol_file_path", value=volPath)
            else:
                volPath = None

            dp.op("annot-wwpdb-validate-all")
            dp.expLog(logPath)
            dp.expList(dstPathList=[validationReportPath, xmlReportPath, validationFullReportPath, pngReportPath, svgReportPath])

            if (self._verbose):
                self._lfh.write("+ValidationUtils.validationReportAllOp() - Entry Id:                %s\n" % depDataSetId)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - PDBx   file path:        %s\n" % pdbxPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - SF     file path:        %s\n" % sfPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - CS     file path:        %s\n" % csPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - Volume file path:        %s\n" % volPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - PDF report file path:  %s\n" % validationReportPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - XML report file path:  %s\n" % xmlReportPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - PNG slider file path:  %s\n" % pngReportPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - SVG slider file path:  %s\n" % svgReportPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - full PDF   file path:  %s\n" % validationFullReportPath)
                self._lfh.write("+ValidationUtils.validationReportAllOp() - validation mode:       %s\n" % validationMode)

            if (self.__cleanUp):
                dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False
        #

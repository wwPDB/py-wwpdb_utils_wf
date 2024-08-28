##
# File:    AnnotationUtils.py
# Date:    15-Aug-2012
#
# Updates:
#  16-Aug-2012 jdw add dictionary check report
#  17-Dec-2012 jdw add option to calculation derived categories after solvent adjustment.
#  26-Jun-2013 jdw add formatCheckPdbxOp() & formatCheckPdbOp()
#  10-Oct-2013 jdw add miscCheckPdbxOp()
#  15-Jan-2014 jdw add update the content type for assembly model files
#  16-Mar-2014 jdw add specialPositionCheckOp()
#  11-Jun-2104 jdw ad mergeXyzOp()
#  11-Jun-2104 tjo modified the check for exit status for mergeXYZop - check last line
#  14-Sep-2014 jdw add user parameter "deposit" on mergeXyzOp()
#  14-May-2015 jdw add status load method
#  20-Jan-2017 ep  add assemblyUpdateDepInfoOp()
#  15-Feb-2017 ep  add combineCifFilesOp()
#  26-Aug-2024 zf  add linkPtmOp()
##
"""
Module of annotation utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import logging
import os
import shutil
import socket
import sys
import tempfile
import traceback

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.dp.DensityWrapper import DensityWrapper
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase

try:
    # We will have present on annotation system - but allow testing without
    from wwpdb.apps.ann_tasks_v2.check.EmMapCheck import EmMapCheckTask
    from wwpdb.apps.ann_tasks_v2.io.PisaReader import PisaAssemblyReader
    from wwpdb.apps.ann_tasks_v2.em3d.EmAutoFix import EmAutoFix
    from wwpdb.apps.ann_tasks_v2.em3d.EmMapAutoFixVers import EmMapAutoFixVers
    from wwpdb.apps.ann_tasks_v2.em3d.EmHeaderUtils import EmHeaderUtils
    from wwpdb.apps.ann_tasks_v2.related.UpdateRelated import UpdateRelated
    from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpUpdate import PdbxExpUpdate
    from wwpdb.utils.session.WebRequest import InputRequest
    from wwpdb.io.locator.PathInfo import PathInfo
except ImportError:
    pass

from wwpdb.utils.db.DbLoadingApi import DbLoadingApi
from mmcif.io.IoAdapterCore import IoAdapterCore

logger = logging.getLogger(__name__)


class AnnotationUtils(UtilsBase):
    """Utility class to perform annotation utility operations.

    Current supported operations include:

    - Assembly calculations

    - Secondary structure
    - Site environment
    - Solvent reorganization
    - Nucleic acid geometric features
    - Chemical linkages and cis-peptide linkages
    - Automatic running of mapfix on archive files
    - Automatic lookup of pdbx_database_related

    -Various format, dictionary and geometry checks

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
        super(AnnotationUtils, self).__init__(verbose, log)
        self.__cleanUp = False
        """Flag to remove any temporary directories created by this class.
        """
        #

    def statusLoadOp(self, **kwArgs):
        """Performs PDBx database load of status related categories."""
        try:
            (inpObjD, _outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            dirPath = inpObjD["src"].getDirPathReference()
            #
            if self._verbose:
                self._lfh.write("+AnnotationUtils.statusLoadOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.statusLoadOp() - deposition ID:          %s\n" % depDataSetId)
            dbLd = DbLoadingApi(log=self._lfh, verbose=self._verbose)
            ok = dbLd.doLoadStatus(pdbxPath, dirPath)
            self._lfh.write("+AnnotationUtils.statusLoadOp() - returns   %r\n" % ok)
            return ok
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def specialPositionCheckOp(self, **kwArgs):
        """Performs special position check and produces a summary report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "special-position-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("annot-dcc-special-position")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.specialPositionCheckOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.specialPositionCheckOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def formatCheckPdbxOp(self, **kwArgs):
        """Performs PDBx format check and returns a text check report."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "format-check-pdbx.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            if "nmr_flag" in uD:
                isNmr = str(uD["nmr_flag"])
                if isNmr == "Y":
                    dp.addInput(name="nmr", value="Y")
            #
            dp.op("annot-format-check-pdbx")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.formatCheckPdbxOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.formatCheckPdbxOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def formatCheckPdbOp(self, **kwArgs):
        """Performs PDB format check and returns a text check report."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            pdbPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "format-check-pdb.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbPath)
            if "nmr_flag" in uD:
                isNmr = str(uD["nmr_flag"])
                if isNmr == "Y":
                    dp.addInput(name="nmr", value="Y")

            #
            dp.op("annot-format-check-pdb")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.formatCheckPdbOp() - PDB input  file path:  %s\n" % pdbPath)
                self._lfh.write("+AnnotationUtils.formatCheckPdbOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def dictCheckOp(self, **kwArgs):
        """Performs PDBx dictionary check on PDBx format input file and returns a text check report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "dict-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("check-cif")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.dictCheckOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.dictCheckOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def xmlCheckOp(self, **kwArgs):
        """ Performs PDBML XML check on PDBx format input file and returns a text check report.
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "cif2pdbx-next.log")
            expPath = os.path.join(dirPath, depDataSetId + "_model-temp_P1.cif.V1")
            if os.path.exists(expPath):
                os.remove(expPath)
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="destination", value="archive_next")
            dp.op("cif2pdbx-ext")

            dp.expLog(logPath)
            dp.exp(expPath)
            if self.__cleanUp:
                dp.cleanup()
            #
            if os.access(expPath, os.R_OK):
                xmlPath = self.__generateXMLFile(siteId, expPath, dirPath)
                os.remove(expPath)
                if xmlPath:
                    self.__checkXMLFile(siteId, xmlPath, dirPath, reportPath, "annot-check-xml-xmllint")
                    self.__checkXMLFile(siteId, xmlPath, dirPath, reportPath, "annot-check-xml-stdinparse")
                    if self._verbose:
                        self._lfh.write("+AnnotationUtils.dictCheckOp() - PDBx input  file path:  %s\n" % pdbxPath)
                        self._lfh.write("+AnnotationUtils.dictCheckOp() - Report file path:       %s\n" % reportPath)
                    #
                    os.remove(xmlPath)
                    return True
                #
            #
            return False
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False
        #

    def __generateXMLFile(self, siteId, pdbxPath, dirPath):
        """ Generate noatom xml file
        """
        try:
            xmlPath = pdbxPath + ".xml-noatom"
            outputList = []
            outputList.append(xmlPath)
            outputList.append(os.path.join(dirPath, "generate_xml_v5.log"))
            outputList.append(os.path.join(dirPath, "generate_xml_command_v5.log"))
            for filePath in outputList:
                if os.access(filePath, os.R_OK):
                    os.remove(filePath)
                #
            #
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-public-pdbx-to-xml-noatom")
            dp.expList(outputList)
            #
            if self.__cleanUp:
                dp.cleanup()
            #
            if os.access(xmlPath, os.R_OK):
                return xmlPath
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #
        return None

    def __checkXMLFile(self, siteId, xmlPath, dirPath, reportPath, op):
        """ Check noatom xml file
        """
        try:
            if op == "annot-check-xml-xmllint":
                statinfo = os.stat(xmlPath)
                if statinfo.st_size > 100000000:
                    return
                #
            #
            inReportPath = os.path.join(dirPath, "check-xml.diag.txt")
            if os.access(inReportPath, os.R_OK):
                os.remove(inReportPath)
            #
            outputList = []
            outputList.append(inReportPath)
            #
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(xmlPath)
            dp.op(op)
            dp.expList(outputList)
            #
            if os.access(inReportPath, os.R_OK):
                ith = open(inReportPath, "r")
                data = ith.read()
                ith.close()
                if len(data) > 0:
                    oth = open(reportPath, "a")
                    for line in data.split("\n"):
                        strip_line = line.strip()
                        if (strip_line == "") or (strip_line == "input_file_1 validates") or strip_line.startswith("stdin:"):
                            continue
                        elif strip_line.startswith("input_file_1:") or strip_line.startswith("input_file_1 "):
                            oth.write("%s\n" % strip_line[13:])
                        else:
                            oth.write("%s\n" % strip_line)
                        #
                    #
                    oth.close()
                #
                os.remove(inReportPath)
            #
            if self.__cleanUp:
                dp.cleanup()
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #

    def dictCheckFirstOp(self, **kwArgs):
        """Performs PDBx dictionary check on the first block of a PDBx format input file
        and returns a text check report.
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "dict-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)

            dp.addInput("first_block")

            #
            dp.op("check-cif")
            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.dictCheckFirstOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.dictCheckFirstOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def dictR4CheckOp(self, **kwArgs):
        """Performs PDBx R4 dictionary check on PDBx format input file and returns a text check report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "dict-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("check-cif-v4")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.dictR4CheckOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.dictR4CheckOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def geometryCheckOp(self, **kwArgs):
        """Performs geometry check on PDBx format input file and returns a text check report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "geometry-check-report.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("validate-geometry")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.geometryCheckOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.geometryCheckOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def miscCheckReportOp(self, **kwArgs):
        """Performs additional checks on PDBx format model files and returns a text check report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "misc-check-report.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("annot-extra-checks")

            dp.expLog(logPath)
            dp.exp(reportPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.miscCheckReportOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.miscCheckReportOp() - Report file path:       %s\n" % reportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def dccCheckReportOp(self, **kwArgs):
        """DCC generated check report of model and SF file --"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            sfPath = inpObjD["src2"].getFilePathReference()
            xyzPath = inpObjD["src1"].getFilePathReference()
            #
            #
            dirPath = outObjD["dst1"].getDirPathReference()
            reportFilePath = outObjD["dst1"].getFilePathReference()
            logFilePath = outObjD["dst2"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(xyzPath)
            if (sfPath is not None) and os.path.exists(sfPath):
                dp.addInput(name="sf_file_path", value=sfPath, type="file")

            dp.op("annot-dcc-report")
            dp.expLog(logFilePath)
            dp.exp(reportFilePath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.dccCheckReportOp() - SF  input  file path:          %s\n" % sfPath)
                self._lfh.write("+FormatUtils.dccCheckReportOp() - XYZ input  file path:          %s\n" % xyzPath)
                self._lfh.write("+FormatUtils.dccCheckReportOp() - LOG output file path:          %s\n" % logFilePath)
                self._lfh.write("+FormatUtils.dccCheckReportOp() - REPORT/PDBx output file path:  %s\n" % reportFilePath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def nucleicAcidGeometryOp(self, **kwArgs):
        """Performs base pair/step geometry calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "base-pair-position.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("annot-base-pair-info")

            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.nucleicAcidGeometryOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.nucleicAcidGeometryOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def solventPositionAddDerivedOp(self, **kwArgs):
        """Performs solvent reorganization calculation on PDBx format input file and update this data in the PDBx model file.

        This version also adds selected derived categories required by other annotation tasks.   This step should
        precede other added annotation tasks.

        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "solvent-position.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            # if (solventArgs is not None):
            #    dp.addInput(name="solvent_arguments",value=solventArgs)
            #
            dp.op("annot-reposition-solvent-add-derived")
            # dp.op("annot-distant-solvent")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.solventPositionOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.solventPositionOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def solventPositionOp(self, **kwArgs):
        """Performs solvent reorganization calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "solvent-position.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            # if (solventArgs is not None):
            #    dp.addInput(name="solvent_arguments",value=solventArgs)
            #
            dp.op("annot-reposition-solvent")
            # dp.op("annot-distant-solvent")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.solventPositionOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.solventPositionOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def solventPositionAnalysis(self, **kwArgs):
        """Performs distant solvent calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "solvent-position-analysis.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            # if (solventArgs is not None):
            #    dp.addInput(name="solvent_arguments",value=solventArgs)
            #
            dp.op("annot-distant-solvent")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.solventPositionAnalysis() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.solventPositionAnalysis() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def linkOp(self, **kwArgs):
        """Performs link calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "annot-link-and-ss-bond.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-link-ssbond")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.linkOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.linkOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def linkPtmOp(self, **kwArgs):
        """Performs link calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            csvOutputPath = outObjD["dst2"].getFilePathReference()
            logPath = os.path.join(dirPath, "annot-link-and-ss-bond.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-link-ssbond-with-ptm")
            dp.expLog(logPath)
            dp.expList(dstPathList=[pdbxOutputPath, csvOutputPath])
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.linkOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.linkOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def cisPeptideOp(self, **kwArgs):
        """Performs cis-peptide link perception on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-cis-peptide")
            # dp.expLog("annot-cis-peptide.log")
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.cisPeptideOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.cidPeptideOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updateGeometryValidationOp(self, **kwArgs):
        """Updates geometrical validation diagnostics in the PDBx model file -"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-validate-geometry")
            # dp.expLog("annot-validate-geometry.log")
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.updateGeometryValidationOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.updateGeometryValidationOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def getCorresInfoOp(self, **kwArgs):
        """gets correspondance information for the PDBx model file -"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-get-corres-info")
            # dp.expLog("annot-get-corres-info")
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.getCorresInfo() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.getCorresInfo() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def secondaryStructureOp(self, **kwArgs):
        """Performs secondary structure calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "annot-secondary-structure-w-top.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            # topPath=
            # dp.addInput(name="ss_topology_file_path",value=topPath)
            dp.op("annot-secondary-structure")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def secondaryStructureTopologyOp(self, **kwArgs):
        """Performs secondary structure calculation on PDBx format input file and update this data in the PDBx model file.

        This method includes the option for a supplementary topology file -

        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()

            topFilePath = inpObjD["src2"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "annot-secondary-structure-w-top.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="ss_topology_file_path", value=topFilePath)
            dp.op("annot-secondary-structure")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx input  file path:     %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - Topology input file path:  %s\n" % topFilePath)
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx output file path:     %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def consolidatedTasksOp(self, **kwArgs):
        """Performs most annotation tasks as a single step -

        This method includes the option for a supplementary topology file -

        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()

            topFilePath = inpObjD["src2"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "annot-consolidated-tasks-w-top.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="ss_topology_file_path", value=topFilePath)
            dp.op("annot-consolidated-tasks")
            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx input  file path:     %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - Topology input file path:  %s\n" % topFilePath)
                self._lfh.write("+AnnotationUtils.secondaryStructureOp() - PDBx output file path:     %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def siteEnvironmentOp(self, **kwArgs):
        """Performs site environment calculation on PDBx format input file and update this data in the PDBx model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "site-anal.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            # Step 1
            resultPath = os.path.join(dirPath, depDataSetId + "-site-anal.cif")
            dp.imp(pdbxPath)
            dp.addInput(name="block_id", value=depDataSetId)
            dp.op("annot-site")
            dp.expLog(logPath)
            dp.exp(resultPath)

            # Step 2
            dp.imp(pdbxPath)
            dp.addInput(name="site_info_file_path", value=resultPath, type="file")
            dp.op("annot-merge-struct-site")
            #
            # dp.expLog(logPath2)
            dp.exp(pdbxOutputPath)
            #
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.siteEnvironmentOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.siteEnvironmentOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
                self._lfh.write("+AnnotationUtils.siteEnvironmentOp() - Site anal file path:    %s\n" % resultPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def assemblyReportOp(self, **kwArgs):
        """Performs assembly prediction on PDBx format input files and produces an assembly report."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()

            assemblyReportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            pisaSession = "session_" + depDataSetId
            logPath1 = os.path.join(dirPath, "assembly-analysis.log")
            logPath2 = os.path.join(dirPath, "assembly-report.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="pisa_session_name", value=pisaSession)
            dp.op("pisa-analysis")
            dp.expLog(logPath1)
            dp.op("pisa-assembly-report-xml")
            dp.exp(assemblyReportPath)
            dp.expLog(logPath2)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.chemCompLinkOp() - PDBx file path:    %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.chemCompLinkOp() - Assembly report file path: %s\n" % assemblyReportPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def assemblyReportAndModelsOp(self, **kwArgs):
        """Performs assembly prediction on PDBx format input files and produces an assembly report.

        The list of file paths for the materialized model coordinates for each assembly is also returned.

        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            assemblyReportPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            pisaSession = "session_" + depDataSetId
            logPath1 = os.path.join(dirPath, "assembly-analysis.log")
            logPath2 = os.path.join(dirPath, "assembly-report.log")
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            if self._verbose:
                self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - PDBx file path:    %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - Assembly report file path: %s\n" % assemblyReportPath)
                self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - dirPath : %s\n" % dirPath)
                self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - siteId  : %s\n" % siteId)
                self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - logPath : %s\n" % logPath1)
            #
            maxAssems = 50

            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="pisa_session_name", value=pisaSession)
            dp.op("pisa-analysis")
            dp.expLog(logPath1)
            dp.op("pisa-assembly-report-xml")
            dp.exp(assemblyReportPath)
            dp.expLog(logPath2)

            #
            assemD = self.__readAssemblyReport(assemblyReportPath)
            pathList = []
            if len(assemD) > 0:
                if self._verbose:
                    self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - assembly uid list %r\n" % assemD.keys())
                #
                for assemblyUid in sorted(assemD.keys()):
                    if assemblyUid > maxAssems:
                        break
                    if assemblyUid == 0:
                        continue
                    assemModelFileName = os.path.join(dirPath, depDataSetId + "_assembly-model-xyz_P" + str(assemblyUid) + ".cif.V1")
                    dp.addInput(name="pisa_assembly_id", value=assemblyUid)
                    dp.op("pisa-assembly-coordinates-cif")
                    dp.exp(assemModelFileName)
                    if self._verbose:
                        self._lfh.write("+AnnotationUtils.assemblyReportAndModels() - creating assembly model %r file %s\n" % (assemblyUid, assemModelFileName))
                    pathList.append(assemModelFileName)

            outObjD["dst2"].setValue(pathList)
            if self.__cleanUp:
                dp.cleanup()
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    # def assemblyInstanceUpdateOp(self, **kwArgs):
    #     """Performs assembly assignment update operations on PDBx format model files.

    #        Requires: extra input files for assignment and user selection.
    #     """
    #     try:
    #         (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
    #         pdbxPath = inpObjD["src1"].getFilePathReference()
    #         #
    #         reportFilePath = inpObjD["src2"].getFilePathReference()
    #         selectFilePath = inpObjD["src3"].getFilePathReference()
    #         #
    #         outputModelPdbxPath = outObjD["dst"].getFilePathReference()
    #         dirPath = outObjD["dst"].getDirPathReference()
    #         logPath = os.path.join(dirPath, "assembly-update.log")
    #         #
    #         cI = ConfigInfo()
    #         siteId = cI.get("SITE_PREFIX")
    #         dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
    #         #
    #         dp.imp(pdbxPath)
    #         selectString = __readSelection(selectFilePath)
    #         iL = []
    #         sL = selectString.split(',')
    #         for s in sL:
    #             if s is not None and len(s) > 0:
    #                 iL.append("%d" % int(s))

    #         tupleList = ','.join(iL)
    #         dp.addInput(name="pisa_assembly_tuple_list", value=tupleList)
    #         dp.addInput(name="pisa_assembly_file_path", value=reportFilePath)
    #         #
    #         dp.op("pisa-assembly-merge-cif")
    #         dp.exp(outputModelPdbxPath)
    #         dp.expLog(logPath)

    #         if (self._verbose):
    #             self._lfh.write("+AnnotationUtils.assemblyInstanceUpdateOp() - PDBx file path:         %s\n" % pdbxPath)
    #             self._lfh.write("+AnnotationUtils.assemblyInstanceUpdateOp() - report file path:       %s\n" % reportFilePath)
    #             self._lfh.write("+AnnotationUtils.assemblyInstanceUpdateOp() - select file path:       %s\n" % selectFilePath)
    #             self._lfh.write("+AnnotationUtils.assemblyInstanceUpdateOp() - PDBx output file path:  %s\n" % outputModelPdbxPath)

    #         if (self.__cleanUp):
    #             dp.cleanup()
    #         return True
    #     except Exception as _e:  # noqa: F841
    #         traceback.print_exc(file=self._lfh)
    #         return False

    def assemblyUpdateDepInfoOp(self, **kwArgs):
        """Performs an update of the pdbx_struct_assembly_gen_depositor_info"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()

            pdbxOutputPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "assembly-depinfo-update.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            #
            dp.op("annot-update-dep-assembly-info")

            dp.expLog(logPath)
            dp.exp(pdbxOutputPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.assemblyUpdateDepInfoOp() - PDBx input  file path:  %s\n" % pdbxPath)
                self._lfh.write("+AnnotationUtils.assemblyUpdateDepInfoOp() - PDBx output file path:  %s\n" % pdbxOutputPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def __readAssemblyReport(self, reportPath):
        """Read assembly calculation report and return a dictionary of assembly details."""
        pA = PisaAssemblyReader(verbose=self._verbose, log=self._lfh)
        _ok = pA.read(reportPath)  # noqa: F841
        self.__assemblyD = pA.getAssemblyDict()  # pylint: disable=attribute-defined-outside-init
        return self.__assemblyD

    # def __readSelection(self, selectPath):
    #     """Read the comma separated selection string from a file in the current session directory."""
    #     try:
    #         ofh = open(selectPath, "r")
    #         tS = ofh.readline()
    #         ofh.close()
    #         if (tS is not None) and (len(tS) > 1):
    #             return tS[:-1]
    #         else:
    #             return None
    #     except Exception as _e:  # noqa: F841
    #         if self._verbose:
    #             traceback.print_exc(file=self._lfh)
    #         return None

    def mergeXyzOp(self, **kwArgs):
        """Merge coordinate data files and report status -"""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            inpXyzPath = inpObjD["src1"].getFilePathReference()
            newXyzPath = inpObjD["src2"].getFilePathReference()

            if "new_coordinate_format" in uD:
                iFormat = str(uD["new_coordinate_format"])
            else:
                iFormat = "cif"

            if iFormat in ["cif", "pdbx", "mmcif"]:
                newXyzFormat = "cif"
            else:
                newXyzFormat = "pdb"

            isDeposit = False
            if "deposit" in uD and (str(uD["deposit"]).lower() != "no"):
                isDeposit = True

            #
            dirPath = outObjD["dst1"].getDirPathReference()
            mergedFilePath = outObjD["dst1"].getFilePathReference()
            logFilePath = outObjD["dst2"].getFilePathReference()

            if self._verbose:
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ input   file path:  %s\n" % inpXyzPath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ new     file path:  %s\n" % newXyzPath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ new file   format:  %s\n" % newXyzFormat)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - directory path:         %s\n" % dirPath)
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setDebugMode(flag=True)
            dp.imp(inpXyzPath)
            if (newXyzPath is not None) and os.path.exists(newXyzPath):
                dp.addInput(name="new_coordinate_file_path", value=newXyzPath, type="file")
                dp.addInput(name="new_coordinate_format", value=newXyzFormat, type="param")
            else:
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ new source input not found in file path:  %s\n" % newXyzPath)
            if isDeposit:
                dp.addInput(name="deposit", value=True, type="param")

            dp.op("annot-merge-xyz")
            dp.expLog(logFilePath)
            dp.exp(mergedFilePath)

            if not os.access(mergedFilePath, os.R_OK):
                myStatus = "error"
            else:
                myStatus = self.__checkMergeStatus(logFilePath)

            outObjD["dst3"].setValue(myStatus)

            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ input   file path:  %s\n" % inpXyzPath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - XYZ new     file path:  %s\n" % newXyzPath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - LOG output  file path:  %s\n" % logFilePath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - PDBx merged file path:  %s\n" % mergedFilePath)
                self._lfh.write("+AnnotationUtils.mergeXyzOp() - return status:          %r\n" % myStatus)

            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def __checkMergeStatus(self, logFilePath):
        # Tom changed this to check the last line as finished!
        # if the first line is not 'finished!' then there is a failure -
        status = "error"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                if str(line).upper().startswith("FINISHED"):
                    status = "ok"

            ifh.close()
        else:
            status = "error"
        return status

    def combineCifFilesOp(self, **kwArgs):
        """Merges the first datablock from src1 and selected categories in
        src2 and output to dst1. Will not overwrite if present
        """
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            srcPath = inpObjD["src1"].getFilePathReference()
            mrgPath = inpObjD["src2"].getFilePathReference()
            outPath = outObjD["dst"].getFilePathReference()
            if "categories" in uD:
                # Handle incomming unicode
                mrgCat = str(uD["categories"]).split(",")
            else:
                mrgCat = None

            if self._verbose:
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - src1 input  file paths:  %s\n" % srcPath)
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - src2 input  file paths:  %s\n" % mrgPath)
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - output path: %s\n" % outPath)
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - mrgCat: %s\n" % mrgCat)

            ioObj = IoAdapterCore(verbose=self._verbose, log=self._lfh)
            tmpdir = os.path.abspath(os.path.dirname(srcPath))
            dIn = ioObj.readFile(inputFilePath=srcPath, outDirPath=tmpdir)
            if not dIn:
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() -failed to load src1\n")
                return False

            srcBlock = dIn[0]

            mrgIn = ioObj.readFile(inputFilePath=mrgPath, selectList=mrgCat, outDirPath=tmpdir)
            if not mrgIn:
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - Failed to load src2\n")
                return False

            mrgBlock = mrgIn[0]

            dstNameList = srcBlock.getObjNameList()

            if len(mrgBlock.getObjNameList()) == 0:
                self._lfh.write("+AnnotationUtils.combineCifFilesOp() - nothing to merge\n")
                return True

            for cName in mrgBlock.getObjNameList():
                # If destination has object - do not overwrite
                if cName not in dstNameList:
                    cObj = mrgBlock.getObj(cName)
                    srcBlock.append(cObj)

            # Write out
            ret = ioObj.writeFile(outputFilePath=outPath, containerList=dIn)
            return ret
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def em3dAutoMapFixOp(self, **kwArgs):
        """Performs mapfix if needed automatically.  Typically run on model and map files in archive as they need to be in sync."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            sessdir = inpObjD["sessdir"].getDirPathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            pdbxOutPath = outObjD["dst"].getFilePathReference()

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")

            eaf = EmAutoFix(sessionPath=sessdir, siteId=siteId)
            _ret = eaf.autoFixMapLabels(datasetid=depDataSetId, modelin=pdbxPath, modelout=pdbxOutPath)  # noqa: F841
            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def em3dAutoEmMapFixVersOp(self, **kwArgs):
        """Updates version numbers of files in em_map category in model file.  Typically run on model and map files in archive as they need to be in sync."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            sessdir = inpObjD["sessdir"].getDirPathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            pdbxOutPath = outObjD["dst"].getFilePathReference()

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")

            if "location" in uD:
                location = str(uD["location"])
            else:
                location = "archive"

            eaf = EmMapAutoFixVers(sessionPath=sessdir, siteId=siteId)
            ret = eaf.autoFixEmMapVersions(datasetid=depDataSetId, modelin=pdbxPath, modelout=pdbxOutPath, location=location)
            self._lfh.write("+em3dAutoEmMapFixVersOp fixvers returns %s\n" % ret)

            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updatePdbxDatabaseRelatedOp(self, **kwArgs):
        """Updates pdbx_database_related by performing lookups on deposition ids D_XXX in the db_id field for PDB, BMRB and EMDB"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            pdbxOutPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "update_pdbx_database_related.log")

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")

            ur = UpdateRelated(siteId=siteId)
            ret = ur.updateRelatedEntries(pdbxPath, pdbxOutPath, logPath)

            self._lfh.write("+updatePdbxDatabaseRelatedOp returns %s\n" % ret)

            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updateSFWavelengthOp(self, **kwArgs):
        """Updates wavelnegth in SF fie"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            sfPath = inpObjD["src2"].getFilePathReference()
            sfOutPath = outObjD["dst"].getFilePathReference()
            # For session directory
            dirPath = inpObjD["src1"].getDirPathReference()
            entryId = inpObjD["src1"].getDepositionDataSetId()

            if not os.path.exists(sfPath):
                # NMR, EM, etc
                return True

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
            myReqObj.setValue("TopSessionPath", dirPath)
            myReqObj.setValue("WWPDB_SITE_ID", siteId)
            myReqObj.newSessionObj()

            peu = PdbxExpUpdate(myReqObj, verbose=self._verbose, log=self._lfh)
            ret = peu.doUpdate(entryId, modelInputFile=pdbxPath, expInputFile=sfPath, expOutputFile=sfOutPath, skipNotChanged=True)

            self._lfh.write("+updateSFWavelengthOp returns %s\n" % ret)

            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def emdXmlHeaderCheckOp(self, **kwArgs):
        """Checks EMD -> XML header conversion"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            # logPath = os.path.join(dirPath, "dict-check.log")

            ioObj = IoAdapterCore(verbose=self._verbose, log=self._lfh)
            dIn = ioObj.readFile(inputFilePath=pdbxPath, selectList=["em_admin"])
            if not dIn or len(dIn) == 0:
                return True

            cObj = dIn[0].getObj("em_admin")
            if not cObj:
                # No em_admin
                return True

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")

            hostName = str(socket.gethostname()).split(".")[0]  # pylint: disable=no-member
            if (hostName is not None) and (len(hostName) > 0):
                suffix = "-" + hostName
            else:
                suffix = "-dir"
            wrkPath = tempfile.mkdtemp(suffix, "rcsb-", dirPath)
            os.chmod(wrkPath, 0o750)

            emdXmlPath = os.path.join(wrkPath, depDataSetId + "-emd.xml")

            fPath = pdbxPath

            emh = EmHeaderUtils(siteId=siteId, verbose=self._verbose, log=self._lfh)
            if hasattr(emh, "transEmd"):
                # Still running EM->EMD conversion
                emdModelPath = os.path.join(wrkPath, depDataSetId + "_model-emd.cif")
                status = emh.transEmd(pdbxPath, emdModelPath, mode="src-dst", tags=[])
                if not status:
                    self._lfh.write("Translation of model failed\n")
                    return True
                fPath = emdModelPath

            status = emh.transHeader(fPath, emdXmlPath, reportPath, validateXml=True)
            self._lfh.write("Status of xml translation %s\n" % status)

            # Cleanup directory
            shutil.rmtree(wrkPath, ignore_errors=True)

            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def emMapCheckOp(self, **kwArgs):
        """Checks em_map category"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            #
            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            #
            checkTask = EmMapCheckTask(siteId=siteId, sessionPath=dirPath, verbose=self._verbose, log=self._lfh)
            checkTask.run(depDataSetId, pdbxPath, reportPath)
            # Always return true - even if no work done
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def emVolumeBcifConversionOp(self, **kwArgs):
        """
        converts EM volume from map format into bcif
        :param kwArgs:
        :return bool: True if worked, False if failed
        """
        try:
            (inpObjD, _outObjD, _uD, _pD) = self._getArgs(kwArgs)
            modelPath = inpObjD["src"].getFilePathReference()
            # depDataSetId = inpObjD["src"].getDepositionDataSetId()

            dirPath = inpObjD["src"].getDirPathReference()
            if not os.path.exists(modelPath):
                # no model
                raise IOError("Missing model file")

            ioObj = IoAdapterCore(verbose=self._verbose, log=self._lfh)
            dIn = ioObj.readFile(inputFilePath=modelPath, selectList=["em_map"])
            if not dIn or len(dIn) == 0:
                return True

            cObj = dIn[0].getObj("em_map")
            if not cObj:
                # No em_map
                return True

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            pi = PathInfo(siteId=siteId)

            # loop through all the map file names in the mmcif file and convert to Bcif files
            for mapNumber in range(0, len(cObj)):
                mapName = cObj.getValue("file", mapNumber)
                mapNameInfo = pi.parseFileName(mapName)
                mapPath = pi.getFilePath(mapNameInfo[0], contentType=mapNameInfo[1], formatType=mapNameInfo[2], partNumber=mapNameInfo[3])
                mapBcifPath = pi.getFilePath(mapNameInfo[0], contentType=mapNameInfo[1], formatType="bcif", partNumber=mapNameInfo[3])
                dw = DensityWrapper()
                dw.convert_em_volume(in_em_volume=mapPath, out_binary_volume=mapBcifPath, working_dir=dirPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def xrayBcifConversionOp(self, **kwArgs):
        """
        converts X-ray maps from maps format into bcif
        :param kwArgs:
        :return bool: True if worked, False if failed
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            coordinates = inpObjD["src1"].getFilePathReference()
            twofofcmap = inpObjD["src2"].getFilePathReference()
            fofcmap = inpObjD["src3"].getFilePathReference()
            # depDataSetId = inpObjD["src1"].getDepositionDataSetId()

            mapBcifPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            if os.path.exists(twofofcmap) and os.path.exists(fofcmap) and os.path.exists(coordinates):
                dw = DensityWrapper()
                return dw.convert_xray_density_map(coord_file=coordinates, in_2fofc_cif=twofofcmap, in_fofc_cif=fofcmap, out_binary_volume=mapBcifPath, working_dir=dirPath)
            else:
                # no x-ray mmCIF map files
                return True

        except Exception as _e:  # noqa: F841
            logging.error(_e)
            traceback.print_exc(file=self._lfh)
            return False

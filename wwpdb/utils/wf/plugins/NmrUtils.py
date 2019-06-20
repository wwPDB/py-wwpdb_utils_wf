##
# File:    NmrUtils.py
# Date:    18-Oct-2013
#
# Updates:
# 12-Sep-2014 jdw    added formatCheckCsXyzOp() and atomNameCheckCsXyzOp()
#  4-Aug-2015 jdw    added atomNameCheckCsXyzAltOp() and uploadChemicalShiftAltOp()
##
"""
Module of NMR utilities.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback
import logging
import shutil
import datetime
import time
import difflib
import string
import random

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.nmr.ExtractFromCCPN import CcpnProject
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.utils.dp.PdbxChemShiftReport import PdbxChemShiftReport
try:
    # XXX We will have present on annotation system - but allow testing of DepUI merge without
    from wwpdb.apps.ann_tasks_v2.nmr.NmrChemShiftProcessUtils import NmrChemShiftProcessUtils
except ImportError:
    pass

from wwpdb.utils.nmr.NmrDpUtility import NmrDpUtility

sys.stdout = sys.stderr

class NmrUtils(UtilsBase):

    """ Utility class to perform NMR file format conversions.




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
        super(NmrUtils, self).__init__(verbose, log)
        self.__cleanUp = True
        """Flag to remove any temporary directories created by this class.
        """
        #

    def ccpnExtractOp(self, **kwArgs):
        """Extract PDB and NMRSTAR files from CCPn project
        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            ccpnPath = inpObjD["src"].getFilePathReference()
            pdbPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            strPath = outObjD["dst2"].getFilePathReference()
            #
            uniq = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6)) + '_ccpn-convert'

            CcpnProject(ccpn=ccpnPath,
                        star=strPath,
                        pdb=pdbPath,
                        uniq=uniq
                        ).process()
            if (self._verbose):
                self._lfh.write("+NmrUtils.ccpnExtractOp() - CCPn input  file path:     %s\n" % ccpnPath)
                self._lfh.write("+NmrUtils.ccpnExtractOp() - PDB  output file path:     %s\n" % pdbPath)
                self._lfh.write("+NmrUtils.ccpnExtractOp() - NMRSTAR  output file path: %s\n" % strPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def formatCheckCsOp(self, **kwArgs):
        """Performs format check on Cs file and returns a text check report.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPath = inpObjD["src"].getFilePathReference()
            reportPath = outObjD["dst1"].getFilePathReference()
            convertedStarPath = outObjD["dst2"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = os.path.join(dirPath, "format-check-cs.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)

            dp.imp(csPath)
            dp.op("annot-chem-shift-check")
            dp.expLog(logPath)
            dp.expList([reportPath, convertedStarPath])
            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.formatCheckCsOp() - Cs input  file path:    %s\n" % csPath)
                self._lfh.write("+AnnotationUtils.formatCheckCsOp() - Cs output file path:    %s\n" % convertedStarPath)
                self._lfh.write("+AnnotationUtils.formatCheckCsOp() - Report file path:       %s\n" % reportPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def formatCheckCsXyzOp(self, **kwArgs):
        """Performs format check on Cs and XYZ file and returns a text check report.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPath = inpObjD["src1"].getFilePathReference()
            xyzPath = inpObjD["src2"].getFilePathReference()

            reportPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            logPath = os.path.join(dirPath, "format-check-cs-xyz.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)

            dp.imp(csPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.op("annot-chem-shift-coord-check")
            dp.expLog(logPath)
            dp.exp(reportPath)
            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.formatCheckCsXyzOp() - Cs input  file path:    %s\n" % csPath)
                self._lfh.write("+AnnotationUtils.formatCheckCsXyzOp() - Report file path:       %s\n" % reportPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def uploadChemicalShiftOp(self, **kwArgs):
        """Performs format check on a list of chemical shift files and concatenates these.

           Data sections are assigned to user provided input names corresponding to each input file.

           Output is a concatenated chemical shift file,  text status (ok,warning,error) and text list of
           warnings and/or errors.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPathList = inpObjD["src1"].getValue()
            nameList = inpObjD["src2"].getValue()
            #
            csOutPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            chkPath = outObjD["dst2"].getFilePathReference()

            logPath = os.path.join(dirPath, "upload-chemical-shift-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setDebugMode(flag=True)

            dp.addInput(name="chemical_shifts_file_path_list", value=csPathList)
            dp.addInput(name="chemical_shifts_auth_file_name_list", value=nameList)
            dp.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath)
            #
            dp.op("annot-chem-shifts-upload-check")
            dp.expLog(logPath)
            dp.exp(csOutPath)

            csr = PdbxChemShiftReport(inputPath=chkPath, verbose=self._verbose, log=self._lfh)
            status = str(''.join(csr.getStatus())).lower()
            warnings = csr.getWarnings()
            errors = csr.getErrors()

            outObjD['dst3'].setValue(status)
            outObjD['dst4'].setValue(warnings)
            outObjD['dst5'].setValue(errors)

            #
            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() - CS path list :    %s\n" % csPathList)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() - CS name list :    %s\n" % nameList)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() - CS output path :  %s\n" % csOutPath)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() Status code: %s\n" % status)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() Warning count : %d\n %s\n" % (len(warnings), ('\n').join(warnings)))
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftOp() Error count : %d\n %s\n" % (len(errors), ('\n').join(errors)))

            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def uploadChemicalShiftAltOp(self, **kwArgs):
        """Performs format check on a list of chemical shift files and concatenates these.

           Data sections are assigned to user provided input names corresponding to each input file.

           Output is a concatenated chemical shift file, and check report file -

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPathList = []
            csPathListFilePath = inpObjD["src1"].getFilePathReference()
            nameList = []
            nameListFilePath = inpObjD["src2"].getFilePathReference()
            #
            ifh = open(csPathListFilePath, 'r')
            for tline in ifh:
                txt = str(tline[:-1]).strip()
                csPathList.append(txt)
            ifh.close()
            #
            ifh = open(nameListFilePath, 'r')
            for tline in ifh:
                txt = str(tline[:-1]).strip()
                nameList.append(txt)
            ifh.close()
            #
            csOutPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            chkPath = outObjD["dst2"].getFilePathReference()

            logPath = os.path.join(dirPath, "upload-chemical-shift-check.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setDebugMode(flag=True)

            dp.addInput(name="chemical_shifts_file_path_list", value=csPathList)
            dp.addInput(name="chemical_shifts_auth_file_name_list", value=nameList)
            dp.addInput(name="chemical_shifts_upload_check_file_path", value=chkPath)
            #
            dp.op("annot-chem-shifts-upload-check")
            dp.expLog(logPath)
            dp.exp(csOutPath)

            #
            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftAltOp() - CS path list :    %s\n" % csPathList)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftAltOp() - CS name list :    %s\n" % nameList)
                self._lfh.write("+AnnotationUtils.uploadChemicalShiftAltOp() - CS output path :  %s\n" % csOutPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def atomNameCheckCsXyzOp(self, **kwArgs):
        """Performs nomenclature and format check on input CS and XYZ files and returns an updated CS file, a CIF check report,
           status (text=ok,warning,error), and both  warnings and error messages as a list of strings.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPath = inpObjD["src1"].getFilePathReference()
            xyzPath = inpObjD["src2"].getFilePathReference()

            csOutPath = outObjD["dst1"].getFilePathReference()
            chkPath = outObjD["dst2"].getFilePathReference()
            dirPath = outObjD["dst2"].getDirPathReference()
            logPath = os.path.join(dirPath, "atom-name-check-cs-xyz.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)

            dp.imp(csPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")

            dp.expLog(logPath)
            dp.exp(csOutPath)

            csr = PdbxChemShiftReport(inputPath=chkPath, verbose=self._verbose, log=self._lfh)
            status = str(''.join(csr.getStatus())).lower()
            warnings = csr.getWarnings()
            errors = csr.getErrors()

            outObjD['dst3'].setValue(status)
            outObjD['dst4'].setValue(warnings)
            outObjD['dst5'].setValue(errors)

            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.atomNameCheckCsXyzOp() - Cs input  file path:    %s\n" % csPath)
                self._lfh.write("+AnnotationUtils.atomNameCheckCsXyzOp() - Report file path:       %s\n" % chkPath)
                self._lfh.write("+AnnotationUtils.atomNameShiftOp() Status code: %s\n" % status)
                self._lfh.write("+AnnotationUtils.atomNameShiftOp() Warning count : %d\n %s\n" % (len(warnings), ('\n').join(warnings)))
                self._lfh.write("+AnnotationUtils.atomNameShiftOp() Error count : %d\n %s\n" % (len(errors), ('\n').join(errors)))

            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def atomNameCheckCsXyzAltOp(self, **kwArgs):
        """Performs nomenclature and format check on input CS and XYZ files and returns an updated CS file, a CIF check report.

            * workflow version * returns chemical shift file and check report output --
        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            csPath = inpObjD["src1"].getFilePathReference()
            xyzPath = inpObjD["src2"].getFilePathReference()

            csOutPath = outObjD["dst1"].getFilePathReference()
            chkPath = outObjD["dst2"].getFilePathReference()
            dirPath = outObjD["dst2"].getDirPathReference()
            logPath = os.path.join(dirPath, "atom-name-check-cs-xyz.log")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)

            dp.imp(csPath)
            dp.addInput(name="coordinate_file_path", value=xyzPath)
            dp.addInput(name="chemical_shifts_coord_check_file_path", value=chkPath)

            dp.op("annot-chem-shifts-atom-name-check")

            dp.expLog(logPath)
            dp.exp(csOutPath)

            if (self.__cleanUp):
                dp.cleanup()
            if (self._verbose):
                self._lfh.write("+AnnotationUtils.atomNameCheckCsXyzAltOp() - Cs input  file path:    %s\n" % csPath)
                self._lfh.write("+AnnotationUtils.atomNameCheckCsXyzAltOp() - Report file path:       %s\n" % chkPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def autoChemShiftProcessOp(self, **kwArgs):
        """Performs chemical shift file update & nomenclature and format check on input CS and XYZ files and returns an updated CS file, a CIF check report.

            * workflow version * returns chemical shift file and check report output --
        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            xyzPath = inpObjD["src1"].getFilePathReference()
            csPath = inpObjD["src2"].getFilePathReference()
            #
            xyzOutPath = outObjD["dst1"].getFilePathReference()
            csOutPath = outObjD["dst2"].getFilePathReference()
            dirPath = outObjD["dst2"].getDirPathReference()
            validationReportPath = outObjD["dst3"].getFilePathReference()
            xmlReportPath = outObjD["dst4"].getFilePathReference()
            validationFullReportPath = outObjD["dst5"].getFilePathReference()
            pngReportPath = outObjD["dst6"].getFilePathReference()
            svgReportPath = outObjD["dst7"].getFilePathReference()
            csReportPath = outObjD["dst8"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            util = NmrChemShiftProcessUtils(siteId=siteId, verbose=self._verbose, log=self._lfh)
            util.setWorkingDirPath(dirPath=dirPath)
            util.setInputModelFileName(fileName=xyzPath)
            util.setInputCsFileName(fileName=csPath)
            util.setOutputModelFileName(fileName=xyzOutPath)
            util.setOutputCsFileName(fileName=csOutPath)
            util.setOutputReportFileName(fileName=csReportPath)
            util.setOutputValidationFileList(dstPathList=[ validationReportPath, xmlReportPath, validationFullReportPath, pngReportPath, svgReportPath ])
            util.run()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    # DepUI for NMR unified data: NEF consistency check with model
    #   action: nmr-nef-consistency-check
    #   src1.content: nmr-unified-data-nef,     src1.format: nmr-star
    #   src2.content: model,                    src2.format: pdbx
    #   dst.content:  nmr-unified-data-report,  dst.format:  json
    def nefConsistencyCheckOp(self, **kwArgs):
        """Performs consistency check on input NEF with coordinate and outputs a JSON report file, which provides diagnostic information to depositor.

           Returns True for success or False for warnings/errors.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            nefInpPath = inpObjD["src1"].getFilePathReference()
            cifInpPath = inpObjD["src2"].getFilePathReference()
            logOutPath = outObjD["dst"].getFilePathReference()
            #
            dp = NmrDpUtility(verbose=self._verbose, log=self._lfh)
            dp.setVerbose(flag=True)
            dp.setSource(nefInpPath)
            dp.addInput(name='coordinate_file_path', value=cifInpPath, type='file')
            dp.setLog(logOutPath)
            stat = dp.op("nmr-nef-consistency-check")
            #
            if (self._verbose):
                self._lfh.write("+NmrUtils.consistencyCheckNefOp() - NEF input file path:      %s\n" % nefInpPath)
                self._lfh.write("+NmrUtils.consistencyCheckNefOp() - mmCIF input file path:    %s\n" % cifInpPath)
                self._lfh.write("+NmrUtils.consistencyCheckNefOp() - JSON output file path:    %s\n" % logOutPath)
            return stat
        except:
            traceback.print_exc(file=self._lfh)
            return False

    # DepUI for NMR unified data: NMR-STAR V3.2 consistency check with model
    #   action: nmr-str-consistency-check
    #   src1.content: nmr-unified-data-str,     src1.format: nmr-star
    #   src2.content: model,                    src2.format: pdbx
    #   dst.content:  nmr-unified-data-report,  dst.format:  json
    def strConsistencyCheckOp(self, **kwArgs):
        """Performs consistency check on input NMR-STAR V3.2 with coordinate and outputs a JSON report file, which provides diagnostic information to depositor.

           Returns True for success or False for warnings/errors.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            strInpPath = inpObjD["src1"].getFilePathReference()
            cifInpPath = inpObjD["src2"].getFilePathReference()
            logOutPath = outObjD["dst"].getFilePathReference()
            #
            dp = NmrDpUtility(verbose=self._verbose, log=self._lfh)
            dp.setVerbose(flag=True)
            dp.setSource(strInpPath)
            dp.addInput(name='coordinate_file_path', value=cifInpPath, type='file')
            dp.setLog(logOutPath)
            stat = dp.op("nmr-str-consistency-check")
            #
            if (self._verbose):
                self._lfh.write("+NmrUtils.consistencyCheckStarOp() - NMR-STAR V3.2 input file path:    %s\n" % strInpPath)
                self._lfh.write("+NmrUtils.consistencyCheckStarOp() - mmCIF input file path:            %s\n" % cifInpPath)
                self._lfh.write("+NmrUtils.consistencyCheckStarOp() - JSON output file path:            %s\n" % logOutPath)
            return stat
        except:
            traceback.print_exc(file=self._lfh)
            return False

    # DepUI for NMR unified data: NEF -> NMR-STAR V3.2 conversion and deposition
    #   action: nmr-nef2str-deposit
    #   src1.content: nmr-unified-data-nef,     src1.format: nmr-star
    #   src2.content: model,                    src2.format: pdbx
    #   src3.content: nmr-unified-data-report,  src3.format: json
    #   dst1.content: nmr-unified-data-nef,     dst1.format: nmr-star
    #   dst2.content: nmr-unified-data-str,     dst2.format: nmr-star
    #   dst3.content: nmr-unified-data-report,  dst3.format: json
    #   dst4.content: nmr-unified-data-report,  dst4.format: json
    def nef2strDepositOp(self, **kwArgs):
        """Perform NEF to NMR-STAR V3.2 format conversion operation (special processing for deposition sessions)

           Returns True for success or False for warnings/errors.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            nefInpPath = inpObjD["src1"].getFilePathReference()
            cifInpPath = inpObjD["src2"].getFilePathReference()
            logInpPath = outObjD["src3"].getFilePathReference()
            nefOutPath = outObjD["dst1"].getFilePathReference()
            strOutPath = outObjD["dst2"].getFilePathReference()
            logOutPath1 = outObjD["dst3"].getFilePathReference()
            logOutPath2 = outObjD["dst4"].getFilePathReference()
            #
            dp = NmrDpUtility(verbose=self._verbose, log=self._lfh)
            dp.setVerbose(flag=True)
            dp.setSource(nefInpPath)
            dp.addInput(name='coordinate_file_path', value=cifInpPath, type='file')
            dp.addInput(name='report_file_path', value=logInpPath, type='file')
            dp.setDestination(nefOutPath)
            dp.addOutput(name='nmr-star_file_path', value=strOutPath, type='file')
            dp.addOutput(name='report_file_path', value=logOutPath2, type='file')
            dp.setLog(logOutPath1)
            stat = dp.op("nmr-nef2str-deposit")
            #
            if (self._verbose):
                self._lfh.write("+NmrUtils.nef2strDepositOp() - NEF input file path:        %s\n" % nefInpPath)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - mmCIF input file path:      %s\n" % cifInpPath)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - JSON input file path:       %s\n" % logInpPath)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - NEF output file path:       %s\n" % nefOutPath)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - NMR-STAR V3.2 file path:    %s\n" % strOutPath)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - JSON output file path 1:    %s\n" % logOutPath1)
                self._lfh.write("+NmrUtils.nef2strDepositOp() - JSON output file path 2:    %s\n" % logOutPath2)
            return stat
        except:
            traceback.print_exc(file=self._lfh)
            return False

    # DepUI for NMR unified data: NMR-STAR V3.2 conversion and deposition
    #   action: nmr-str2str-deposit
    #   src1.content: nmr-unified-data-str,     src1.format: nmr-star
    #   src2.content: model,                    src2.format: pdbx
    #   src3.content: nmr-unified-data-report,  src3.format: json
    #   dst1.content: nmr-unified-data-str,     dst1.format: nmr-star
    #   dst2.content: nmr-unified-data-report,  dst2.format: json
    def str2strDepositOp(self, **kwArgs):
        """Perform NMR-STAR V3.2 format conversion operation (special processing for deposition sessions)

           Returns True for success or False for warnings/errors.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            strInpPath = inpObjD["src1"].getFilePathReference()
            cifInpPath = inpObjD["src2"].getFilePathReference()
            logInpPath = outObjD["src3"].getFilePathReference()
            strOutPath = outObjD["dst1"].getFilePathReference()
            logOutPath = outObjD["dst2"].getFilePathReference()
            #
            dp = NmrDpUtility(verbose=self._verbose, log=self._lfh)
            dp.setVerbose(flag=True)
            dp.setSource(strInpPath)
            dp.addInput(name='coordinate_file_path', value=cifInpPath, type='file')
            dp.addInput(name='report_file_path', value=logInpPath, type='file')
            dp.setDestination(strOutPath)
            dp.setLog(logOutPath)
            stat = dp.op("nmr-str2str-deposit")
            #
            if (self._verbose):
                self._lfh.write("+NmrUtils.str2strDepositOp() - NMR-STAR V3.2 input file path:     %s\n" % strInpPath)
                self._lfh.write("+NmrUtils.str2strDepositOp() - mmCIF input file path:             %s\n" % cifInpPath)
                self._lfh.write("+NmrUtils.str2strDepositOp() - JSON input file path:              %s\n" % logInpPath)
                self._lfh.write("+NmrUtils.str2strDepositOp() - NMR-STAR V3.2 output file path:    %s\n" % strOutPath)
                self._lfh.write("+NmrUtils.str2strDepositOp() - JSON output file path:             %s\n" % logOutPath)
            return stat
        except:
            traceback.print_exc(file=self._lfh)
            return False


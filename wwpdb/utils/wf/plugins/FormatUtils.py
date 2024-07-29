##
# File:    FormatUtils.py
# Date:    10-April-2010
#
# Updates:
# 23-April-2010  jdw Add rcsb internal cif to pdbx
# 18-April-2013  jdw update to latest RcsbDbUtility() class -
# 29-May  -2013  jdw Add pdb2pdbxDepositOp()  and pdbx2pdbxDepositOp() methods
# 15-Aug  -2013  jdw Add mtz2pdbxOp()
# 31-Dec  -2013  jdw add timeout for mtz2pdbxOp()
# 16-Jan  -2014  jdw repoint dst3 in mtz2pdbxOp() to logfile
# 26-Sep  -2014  jdw add pdbx2nmrstarAnnotOp() from annotation package
##
"""
Module of format translation utility operations supporting the call protocol of the ProcessRunner() class.

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
# from wwpdb.utils.wf.plugins.SFConvert import SFConvert


class FormatUtils(UtilsBase):

    """Utility class to perform file format conversions.

    Current supported operations include:
    - annot-pdbx2pdb (cif2pdb)
    - annot-pdb2pdbx (pdb2cif)
    - annot-rcsb2pdbx (cif2pdbx)
    - annot-cif2cif-dep   (pdbx2pdbx)
    - annot-pdb2cif-dep   (pdb2cif)

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
        super(FormatUtils, self).__init__(verbose, log)
        self.__cleanUp = True
        """Flag to remove any temporary directories created by this class.
        """
        #

    def pdbx2pdbOp(self, **kwArgs):
        """Performs PDBx(cif) to PDB format conversion operation."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            pdbPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-cif2pdb")
            dp.exp(pdbPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.pdbx2pdbOp() - PDB  file path: %s\n" % pdbPath)
                self._lfh.write("+FormatUtils.pdbx2pdbOp() - PDBx file path: %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def pdb2pdbxOp(self, **kwArgs):
        """Perform PDB to PDBx(cif) format conversion operation."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbPath = inpObjD["src"].getFilePathReference()
            pdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbPath)
            dp.op("annot-pdb2cif")
            dp.exp(pdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.pdb2pdbxOp() - PDB  file path: %s\n" % pdbPath)
                self._lfh.write("+FormatUtils.pdb2pdbxOp() - PDBx file path: %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def pdb2pdbxDepositOp(self, **kwArgs):
        """Perform PDB to PDBx(cif) format conversion operation (special processing for deposition sessions)"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbPath = inpObjD["src"].getFilePathReference()
            pdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbPath)
            dp.op("annot-pdb2cif-dep")
            dp.exp(pdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.pdb2pdbxDepositOp() - PDB  file path: %s\n" % pdbPath)
                self._lfh.write("+FormatUtils.pdb2pdbxDepositOp() - PDBx file path: %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def rcsb2pdbxOp(self, **kwArgs):
        """Perform RCSB(cif) to PDBx(cif) format conversion operation."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            rcsbPath = inpObjD["src"].getFilePathReference()
            pdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(rcsbPath)
            dp.op("annot-cif2cif")
            dp.exp(pdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.cif2cifOp() - RCSB cif file path: %s\n" % rcsbPath)
                self._lfh.write("+FormatUtils.cif2cifOp() - PDBx file path: %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def pdbx2pdbxDepositOp(self, **kwArgs):
        """Perform  PDBx(cif) to PDBx(cif) format conversion operation (special processing deposition sessions)"""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            rcsbPath = inpObjD["src"].getFilePathReference()
            pdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(rcsbPath)
            dp.op("annot-cif2cif-dep")
            dp.exp(pdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.pdbx2pdbxDepositOp() - PDBx input  file path: %s\n" % rcsbPath)
                self._lfh.write("+FormatUtils.pdbx2pdbxDepositOp() - PDBx output file path: %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def mtz2pdbxOp(self, **kwArgs):
        """Perform  MTZ or other SF file  to  PDBx(cif) format conversion operation."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            sfPath = inpObjD["src1"].getFilePathReference()
            # sfFmt = inpObjD["src1"].getFileFormat()
            xyzPath = inpObjD["src2"].getFilePathReference()
            #
            #
            sfPdbxFilePath = outObjD["dst1"].getFilePathReference()
            sfDiagFilePath = outObjD["dst2"].getFilePathReference()
            logFilePath = outObjD["dst3"].getFilePathReference()
            #
            dirPath = outObjD["dst1"].getDirPathReference()
            #
            # logPath=os.path.join(dirPath,"mtz2pdbx.log")
            dmpPath = os.path.join(dirPath, "mtzdmp.log")
            #
            timeout = int(uD["timeout"])
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")

            # if sfFmt == "pdbx":
            #     # See if we can handle specially
            #     sfc = SFConvert()
            #     if sfc.isSpecialSF(sfPath):
            #         ok = sfc.handleSpecialSF(sfPath, sfPdbxFilePath, xyzPath, sfDiagFilePath, logFilePath)
            #         self._lfh.write("Special handling of SF file returns %s\n" % ok)
            #         if ok is True:
            #             return True
            #        # Else fall through

            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(sfPath)
            if (xyzPath is not None) and os.path.exists(xyzPath):
                dp.addInput(name="xyz_file_path", value=xyzPath, type="file")
            if timeout > 0:
                dp.setTimeout(timeout)
            dp.op("annot-sf-convert")
            dp.expLog(logFilePath)
            dp.expList(dstPathList=[sfPdbxFilePath, sfDiagFilePath, dmpPath])

            #
            myStatus = self.__checkMergeStatus(logFilePath)
            outObjD["dst4"].setValue(myStatus)

            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.mtz2pdbxOp() - timeout :      %d\n" % timeout)
                self._lfh.write("+FormatUtils.mtz2pdbxOp() - SF  input  file path:      %s\n" % sfPath)
                self._lfh.write("+FormatUtils.mtz2pdbxOp() - XYZ input  file path:      %s\n" % xyzPath)
                self._lfh.write("+FormatUtils.mtz2pdbxOp() - PDBx SF output file path:  %s\n" % sfPdbxFilePath)
                self._lfh.write("+FormatUtils.mtz2pdbxOp() - Log file path:             %s\n" % logFilePath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def nmrstar2pdbxOp(self, **kwArgs):
        """Perform NMRSTAR to PDBx(cif) format conversion operation."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            strPath = inpObjD["src"].getFilePathReference()
            pdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            dId = uD["data_set_id"]
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(strPath)
            dp.addInput(name="data_set_id", value=dId)
            dp.op("annot-nmrstar2pdbx")
            dp.exp(pdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.nmrstar2pdbxOp() - NMRSTAR  file path: %s\n" % strPath)
                self._lfh.write("+FormatUtils.nmrstar2pdbxOp() - PDBx file path:     %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def pdbx2nmrstarAnnotOp(self, **kwArgs):
        """Perform PDBx(cif) to NMRSTAR format conversion operation.  (using annotation package stack)"""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = outObjD["src"].getFilePathReference()
            strPath = inpObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            dId = uD["data_set_id"]
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.addInput(name="pdb_id", value=dId)
            dp.op("annot-pdbx2nmrstar")
            dp.exp(strPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+FormatUtils.pdbx2nmrstarAnnotOp() - NMRSTAR  file path: %s\n" % strPath)
                self._lfh.write("+FormatUtils.pdbx2nmrstarAnnotOp() - PDBx file path:     %s\n" % pdbxPath)
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def __checkMergeStatus(self, logFilePath):
        status = "ok"
        if os.access(logFilePath, os.R_OK):
            ifh = open(logFilePath, "r")
            for line in ifh:
                if str(line).upper().startswith("++ERROR") or str(line).upper().startswith("ERROR:"):
                    return "error"
                if str(line).upper().startswith("++WARN") or str(line).upper().startswith("WARN:"):
                    return "warn"
            ifh.close()
        else:
            return "error"
        return status

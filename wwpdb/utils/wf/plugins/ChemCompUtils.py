##
# File:    ChemCompUtils.py
# Date:    10-Sept-2010
#
# Updates:
# 2011-09-13    RPS    Explicitly setting name of working directory used during calls for "chem-comp-assign" processing.
# 2012-06-14    jdw    Add user selection file to instance update option.
# 2013-06-27    RPS    Added chemCompAssignExactOp and chemCompAssignExactNLOp for use by LigandLite Module.
# 2014-07-07    jdw    Disable user selection file to instance update option.
# 2026-07-10     zf    Add chemCompAssignUIOp and chemCompAssignNLUIOp
##
"""
Module of chemical component utility operations supporting the call protocol of the ProcessRunner() class.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback

from mmcif.io.IoAdapterCore import IoAdapterCore
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.dp.MetalCoordinationUtility import MetalCoordinationUtility
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase


class ChemCompUtils(UtilsBase):
    """Utility class to perform file format conversions.

    Current supported operations include:

    - Chemical component linkage calculation
    - Chemical component assignment
    - Chemical component instance assignment update

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
        super(ChemCompUtils, self).__init__(verbose, log)
        # DO NOT SET TO TRUE - RcsbDpUtility removes setWorkingDir - breaks image generation ligand lite as directories removed!!
        # Cannot cleanup after chemCompAssignOp
        self.__cleanUp = False
        self.__cleanUpSafe = True
        """Flag to remove any temporary directories created by this class.
        """
        #

    def chemCompLinkOp(self, **kwArgs):
        """Performs chemical component linkage calculation on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            ccLinkPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("chem-comp-link")
            dp.exp(ccLinkPath)
            if self.__cleanUpSafe:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompLinkOp() - PDBx XXXXX:    %s\n" % self.__cleanUpSafe)
                self._lfh.write("+ChemCompUtils.chemCompLinkOp() - PDBx file path:    %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompLinkOp() - CC link file path: %s\n" % ccLinkPath)
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False

    def chemCompAssignOp(self, **kwArgs):
        """Performs chemical component assignment calculation on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            depDataSetId = inpObjD["src1"].getDepositionDataSetId()
            #
            ccLinkFilePath = inpObjD["src2"].getFilePathReference()
            #
            ccAssignFilePath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            if (ccLinkFilePath is not None) and os.path.exists(ccLinkFilePath):
                dp.addInput(name="cc_link_file_path", value=ccLinkFilePath, type="file")
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign")
            dp.exp(ccAssignFilePath)
            if self.__cleanUp:
                dp.cleanup()
            #
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC link file path:   %s\n" % ccLinkFilePath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC assign file path: %s\n" % ccAssignFilePath)
            #
            self.__runMetalCoordination(siteId, depDataSetId, outObjD["dst"].getWorkflowInstanceId(), outObjD["dst"].getStorageType(), dirPath, pdbxPath, ccAssignFilePath, False)
            #
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False
        #

    def chemCompAssignUIOp(self, **kwArgs):
        """Performs chemical component assignment calculation on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            depDataSetId = inpObjD["src1"].getDepositionDataSetId()
            #
            ccLinkFilePath = inpObjD["src2"].getFilePathReference()
            #
            ccAssignFilePath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            if (ccLinkFilePath is not None) and os.path.exists(ccLinkFilePath):
                dp.addInput(name="cc_link_file_path", value=ccLinkFilePath, type="file")
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign")
            dp.exp(ccAssignFilePath)
            if self.__cleanUp:
                dp.cleanup()
            #
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC link file path:   %s\n" % ccLinkFilePath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC assign file path: %s\n" % ccAssignFilePath)
            #
            self.__runMetalCoordination(siteId, depDataSetId, outObjD["dst"].getWorkflowInstanceId(), outObjD["dst"].getStorageType(), dirPath, pdbxPath, ccAssignFilePath, True)
            #
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False
        #

    def chemCompAssignNLOp(self, **kwArgs):
        """Performs chemical component assignment calculation on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            #
            ccLinkFilePath = None
            #
            ccAssignPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            if (ccLinkFilePath is not None) and os.path.exists(ccLinkFilePath):
                dp.addInput(name="cc_link_file_path", value=ccLinkFilePath, type="file")
            #
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign")
            dp.exp(ccAssignPath)
            if self.__cleanUp:
                dp.cleanup()
            #
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC assign file path: %s\n" % ccAssignPath)
            #
            self.__runMetalCoordination(siteId, depDataSetId, outObjD["dst"].getWorkflowInstanceId(), outObjD["dst"].getStorageType(), dirPath, pdbxPath, ccAssignPath, False)
            #
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False
        #

    def chemCompAssignNLUIOp(self, **kwArgs):
        """Performs chemical component assignment calculation on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            #
            ccLinkFilePath = None
            #
            ccAssignPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            if (ccLinkFilePath is not None) and os.path.exists(ccLinkFilePath):
                dp.addInput(name="cc_link_file_path", value=ccLinkFilePath, type="file")
            #
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign")
            dp.exp(ccAssignPath)
            if self.__cleanUp:
                dp.cleanup()
            #
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignOp() - CC assign file path: %s\n" % ccAssignPath)
            #
            self.__runMetalCoordination(siteId, depDataSetId, outObjD["dst"].getWorkflowInstanceId(), outObjD["dst"].getStorageType(), dirPath, pdbxPath, ccAssignPath, True)
            #
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False
        #

    def chemCompAssignExactOp(self, **kwArgs):
        """Performs chemical component assignment calculation with exact match option on PDBx format files."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            depDataSetId = inpObjD["src1"].getDepositionDataSetId()
            #
            ccLinkFilePath = inpObjD["src2"].getFilePathReference()
            #
            ccAssignFilePath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            if (ccLinkFilePath is not None) and os.path.exists(ccLinkFilePath):
                dp.addInput(name="cc_link_file_path", value=ccLinkFilePath, type="file")
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign-exact")
            dp.exp(ccAssignFilePath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignExactOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignExactOp() - CC link file path:   %s\n" % ccLinkFilePath)
                self._lfh.write("+ChemCompUtils.chemCompAssignExactOp() - CC assign file path: %s\n" % ccAssignFilePath)
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False

    def chemCompAssignExactNLOp(self, **kwArgs):
        """Performs chemical component assignment calculation with exact match option on PDBx format files.
        This method assumes no link file being provided.
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            #
            ccAssignPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            ccAssignWrkngDirPath = os.path.join(dirPath, "assign")
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setWorkingDir(ccAssignWrkngDirPath)
            dp.addInput(name="id", value=depDataSetId)
            #
            dp.imp(pdbxPath)
            dp.op("chem-comp-assign-exact")
            dp.exp(ccAssignPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompAssignExactNLOp() - PDBx file path:      %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompAssignExactNLOp() - CC assign file path: %s\n" % ccAssignPath)
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False

    def chemCompInstanceUpdateOp(self, **kwArgs):
        """Performs chemical component assignment update operations on PDBx format model files.

        Requires: extra input files for assignment and user selection.
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            #
            ccAssignFilePath = inpObjD["src2"].getFilePathReference()
            #
            outputModelPdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            #
            if (ccAssignFilePath is not None) and os.path.exists(ccAssignFilePath):
                dp.addInput(name="cc_assign_file_path", value=ccAssignFilePath, type="file")
            #
            # if ((ccSelectFilePath is not None)  and  os.path.exists(ccSelectFilePath)):
            #     dp.addInput(name="cc_select_file_path",value=ccSelectFilePath,type='file')
            dp.imp(pdbxPath)
            dp.op("chem-comp-instance-update")
            dp.exp(outputModelPdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+ChemCompUtils.chemCompInstanceUpdateOp() - PDBx file path:          %s\n" % pdbxPath)
                self._lfh.write("+ChemCompUtils.chemCompInstanceUpdateOp() - CC assign file path:     %s\n" % ccAssignFilePath)
                # self._lfh.write("+ChemCompUtils.chemCompInstanceUpdateOp() - CC select file path:     %s\n" % ccSelectFilePath)
                self._lfh.write("+ChemCompUtils.chemCompInstanceUpdateOp() - PDBx output file path:   %s\n" % outputModelPdbxPath)
            return True
        except Exception as _e:  # noqa: F841,BLE001
            traceback.print_exc(file=self._lfh)
            return False

    def __runMetalCoordination(self, siteId, depId, instId, fileSource, dirPath, pdbxPath, ccAssignFilePath, uiFlag):
        """Performs metal coordination calculations with MetalCoord and FindGeo programs on PDBx format input file"""
        if (not ccAssignFilePath) or (not os.access(ccAssignFilePath, os.R_OK)):
            return
        #
        assignReader = IoAdapterCore(verbose=self._verbose, log=self._lfh)
        assignList = assignReader.readFile(inputFilePath=ccAssignFilePath, selectList=["pdbx_entry_info", "pdbx_polyatomic_metal_ccd"], outDirPath=dirPath)
        if len(assignList) == 0:
            return
        #
        polyAtomicMetalCcdList = []
        #
        ccdObj = assignList[0].getObj("pdbx_polyatomic_metal_ccd")
        if ccdObj:
            for rowIdx in range(ccdObj.getRowCount()):
                value = ccdObj.getValue(attributeName="id", rowIndex=rowIdx)
                if (value is None) or (value == ".") or (value == "?"):  # noqa: PLR1714
                    value = ""
                #
                if value != "":
                    polyAtomicMetalCcdList.append(value)
                #
            #
        #
        if len(polyAtomicMetalCcdList) == 0:
            return
        #
        if not uiFlag:
            # for AUTO pass
            infoObj = assignList[0].getObj("pdbx_entry_info")
            if infoObj:
                status = infoObj.getValue(attributeName="status", rowIndex=0)
                if status == "OK":
                    return
                #
            #
            # for timeout
            pdbxReader = IoAdapterCore(verbose=self._verbose, log=self._lfh)
            pdbxList = pdbxReader.readFile(inputFilePath=pdbxPath, selectList=["pdbx_data_processing_status"], outDirPath=dirPath)
            if len(pdbxList) > 0:
                pdbxObj = pdbxList[0].getObj("pdbx_data_processing_status")
                if pdbxObj:
                    found = False
                    for rowIdx in range(pdbxObj.getRowCount()):
                        value = pdbxObj.getValue(attributeName="task_name", rowIndex=rowIdx)
                        if value == "metal coordination":
                            found = True
                            break
                        #
                    #
                    if found:
                        return
                    #
                #
            #
        #
        pI = PathInfo(siteId=siteId, verbose=self._verbose, log=self._lfh)
        findFilePath = pI.getFilePath(depId, wfInstanceId=instId, contentType="findgeo-annotation", formatType="json", fileSource=fileSource, versionId="next")
        metFilePath = pI.getFilePath(depId, wfInstanceId=instId, contentType="metalcoord-annotation", formatType="json", fileSource=fileSource, versionId="next")
        #
        metalUtil = MetalCoordinationUtility(wrkPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
        metalUtil.setModelCoordinatesFilePath(pdbxPath)
        metalUtil.setPolyAtomicMetalLigandIdList(polyAtomicMetalCcdList)
        metalUtil.setFindGeoOutputFilePath(findFilePath)
        metalUtil.setMetalCoordOutputFilePath(metFilePath)
        if not uiFlag:
            metalUtil.run(noTimeOutFlag=False, regularFilter="-filter-regular")
        else:
            metalUtil.run(noTimeOutFlag=True, regularFilter="-filter-regular")
        #

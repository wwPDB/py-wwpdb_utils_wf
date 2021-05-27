#
# File:   SFConvert.py
# Date:   2021-03-01
#
"""
Module to handle dictionary compliant SF files from autoPROC in mmCIF format
"""


import os
import sys

try:
    # We will have present on annotation system - but allow testing of DepUI merge without
    from wwpdb.apps.ann_tasks_v2.expIoUtils.PdbxExpIoUtils import PdbxExpFileIo, PdbxExpIoUtils
except ImportError:
    pass
from mmcif.io.IoAdapterCore import IoAdapterCore


class SFConvert(object):
    def __init__(self, verbose=False, log=sys.stderr):
        self._verbose = verbose
        self._lfh = log

    def isSpecialSF(self, pathIn):
        """Detect if autoPROC sf file uploaded

        Returns True if special handling warranted
        """
        try:
            io = IoAdapterCore()
            # Categories that will trigger special handling.  AUTOProc uses software
            # Used to key off software
            catList = ["pdbx_audit_conform"]

            containerList = io.readFile(pathIn, selectList=catList)

            if containerList is None or len(containerList) < 1:
                return False

            for cat in catList:
                for cl in containerList:
                    if cat in cl.getObjNameList():
                        return True
        except Exception as _e:  # noqa: F841
            pass

        return False

    def handleSpecialSF(self, sfIn, sfOut, modelIn, sfDiagFilePath, logFilePath):

        # Empty log and diagnostic
        with open(sfDiagFilePath, "w") as _fout:  # noqa: F841
            pass
        with open(logFilePath, "w") as _fout:  # noqa: F841
            pass

        # Get pdbid
        pdbId = self.__getmodelPdbId(modelIn)
        if pdbId is None:
            pdbId = "xxxx"

        try:
            sfIo = PdbxExpFileIo(verbose=self._verbose, log=self._lfh)
            containerList = sfIo.getContainerList(sfIn)
            if len(containerList) < 1:
                return False

            sfIo.updateContainerNames(idCode=pdbId, containerList=containerList)
            sfIo.updateEntryIds(idCode=pdbId, containerList=containerList)
            self.__stripAudit(containerList)
            self.__correctGphlAlias(containerList)
            _err = self.__checkErrors(containerList, sfDiagFilePath, logFilePath)  # noqa: F841
            # We always write to avoid complaint about pdbx2pdbx failing
            sfIo.writeContainerList(sfOut, containerList)
            return True
        except Exception as e:
            self._lfh.write("Failed to convert %s\n" % e)

        return False

    def __getmodelPdbId(self, modelIn):
        """Gets pdb id if present"""
        try:
            if modelIn and os.path.exists(modelIn):
                mIo = PdbxExpFileIo(verbose=self._verbose, log=self._lfh)
                modelContainerList = mIo.getContainerList(modelIn)
                if len(modelContainerList) < 1:
                    return None

                mE = PdbxExpIoUtils(dataContainer=modelContainerList[0], verbose=self._verbose, log=self._lfh)
                pdbId = str(mE.getDbCode(dbId="PDB")).lower()

                return pdbId
        except Exception as _e:  # noqa: F841
            pass

        return None

    def __stripAudit(self, cList):
        """Strip out Audit records from uploaded files"""
        for cat in ["audit", "audit_conform"]:
            for container in cList:
                if cat in container.getObjNameList():
                    container.remove(cat)

    def __correctGphlAlias(self, cList):
        """Strip out Audit records from uploaded files"""

        rmappings = {"gphl_signal_type": "pdbx_signal_type", "gphl_observed_signal_threshold": "pdbx_observed_signal_threshold"}

        for container in cList:
            if "reflns" in container.getObjNameList():
                cObj = container.getObj("reflns")
                cObj.renameAttributes(rmappings)

    def __checkErrors(self, cList, sfDiagFilePath, logFilePath):
        """Checks for standard errors in files"""

        errs = []

        if len(cList) < 1:
            errs.append("Error: empty file")

        else:
            # In first datablock, refln category should have at least one of: F/I/F+/F-/I+/I-
            b0 = cList[0]

            if "refln" not in b0.getObjNameList():
                errs.append("Error: missing _refln category in first block")
            else:
                cObj = b0.getObj("refln")
                needAtt = ["F_meas_au", "F_meas", "intensity_meas", "intensity_meas_au", "F_squared_meas", "pdbx_I_plus", "pdbx_I_minus", "pdbx_F_plus", "pdbx_F_minus"]
                found = False
                for att in needAtt:
                    if att in cObj.getAttributeList():
                        found = True
                if not found:
                    errs.append("Error: SF file missing mandatory items 'F/I/F+/F-/I+/I-'")

            # Check all datablocks to ensure none have both merged and unmerged data
            for bl in cList:
                names = bl.getObjNameList()
                if "refln" in names and "diffrn_refln" in names:
                    errs.append("Error: cannot have _refln and _diffrn_refln categories in same data block")

        if len(errs) > 0:
            # sfDiagFilePath, logFilePath):
            with open(sfDiagFilePath, "a") as fOut:
                for e in errs:
                    fOut.write("%s\n" % e)

            with open(logFilePath, "a") as fOut:
                for e in errs:
                    fOut.write("%s\n" % e)

            return True

        return False

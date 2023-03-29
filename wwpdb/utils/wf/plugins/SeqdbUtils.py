##
# File:    SeqdbUtils.py
# Date:    25-April-2010
#
# Updates:
#    22-Mar-2013 jdw overhaul for version 2 sequence module
#    22-Mar-2013 jdw provide matchAppOp() to search all relevant entities in a single method.
#    25-Mar-2013 jdw respect the destination setting when returning files in match-all
#    20-Apr-2014 jdw add additional export of polymer linkage report
#    22-May-2014 jdw add perform and store alignments with default selections
##
"""
Module of sequence database search utilities.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback
from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase

try:
    # We will have present on annotation system - but allow testing
    from wwpdb.apps.seqmodule.webapp.SeqModWebRequest import SeqModInputRequest
except ImportError:
    pass

try:
    # We will have present on annotation system - but allow testing
    from wwpdb.apps.seqmodule.control.DataImporter import DataImporter
except ImportError:
    pass

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class SeqdbUtils(UtilsBase):
    """Utility class to perform sequence database searches.

    Current supported operations include:
    - find matching sequences for all polymer entities in a model file
    - find matching sequences of a specific polymer identified by entity_id

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
        super(SeqdbUtils, self).__init__(verbose, log)
        self.__cleanUp = False
        """Flag to remove any temporary directories created by this class.
        """
        # Init here to keep pylint happy
        self.__maxRefAlign = 0
        self.__siteId = None
        self.__reqObj = None
        # self.__sessionId = None
        # self.__sessionObj = None
        # self.__sessionPath = None
        self.__doAutoProcessFlag = False
        self.__includeSeqAssignFileFlag = False
        #

    def mySetup(self, topSessionPath="."):
        """Setup application environment for managing session storage of
        temporally data files.
        """
        self.__maxRefAlign = 100
        self.__siteId = getSiteId(defaultSiteId="WWPDB_DEPOLY_TEST")
        #
        self.__reqObj = SeqModInputRequest({}, verbose=self._verbose, log=self._lfh)
        self.__reqObj.setValue("TopSessionPath", topSessionPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)
        #
        #  self.__sessionId = self.__reqObj.getSessionId()
        # The following has side effects
        _sessionObj = self.__reqObj.newSessionObj()  # noqa: F841
        #  self.__sessionPath = self.__sessionObj.getPath()

    def matchAllOp(self, **kwArgs):
        """Find matching sequences for all entities."""
        try:
            self.__doAutoProcessFlag = False
            self.__includeSeqAssignFileFlag = False
            self.__runMatchAllOp(kwArgs, "matchAllOp")
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False
        #

    def matchAllAutoOp(self, **kwArgs):
        """Find matching sequences for all entities."""
        try:
            self.__doAutoProcessFlag = True
            self.__includeSeqAssignFileFlag = True
            self.__runMatchAllOp(kwArgs, "matchAllAutoOp")
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False
        #

    def matchEntityOp(self, **kwArgs):
        """Find matching sequences for all entities."""
        try:
            (inpObjD, outObjD, uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            dstPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            entityId = str(uD["entity_id"])
            #
            # details of the input file -
            #
            depDataSetId = inpObjD["src"].getDepositionDataSetId()
            instanceId = inpObjD["src"].getWorkflowInstanceId()
            fileSource = inpObjD["src"].getStorageType()
            #
            self.mySetup(topSessionPath=dirPath)
            self.__reqObj.setValue("identifier", depDataSetId)
            self.__reqObj.setValue("instance", instanceId)
            #
            dI = DataImporter(reqObj=self.__reqObj, fileSource=fileSource, maxRefAlign=self.__maxRefAlign, verbose=self._verbose, log=self._lfh)
            dI.copyModelFile(inputFileSource=fileSource, inputWfInstanceId=instanceId)
            dI.copyFiles(messageHead="SeqdbUtils.matchAllOp(OnStart)")
            entityIdList, ok = dI.loadSeqDataAssemble(selectedEntityIdList=[entityId], doRefSearch=True)
            #
            # Return the files according to the destination setting --
            #
            instanceId = outObjD["dst"].getWorkflowInstanceId()
            fileSource = outObjD["dst"].getStorageType()
            dI.copyFiles(
                inputFileSource="session",
                outputFileSource=fileSource,
                outputWfInstanceId=instanceId,
                versionIndex=4,
                includePolyLinkFile=True,
                entityIdList=entityIdList,
                messageHead="SeqdbUtils.matchEntityOp(OnFinish)",
            )
            #
            if self._verbose:
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Input model PDBx file path: %s\n" % pdbxPath)
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Entity id : %s\n" % entityId)
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Output result path: %s\n" % dstPath)
            #
            if self.__cleanUp:
                pass
            #
            return ok
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def updateModelWithSeqAssignmentOp(self, **kwArgs):
        """Performs sequence assignment update operation on PDBx format model file."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src1"].getFilePathReference()
            depDataSetId = inpObjD["src1"].getDepositionDataSetId()
            instanceId = inpObjD["src1"].getWorkflowInstanceId()
            fileSource = inpObjD["src1"].getStorageType()
            #
            seqAssignFilePath = inpObjD["src2"].getFilePathReference()
            #
            outputModelPdbxPath = outObjD["dst"].getFilePathReference()
            dirPath = outObjD["dst"].getDirPathReference()
            #
            self.mySetup(topSessionPath=dirPath)
            self.__reqObj.setValue("identifier", depDataSetId)
            self.__reqObj.setValue("instance", instanceId)
            #
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=self.__siteId, verbose=self._verbose, log=self._lfh)
            #
            if (seqAssignFilePath is not None) and os.path.exists(seqAssignFilePath):
                dp.addInput(name="seqmod_assign_file_path", value=seqAssignFilePath, type="file")
            #
            dp.imp(pdbxPath)
            dp.op("annot-merge-sequence-data")
            dp.exp(outputModelPdbxPath)
            if self.__cleanUp:
                dp.cleanup()
            if self._verbose:
                self._lfh.write("+SeqdbUtils.updateModelWithSeqAssignmentOp() - PDBx file path:        %s\n" % pdbxPath)
                self._lfh.write("+SeqdbUtils.updateModelWithSeqAssignmentOp() - Seq assign file path:  %s\n" % seqAssignFilePath)
                self._lfh.write("+SeqdbUtils.updateModelWithSeqAssignmentOp() - PDBx output file path: %s\n" % outputModelPdbxPath)
            #
            # Copy files back to archive
            #
            dI = DataImporter(reqObj=self.__reqObj, fileSource=fileSource, maxRefAlign=self.__maxRefAlign, verbose=self._verbose, log=self._lfh)
            dI.copyModelFile(inputFileSource=fileSource, inputWfInstanceId=instanceId, outputFileSource="archive", versionIndex=4)
            dI.copyFiles(
                inputFileSource=fileSource,
                inputWfInstanceId=instanceId,
                outputFileSource="archive",
                versionIndex=4,
                includePolyLinkFile=True,
                includeSeqAssignFile=True,
                messageHead="SeqdbUtils.updateModelWithSeqAssignmentOp(OnFinish)",
            )
            #
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False
        #

    def __runMatchAllOp(self, kwArgs, functionName):
        """Find matching sequences for all entities."""
        (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
        pdbxPath = inpObjD["src"].getFilePathReference()
        dirPath = outObjD["dst"].getDirPathReference()
        #
        # details of the input file -
        #
        depDataSetId = inpObjD["src"].getDepositionDataSetId()
        instanceId = inpObjD["src"].getWorkflowInstanceId()
        fileSource = inpObjD["src"].getStorageType()
        #
        self.mySetup(topSessionPath=dirPath)
        self.__reqObj.setValue("identifier", depDataSetId)
        self.__reqObj.setValue("instance", instanceId)
        #
        # Do all the work here
        #
        dI = DataImporter(reqObj=self.__reqObj, fileSource=fileSource, maxRefAlign=self.__maxRefAlign, verbose=self._verbose, log=self._lfh)
        dI.copyModelFile(inputFileSource=fileSource, inputWfInstanceId=instanceId)
        dI.copyFiles(messageHead="SeqdbUtils." + functionName + "(OnStart)")
        entityIdList, _ok = dI.loadSeqDataAssemble(doAutoProcess=self.__doAutoProcessFlag)
        #
        # Return the files according to the destination setting --
        #
        instanceId = outObjD["dst"].getWorkflowInstanceId()
        fileSource = outObjD["dst"].getStorageType()
        dI.copyFiles(
            inputFileSource="session",
            outputFileSource=fileSource,
            outputWfInstanceId=instanceId,
            versionIndex=4,
            includePolyLinkFile=True,
            includeSeqAssignFile=self.__includeSeqAssignFileFlag,
            entityIdList=entityIdList,
            messageHead="SeqdbUtils." + functionName + "(OnFinish)",
        )
        #
        if self._verbose:
            self._lfh.write("+SeqdbUtils.matchAllOp() - Input model PDBx file path: %s\n" % pdbxPath)
            self._lfh.write("+SeqdbUtils.matchAllOp() - Output dir path: %s\n" % dirPath)
        #

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
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import  os,sys,traceback
from wwpdb.utils.config.ConfigInfo                        import getSiteId
from wwpdb.utils.wf.plugins.UtilsBase                        import UtilsBase
from wwpdb.apps.seqmodule.webapp.SeqModWebRequest       import SeqModInputRequest
from wwpdb.apps.seqmodule.control.DataImporter          import DataImporter

class SeqdbUtils(UtilsBase):
    """ Utility class to perform sequence database searches.

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
    def __init__(self, verbose=True,log=sys.stderr):
        super(SeqdbUtils,self).__init__(verbose,log)
        self.__cleanUp=False
        """Flag to remove any temporary directories created by this class.
        """

        #

    def mySetup(self,topSessionPath='.'):
        """  Setup application environment for managing session storage of
             temporaty data files.
        """
        self.__maxRefAlign=100
        self.__siteId=getSiteId(defaultSiteId="WWPDB_DEPOLY_TEST")
        #
        self.__reqObj=SeqModInputRequest({},verbose=self._verbose,log=self._lfh)
        self.__reqObj.setValue("TopSessionPath", topSessionPath)
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)

        self.__sessionId = self.__reqObj.getSessionId()
        self.__sessionObj=self.__reqObj.newSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()

    def matchAllOp(self,**kwArgs):
        """Find matching sequences for all entities.
        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)
            pdbxPath =inpObjD["src"].getFilePathReference()
            dstPath  =outObjD["dst"].getFilePathReference()
            dirPath  =outObjD["dst"].getDirPathReference()
            #
            # details of the input file -
            #
            depDataSetId       =inpObjD["src"].getDepositionDataSetId()
            instanceId         =inpObjD["src"].getWorkflowInstanceId()
            fileSource         =inpObjD["src"].getStorageType()
            #
            self.mySetup(topSessionPath=dirPath)
            self.__reqObj.setValue("identifier",depDataSetId)
            self.__reqObj.setValue("instance",instanceId)
            #
            # Do all the work here
            #
            dI = DataImporter(reqObj=self.__reqObj,fileSource=fileSource,maxRefAlign=self.__maxRefAlign,verbose=self._verbose,log=self._lfh)
            dI.copyModelFile(inputFileSource=fileSource, inputWfInstanceId=instanceId)
            dI.copyFiles(messageHead="SeqdbUtils.matchAllOp(OnStart)")
            entityIdList,ok = dI.loadSeqDataAssemble()
            #
            # Return the files according to the destination setting --
            #
            instanceId         =outObjD["dst"].getWorkflowInstanceId()
            fileSource         =outObjD["dst"].getStorageType()
            dI.copyFiles(inputFileSource="session", outputFileSource=fileSource, outputWfInstanceId=instanceId, versionIndex=4, \
                         includePolyLinkFile=True, entityIdList=entityIdList, messageHead="SeqdbUtils.matchAllOp(OnFinish)")
            #
            if (self._verbose):
                self._lfh.write("+SeqdbUtils.matchAllOp() - Input model PDBx file path: %s\n" % pdbxPath)
                self._lfh.write("+SeqdbUtils.matchAllOp() - Output dir path: %s\n" % dirPath)
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def matchEntityOp(self,**kwArgs):
        """Find matching sequences for all entities.
        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)
            pdbxPath =inpObjD["src"].getFilePathReference()
            dstPath =outObjD["dst"].getFilePathReference()
            dirPath  =outObjD["dst"].getDirPathReference()
            entityId=str(uD['entity_id'])
            #
            # details of the input file -
            #
            depDataSetId       =inpObjD["src"].getDepositionDataSetId()
            instanceId         =inpObjD["src"].getWorkflowInstanceId()
            fileSource         =inpObjD["src"].getStorageType()
            #
            self.mySetup(topSessionPath=dirPath)
            self.__reqObj.setValue("identifier",depDataSetId)
            self.__reqObj.setValue("instance",instanceId)
            #
            dI = DataImporter(reqObj=self.__reqObj,fileSource=fileSource,maxRefAlign=self.__maxRefAlign,verbose=self._verbose,log=self._lfh)
            dI.copyModelFile(inputFileSource=fileSource, inputWfInstanceId=instanceId)
            dI.copyFiles(messageHead="SeqdbUtils.matchAllOp(OnStart)")
            entityIdList,ok = dI.loadSeqDataAssemble(selectedEntityIdList=[entityId], doRefSearch=True)
            #
            # Return the files according to the destination setting --
            #
            instanceId         =outObjD["dst"].getWorkflowInstanceId()
            fileSource         =outObjD["dst"].getStorageType()
            dI.copyFiles(inputFileSource="session", outputFileSource=fileSource, outputWfInstanceId=instanceId, versionIndex=4, \
                         includePolyLinkFile=True, entityIdList=entityIdList, messageHead="SeqdbUtils.matchAllOp(OnFinish)")
            #
            if (self._verbose):
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Input model PDBx file path: %s\n" % pdbxPath)
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Entity id : %s\n" % entityId)
                self._lfh.write("+SeqdbUtils.matchEntityOp() - Output result path: %s\n" % dstPath)
            #

            if (self.__cleanUp):
                pass
            return ok
        except:
            traceback.print_exc(file=self._lfh)
            return False
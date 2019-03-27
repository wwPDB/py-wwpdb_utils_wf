##
# File:    PrdSearchUtils.py
# Date:    10-Sept-2010
#
# Updates:
# 2013-03-15    ZF   Explicitly setting name of working directory used during calls for "prd-search" processing.
##
""" 
Module of entity transformer utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import  os,sys,traceback
import shutil,datetime,time,difflib
#from wwpdb.apps.entity_transform.depict.ProcessPrdSummary import ProcessPrdSummary
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfo import ConfigInfo
#from wwpdb.utils.session.WebRequest import InputRequest
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

class PrdSearchUtils(UtilsBase):
    """ Utility class to perform PRD search operation.

        The method in this class implements the method calling interface of the 
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParameterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        The method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """
    def __init__(self, verbose=False,log=sys.stderr):
        super(PrdSearchUtils,self).__init__(verbose,log)
        self.__cleanUp=False
        """Flag to remove any temporary directories created by this class.
        """
        #

    def PrdSearchOp(self,**kwArgs):
        """Performs PRD search on PDBx format files.
        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)
            pdbxPath       = inpObjD["src"].getFilePathReference()
            dirPath        = outObjD["dst"].getDirPathReference()
            resultFilePath = outObjD["dst"].getFilePathReference()
            #
            WorkingDirPath = os.path.join(dirPath, 'search')  
            firstModelPath = os.path.join(WorkingDirPath, 'firstmodel.cif')
            logFilePath    = os.path.join(WorkingDirPath, 'search-prd.log')
            #
            cI=ConfigInfo()
            siteId=cI.get("SITE_PREFIX")            
            dp=RcsbDpUtility(tmpPath=dirPath,siteId=siteId,verbose=self._verbose,log=self._lfh)
            dp.setWorkingDir(WorkingDirPath)
            dp.addInput(name='firstmodel', value=firstModelPath)
            dp.addInput(name='logfile', value=logFilePath)
            dp.imp(pdbxPath)
            dp.op("prd-search")
            dp.exp(resultFilePath)
            if (self.__cleanUp): dp.cleanup()            
            if not os.access(resultFilePath, os.R_OK):
                return False
            # 
            logFilePath = os.path.join(WorkingDirPath, 'process-prd.log')
            dp1 = RcsbDpUtility(tmpPath=dirPath,siteId=siteId,verbose=self._verbose,log=self._lfh)
            dp1.addInput(name='resultFile', value=resultFilePath)
            dp1.addInput(name='logfile', value=logFilePath)
            dp1.op("prd-process-summary")
            if (self.__cleanUp): dp1.cleanup()
            """
            myReqObj = InputRequest({}, verbose=self._verbose, log=self._lfh)
            myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
            myReqObj.setValue("TopPath", cI.get('SITE_WEB_APPS_TOP_PATH'))
            myReqObj.setValue("WWPDB_SITE_ID",  siteId)
            prdUtil = ProcessPrdSummary(reqObj=myReqObj, verbose=self._verbose, log=self._lfh)
            prdUtil.setTopDirPath(dirPath)
            prdUtil.setPrdSummaryFile(resultFilePath)
            prdUtil.run()
            #
            """
            return True
        except:
            traceback.print_exc(file=self._lfh)            
            return False

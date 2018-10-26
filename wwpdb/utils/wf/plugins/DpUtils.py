##
# File:    DpUtils.py
# Date:    23-April-2010
#
# Updates:
#
##
""" 
Module of data processing utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.01"

import  os,sys,traceback
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility

class DpUtils(UtilsBase):
    """ Utility class to perform data processing operations.

        Current supported operations include:
        - polymer linkage distances 
        
        Each method in this class implements the method calling interface of the 
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParameterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        Each method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """
    def __init__(self, verbose=False,log=sys.stderr):
        super(DpUtils,self).__init__(verbose,log)
        self.__cleanUp=False
        """Flag to remove any temporary directories created by this class.
        """
        #

    def polymerLinkageDistanceOp(self,**kwArgs):
        """Calculate polymer linkage distances -
        """
        try:
            (inpObjD,outObjD,uD,pD)=self._getArgs(kwArgs)
            pdbxPath=inpObjD["src"].getFilePathReference()
            distPath =outObjD["dst"].getFilePathReference()
            dirPath =outObjD["dst"].getDirPathReference()            
            #
            cI=ConfigInfo()
            siteId=cI.get("SITE_PREFIX")
            tmpPath=cI.get("SITE_TMP_DIR")
            dp=RcsbDpUtility(tmpPath=tmpPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(pdbxPath)
            dp.op("annot-poly-link-dist")
            dp.exp(distPath)
            if (self.__cleanUp): dp.cleanup()            
            if (self._verbose):
                self._lfh.write("+DpUtils.polymerLinkageDistanceOp() - PDBx     file path: %s\n" % pdbxPath)
                self._lfh.write("+DpUtils.polymerLinkageDistanceOp() - Distance file path: %s\n" % distPath)                                
            return True
        except:
            traceback.print_exc(file=self._lfh)            
            return False

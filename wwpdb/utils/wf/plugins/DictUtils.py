##
# File:    DictUtils.py
# Date:    21-July-2015
#
# Updates:
#
##
"""
Module of extension dictionary translation operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppEm
from mmcif_utils.trans.InstanceMapper import InstanceMapper


class DictUtils(UtilsBase):

    """Utility class to perform extension dictionary content conversions.

    Current supported operations include:
    - cnv-em2emd   PDBx EM dialect to EMD dialect.
    - cnv-emd2em   EMD dialect to PDBx EM dialect

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
        super(DictUtils, self).__init__(verbose, log)

    def em2emdOp(self, **kwArgs):
        """Convert PDBx EM dialect to EMD dialect."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            #
            dstPath = outObjD["dst"].getFilePathReference()
            #
            cIA = ConfigInfoAppEm()
            mappingInfoPath = cIA.get_emd_mapping_file_path()

            #
            im = InstanceMapper(verbose=self._verbose, log=self._lfh)
            im.setMappingFilePath(mappingInfoPath)
            ok = im.translate(pdbxPath, dstPath, mode="src-dst")
            self._lfh.write("+DictUtils em2emdOp return status %r \n" % ok)
            #
            if self._verbose:
                self._lfh.write("+DictUtils.em2emdOp() - Input model PDBx file path: %s\n" % pdbxPath)
                self._lfh.write("+DictUtils.em2emdOp() - Output result path: %s\n" % dstPath)
            #
            return ok
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

    def emd2emOp(self, **kwArgs):
        """Convert EMD dialect to PDBx EM dialect."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            pdbxPath = inpObjD["src"].getFilePathReference()
            #
            dstPath = outObjD["dst"].getFilePathReference()
            #
            cIA = ConfigInfoAppEm()
            mappingInfoPath = cIA.get_emd_mapping_file_path()

            #
            im = InstanceMapper(verbose=self._verbose, log=self._lfh)
            im.setMappingFilePath(mappingInfoPath)
            ok = im.translate(pdbxPath, dstPath, mode="dst-src")
            self._lfh.write("+DictUtils emd2emOp return status %r \n" % ok)
            #
            if self._verbose:
                self._lfh.write("+DictUtils.emd2emOp() - Input model PDBx file path: %s\n" % pdbxPath)
                self._lfh.write("+DictUtils.emd2emOp() - Output result path: %s\n" % dstPath)
            #
            return ok
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

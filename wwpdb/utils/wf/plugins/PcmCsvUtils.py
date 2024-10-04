##
# File:    PcmCsvUtils.py
# Date:    03-Oct-2024
#
# Updates:
#
##
"""
Module of annotation utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os,sys
import traceback
from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase


class PcmCsvUtils(UtilsBase):

    """Utility class to check "pcm-missing-data" csv file has missing data information.

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
        super(PcmCsvUtils, self).__init__(verbose, log)

    def missingPcmDataOp(self, **kwArgs):
        """Merges the first datablock from src1 and selected categories in
        src2 and output to dst1. Will not overwrite if present
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwArgs)
            srcPath = inpObjD["src"].getFilePathReference()
            outPath = outObjD["dst"].getFilePathReference()
            #
            yes_no_value = "NO"
            if os.access(srcPath, os.R_OK):
                ifh = open(srcPath, "r")
                data = ifh.read()
                ifh.close()
                #
                title = "Comp_id,Modified_residue_id,Type,Category,Position,Polypeptide_position,Comp_id_linking_atom,Modified_residue_id_linking_atom,First_instance_model_db_code"
                if data.startswith(title):
                    yes_no_value = "YES"
                #
            #
            if outObjD["dst"].getContainerTypeName() == "value":
                outObjD["dst"].setValue(yes_no_value)
            elif outObjD["dst"].getContainerTypeName() == "list":
                outObjD["dst"].setValue([yes_no_value])
            else:
                return False
            #
            return True
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=self._lfh)
            return False

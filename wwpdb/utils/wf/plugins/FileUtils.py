##
# File:    FileUtils.py
# Date:    6-April-2010
#
# Updates:
#
##
"""
Module of file utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback
import shutil
import datetime
import difflib
import json

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.wf.WfDataObject import WfDataObject
from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner
#


class FileUtils(UtilsBase):

    """Utility class of simple file operations.

    Current supported operations include:
    - copy
    - make directory
    - get size
    - get modification datetime
    - contextual difference

    Each method in this class implements the method calling interface of the
    `ProcessRunner()` class.   This interface provides the keyword arguments:

    - inputObjectD   dictionary of input objects
    - outputObjectD  dictionary of output objects
    - userParmeterD  dictionary of user adjustable parameters
    - internalParameterD dictionary of internal parameters

    Each method in the class handles its own exceptions and returns
    True on success or False otherwise.

    """

    def __init__(self, verbose=False, log=sys.stderr):
        super(FileUtils, self).__init__(verbose, log)

    def copyOp(self, **kwargs):
        """Copy operation the file reference from the input object ('src') to the
        file reference in the output object ('dst')
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwargs)
            iPth = inpObjD["src"].getFilePathReference()
            oPth = outObjD["dst"].getFilePathReference()
            if self._verbose:
                self._lfh.write("+FileUtils.copyOp Input  path %s\n" % iPth)
                self._lfh.write("+FileUtils.copyOp Output path %s\n" % oPth)
            shutil.copyfile(iPth, oPth)
            return True
        except Exception as _e:  # noqa: F841
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

    def copyIfExistsOp(self, **kwargs):
        """Copy operation the file reference from the input object ('src') to the
        file reference in the output object ('dst')

        Test for 'src' file existence  -- always return true -
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwargs)
            iPth = inpObjD["src"].getFilePathReference()
            oPth = outObjD["dst"].getFilePathReference()
            if self._verbose:
                self._lfh.write("+FileUtils.copyIfExistsOp Input  path %s\n" % iPth)
                self._lfh.write("+FileUtils.copyIfExistsOp Output path %s\n" % oPth)
            if os.access(iPth, os.R_OK):
                shutil.copyfile(iPth, oPth)
            return True
        except Exception as _e:  # noqa: F841
            # if (self._verbose): traceback.print_exc(file=self._lfh)
            return True

    def makeDirOp(self, **kwargs):
        """Create the directory path for the file reference in the input object ('src').
        Set the mode of the directory according to the value of *mode*.

        Returns:

        True for success or False otherwise.

        """
        try:
            (inpObjD, _outObjD, uD, _pD) = self._getArgs(kwargs)
            newPth = inpObjD["src"].getDirPathReference()
            if not os.path.exists(newPth):
                modeS = uD["mode"]
                modeO = int(modeS, 8)
                os.makedirs(newPth, modeO)
            return True
        except Exception as _e:  # noqa: F841
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

    def sizeOfOp(self, **kwargs):
        """Determine the input file ('src') size in bytes and store this value in the
        output object ('dst')

        Returns:

        True on success or False otherwise
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwargs)
            newPth = inpObjD["src"].getFilePathReference()
            if os.path.exists(newPth):
                nBytes = os.path.getsize(newPth)
                outObjD["dst"].setValue(nBytes)
                return True
            else:
                outObjD["dst"].setValue(0)
                return False
        except Exception as _e:  # noqa: F841
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

    def mtimeOp(self, **kwargs):
        """Determine the input file ('src') modification time and store this value in the output object ('dst')."""
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwargs)
            newPth = inpObjD["src"].getFilePathReference()
            if os.path.exists(newPth):
                tSec = os.path.getmtime(newPth)
                dt = datetime.datetime.fromtimestamp(tSec)
                outObjD["dst"].setValue(dt)
                return True
            else:
                return False
        except Exception as _e:  # noqa: F841
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

    def diffOp(self, **kwargs):
        """Difference the file references from the input objects ('src1' and 'src2')
        and store the line based difference in the output object ('dst')
        """
        try:
            (inpObjD, outObjD, _uD, _pD) = self._getArgs(kwargs)
            iPth1 = inpObjD["src1"].getFilePathReference()
            iPth2 = inpObjD["src2"].getFilePathReference()
            if self._verbose:
                self._lfh.write("+FileUtils.diffOp Input  path 1 %s\n" % iPth1)
                self._lfh.write("+FileUtils.diffOp Input  path 2 %s\n" % iPth2)

            ifh = open(iPth1, "r")
            aL1 = ifh.readlines()
            ifh.close()

            ifh = open(iPth2, "r")
            aL2 = ifh.readlines()
            ifh.close()
            oL = difflib.context_diff(aL1, aL2, "src1", "src2")
            outObjD["dst"].setValue(oL)
            return True
        except Exception as _e:  # noqa: F841
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False
    
    def batchCopyOp(self, **kwargs):
        """
        Perform batch copy operations as specified in a config file.
        Expects:
            - inputObjectD["src"]: file object for the config file (JSON)
            - userParameterD["depID"]: deposition ID
        """
        try:    
            (inpObjD, _outObjD, uD, _pD) = self._getArgs(kwargs)
            config_file_obj = inpObjD["src"].getFilePathReference()
    
            if self._verbose:
                self._lfh.write(f"+FileUtils.batchCopyOp Config file: {config_file_obj}\n")
    
            with open(config_file_obj, "r", encoding="utf-8") as fIn:
                config = json.load(fIn)
                if self._verbose:
                    self._lfh.write(f"+FileUtils.batchCopyOp Loaded config: {config}\n")
                depID = config.get("deposition-id")
                pending_archive_copy_instructions = config.get("copy-instructions", [])
                if self._verbose:
                    self._lfh.write(f"+FileUtils.batchCopyOp Instructions: {pending_archive_copy_instructions}\n")
    
            for op, spec in pending_archive_copy_instructions:
                if op != "copy":
                    continue
                try:
                    src = spec["src"]
                    dst = spec["dst"]
    
                    fin = WfDataObject()
                    fin.setDepositionDataSetId(depID)
                    fin.setWorkflowInstanceId("W_001")
                    fin.setStorageType(src["location"])
                    if src.get("milestone"):
                        fin.setContentTypeAndFormat(src["content"] + '-' + src["milestone"], src["format"])
                    else:
                        fin.setContentTypeAndFormat(src["content"], src["format"])
                    fin.setVersionId(src["version"])
                    fin.setPartitionNumber(src["partno"])
    
                    fout = WfDataObject()
                    fout.setDepositionDataSetId(depID)
                    fout.setWorkflowInstanceId("W_001")
                    fout.setStorageType(dst["location"])
                    if dst.get("milestone"):
                        fout.setContentTypeAndFormat(dst["content"] + '-' + dst["milestone"], dst["format"])
                    else:
                        fout.setContentTypeAndFormat(dst["content"], dst["format"])
                    fout.setVersionId(dst["version"])
                    fout.setPartitionNumber(dst["partno"])
    
                    pR = ProcessRunner(verbose=self._verbose, log=self._lfh)
                    pR.setInput("src", fin)
                    pR.setOutput("dst", fout)
                    ok = pR.setAction(op)
                    if self._verbose:
                        self._lfh.write(f"+FileUtils.batchCopyOp setAction() for {op_name} returns status {ok}\n")
                    ok = pR.preCheck()
                    if self._verbose:
                        self._lfh.write(f"+FileUtils.batchCopyOp preCheck() for {op_name} returns status {ok}\n")
                    ok = pR.run()
                    if self._verbose:
                        self._lfh.write(f"+FileUtils.batchCopyOp run() for {op_name} returns status {ok}\n")
    
                except Exception as e:
                    if self._verbose:
                        self._lfh.write(f"+FileUtils.batchCopyOp Failed copy operation for spec: {spec}\n")
                        traceback.print_exc(file=self._lfh)
            return True
        except Exception as _e:
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

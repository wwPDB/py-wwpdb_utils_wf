##
# File:    ProcessRunner.py
# Date:    1-April-2010
#
# Updates:
# 01-May-2010 jdw add getParameterDict() method and add adjust return values in setParamterDict()
#
##
"""
Classes for accessing  definition of actions/processes, the assignment of data inputs, data outputs,
and process invocation/execution.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback

#
from wwpdb.utils.wf.process.ActionRegistry import ActionRegistry


class ProcessRunner(object):

    """Provide access to action/process definitions, assign data inputs and outputs,
    and manage invocation/execution of processes.

    """

    def __init__(self, verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        self.__actionId = None
        self.__userParameterD = {}
        self.__inputD = {}
        self.__outputD = {}
        self.__aReg = ActionRegistry()

    def setInput(self, name, wfDataObject):
        """Set the input data object identified by the input name.

        Returns:

        True on success or false otherwise.
        """
        try:
            self.__inputD[str(name)] = wfDataObject
            return True
        except Exception as _e:  # noqa: F841
            return False

    def setOutput(self, name, wfDataObject):
        """Set the output data object identified by the input name.

        Returns:

        True on success or false otherwise.
        """
        try:
            self.__outputD[str(name)] = wfDataObject
            return True
        except Exception as _e:  # noqa: F841
            return False

    def setAction(self, actionId):
        """Set the name for this action.  The input action identifier should correspond
        to a action defined in the action registry in class `ActionRegistry`.

        Returns:

        True on success or false otherwise.
        """
        self.__actionId = actionId
        if self.__aReg.isDefinedAction(self.__actionId):
            self.__setParameterDictDefault()
            return True
        else:
            return False

    def __setParameterDictDefault(self):
        """Copy the default user adjustable parameters from the action definition
        to a local dictionary.
        """
        self.__userParameterD = {}
        try:
            dd = self.__aReg.getUserParameterDict(self.__actionId)
            for k, v in dd.items():
                self.__userParameterD[k] = v

        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=sys.stderr)
            return False

        return True

    def getParameterDict(self):
        return self.__userParameterD

    def setParameterDict(self, pD):
        """Copy values for input parameters corresponding to any user adjustable
        parameters for the current action.

        Returns:

        True on success or false otherwise.
        """
        self.__userParameterD = {}
        try:
            for k, v in self.__aReg.getUserParameterDict(self.__actionId).items():

                if k in pD:
                    if self.__verbose:
                        self.__lfh.write("+ProcessRunner.setParameterDict() setting parameter %s to %r\n" % (k, pD[k]))
                    self.__userParameterD[k] = pD[k]
                else:
                    if self.__verbose:
                        self.__lfh.write("+ProcessRunner.setParameterDict() using default setting for parameter %s = %r\n" % (k, v))
                    self.__userParameterD[k] = v

            if self.__verbose:
                self.__lfh.write("+ProcessRunner.setParameterDict() parameter settings:\n")
                for k, v in self.getParameterDict().items():
                    self.__lfh.write("+ProcessRunner.setParameterDict() parameter %s = %r\n" % (k, v))
        except Exception as _e:  # noqa: F841
            traceback.print_exc(file=sys.stderr)
            return False

        return True

    def preCheck(self):
        """Check that input and output data objects are consistent with the type requirements
        for the specified action.

        Returns:

        True if requirements are satisfied or False otherwise.

        """

        if not self.__aReg.isDefinedAction(self.__actionId):
            self.__lfh.write("preCheck : not a valid action  %s\n" % self.__actionId)
            return False

        if self.__debug:
            self.__lfh.write("preCheck for action %s\n" % self.__actionId)

        numInp = self.__aReg.getInputObjectCount(self.__actionId)
        # number of inputs consistent?
        if numInp != len(self.__inputD):
            if self.__verbose:
                self.__lfh.write("Failed input count\n")
            return False
        #
        # input types consistent?
        if numInp > 0:
            for iN in self.__aReg.getInputObjectNames(self.__actionId):
                if self.__aReg.isSetInputReferenceType(self.__actionId, iN):
                    if self.__aReg.getInputReferenceType(self.__actionId, iN) != self.__inputD[iN].getReferenceType():
                        if self.__verbose:
                            self.__lfh.write("Failed input reference type %s\n" % iN)
                        return False
                if self.__aReg.isSetInputContainerType(self.__actionId, iN):
                    if self.__aReg.getInputContainerType(self.__actionId, iN) != self.__inputD[iN].getContainerTypeName():
                        if self.__verbose:
                            self.__lfh.write("Failed input container type %s\n" % iN)
                        return False
                if self.__aReg.isSetInputValueType(self.__actionId, iN):
                    if self.__aReg.getInputValueType(self.__actionId, iN) != self.__inputD[iN].getValueTypeName():
                        if self.__verbose:
                            self.__lfh.write("Failed input value type %s\n" % iN)
                        return False
                if self.__aReg.isSetInputSelectorType(self.__actionId, iN):
                    if self.__aReg.getInputSelectorType(self.__actionId, iN) != self.__inputD[iN].getSelectorType():
                        if self.__verbose:
                            self.__lfh.write("Failed input selector type %s registered as %s \n" % (iN, self.__aReg.getInputSelectorType(self.__actionId, iN)))
                        return False

                if self.__aReg.isSetInputContentType(self.__actionId, iN):
                    if self.__aReg.getInputContentType(self.__actionId, iN) != self.__inputD[iN].getContentType():
                        if self.__verbose:
                            self.__lfh.write(
                                "Failed input content type %s - %s:%s\n" % (iN, self.__aReg.getInputContentType(self.__actionId, iN), self.__inputD[iN].getContentType())
                            )
                        return False

                if self.__aReg.isSetInputFileFormat(self.__actionId, iN):
                    if self.__aReg.getInputFileFormat(self.__actionId, iN) != self.__inputD[iN].getFileFormat():
                        if self.__verbose:
                            self.__lfh.write("Failed input file format %s \n" % iN)
                        return False

        #
        numOut = self.__aReg.getOutputObjectCount(self.__actionId)
        # number of outputs consistent?
        if numOut != len(self.__outputD):
            if self.__verbose:
                self.__lfh.write("Failed number of outputs\n")
            return False
        #
        # output types consistent?
        if numOut > 0:
            for oN in self.__aReg.getOutputObjectNames(self.__actionId):
                if self.__aReg.isSetOutputReferenceType(self.__actionId, oN):
                    if self.__aReg.getOutputReferenceType(self.__actionId, oN) != self.__outputD[oN].getReferenceType():
                        if self.__verbose:
                            self.__lfh.write("Failed output reference type %s\n" % oN)
                        return False
                if self.__aReg.isSetOutputContainerType(self.__actionId, oN):
                    if self.__aReg.getOutputContainerType(self.__actionId, oN) != self.__outputD[oN].getContainerTypeName():
                        if self.__verbose:
                            self.__lfh.write("Failed output container type %s\n" % oN)
                        return False
                if self.__aReg.isSetOutputValueType(self.__actionId, oN):
                    if self.__aReg.getOutputValueType(self.__actionId, oN) != self.__outputD[oN].getValueTypeName():
                        if self.__verbose:
                            self.__lfh.write("Failed output value type %s\n" % oN)
                        return False
                if self.__aReg.isSetOutputSelectorType(self.__actionId, oN):
                    if self.__aReg.getOutputSelectorType(self.__actionId, oN) != self.__outputD[oN].getSelectorType():
                        if self.__verbose:
                            self.__lfh.write("Failed output selector type %s\n" % oN)
                        return False
                if self.__aReg.isSetOutputContentType(self.__actionId, oN):
                    if self.__aReg.getOutputContentType(self.__actionId, oN) != self.__outputD[oN].getContentType():
                        if self.__verbose:
                            self.__lfh.write("Failed output content type %s\n" % oN)
                        return False
                if self.__aReg.isSetOutputFileFormat(self.__actionId, oN):
                    if self.__aReg.getOutputFileFormat(self.__actionId, oN) != self.__outputD[oN].getFileFormat():
                        if self.__verbose:
                            self.__lfh.write("Failed output file format %s\n" % oN)
                        return False

        return True

    def run(self):
        """Invokes the specified action.

        Returns:

        The True if the action completed without exception or False otherwise.

        """
        try:
            modulePath = self.__aReg.getModuleName(self.__actionId)
            aMod = __import__(modulePath, globals(), locals(), [""])
            sys.modules[modulePath] = aMod
            #
            # Strip off any leading path to the module before we instaniate the object.
            mpL = modulePath.split(".")
            clN = mpL[-1]
            #
            # aObj = getattr(aMod,modulePath)()
            aObj = getattr(aMod, clN)(verbose=self.__verbose, log=self.__lfh)
            aMeth = getattr(aObj, self.__aReg.getMethodName(self.__actionId), None)
            if aMeth is not None:
                ok = aMeth(
                    inputObjectD=self.__inputD,
                    outputObjectD=self.__outputD,
                    userParameterD=self.__userParameterD,
                    internalParameterD=self.__aReg.getInternalParameterDict(self.__actionId),
                )
                return ok
            else:
                return False
        except Exception as _e:  # noqa: F841
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

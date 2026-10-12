##
# File:    UtilsBase.py
# Date:    8-April-2010
#
# Updates:
#
##
"""
Module containing the base class describing the call interface for methods callable
from the ProcessRunner() class.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


import sys
from typing import TYPE_CHECKING, Any, Dict, Mapping, TextIO, Tuple

from typing_extensions import TypedDict, Unpack

from wwpdb.utils.wf.process.ActionRegistryTypes import ActionParameterDict

if TYPE_CHECKING:
    from wwpdb.utils.wf.WfDataObject import WfDataObject

# Input or output data objects passed by ProcessRunner, keyed by the names declared in the action registry
WfDataObjectDict = Dict[str, "WfDataObject"]
# What _getArgs() returns: (inputObjectD, outputObjectD, userParameterD, internalParameterD)
PluginArgs = Tuple[WfDataObjectDict, WfDataObjectDict, ActionParameterDict, ActionParameterDict]


class PluginKwargs(TypedDict):
    """The keyword arguments ProcessRunner.run() passes to every plugin action method.

    Action methods are declared as `def xxxOp(self, **kwArgs: Unpack[PluginKwargs]) -> bool`.
    """

    inputObjectD: WfDataObjectDict
    """Input data objects, keyed by the input names declared in the action registry"""
    outputObjectD: WfDataObjectDict
    """Output data objects, keyed by the output names declared in the action registry"""
    userParameterD: ActionParameterDict
    """User adjustable parameters (registry defaults overridden by ProcessRunner.setParameterDict())"""
    internalParameterD: ActionParameterDict
    """Internal parameters from the action registry"""


class UtilsBase:
    """Base class implementing the method calling interface of the
    `ProcessRunner()` class.   This interface provides the keyword arguments:

    - inputObjectD   dictionary of input objects
    - outputObjectD  dictionary of output objects
    - userParmeterD  dictionary of user adjustable parameters
    - internalParameterD dictionary of internal parameters

    Each method in the class handles its own exceptions and returns
    True on success or False otherwise.

    """

    def __init__(self, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        self._verbose = verbose
        self._lfh = log

    def _getArgs(self, kwD: PluginKwargs) -> PluginArgs:
        """Extract the keyword arguments used by methods in this class."""
        return (kwD["inputObjectD"], kwD["outputObjectD"], kwD["userParameterD"], kwD["internalParameterD"])

    def noOp(self, **kwArgs: Unpack[PluginKwargs]) -> bool:
        self._getArgs(kwArgs)
        return True

    def dumpArgs(self, kwD: Mapping[str, Any]) -> None:
        for k, v in kwD.items():
            self._lfh.write("+UtilsBase.dumArgs() key: %s  value: %r \n" % (k, v))

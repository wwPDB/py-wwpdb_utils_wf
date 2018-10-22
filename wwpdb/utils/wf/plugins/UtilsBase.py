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


class UtilsBase(object):

    """ Base class implementing the method calling interface of the
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParmeterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        Each method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """

    def __init__(self, verbose=True, log=sys.stderr):
        self._verbose = verbose
        self._lfh = log

    def _getArgs(self, kwD):
        """ Extract the keyword arguments used by methods in this class.
        """
        return (kwD['inputObjectD'], kwD['outputObjectD'], kwD['userParameterD'], kwD['internalParameterD'])

    def noOp(self, **kwArgs):
        self._getArgs(kwArgs)
        return True

    def dumpArgs(self, kwD):
        for k, v in kwD.items():
            self._lfh.write("+UtilsBase.dumArgs() key: %s  value: %r \n" % (k, v))

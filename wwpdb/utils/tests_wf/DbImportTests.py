##
# File: DbImportTests.py
# Date:  10-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for wwpdb.utils.wf - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest
import datetime

if __package__ is None or __package__ == '':
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import MyNoop  # pylint: disable=import-error
else:
    from .commonsetup import MyNoop  # noqa: F401

from wwpdb.utils.wf.dbapi.WfDbApi import WfDbApi  # noqa: F401
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection
from wwpdb.utils.wf.dbapi.DbCommand import DbCommand
from wwpdb.utils.wf.dbapi.WfTracking import WfTracking
from wwpdb.utils.wf.dbapi.WFEtime import getTimeZero, getTimeNow, getTimeSeconds, getTimeString, getTimeFromEpoc, getTimeReadable  # noqa: F401


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        # vT = WfDbApi() --- This should be mocked
        _vC = DbConnection()  # noqa: F841
        _vC = DbCommand(dbcon=None)  # noqa: F841
        _vC = WfTracking()  # noqa: F841

        self.assertEqual(getTimeZero(), datetime.datetime(2000, 1, 1, 0, 0, 0))


if __name__ == '__main__':
    unittest.main()

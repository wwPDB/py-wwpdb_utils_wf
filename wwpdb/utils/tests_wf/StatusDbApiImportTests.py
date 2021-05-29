##
# File: StatusDbApiImportTests.py
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

if __package__ is None or __package__ == "":
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, mockTopPath  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT, mockTopPath  # noqa: F401

from wwpdb.utils.wf.dbapi.StatusDbApi import StatusDbApi  # noqa: F401 pylint: disable=unused-import


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        pass


if __name__ == "__main__":
    unittest.main()

##
# File: ProcessImportTests.py
# Date:  10-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for wwpdb.utils.wf.process - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

# pylint: disable=unused-import

import unittest

if __package__ is None or __package__ == '':
    import sys
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import HERE  # pylint: disable=import-error,unused-import
else:
    from .commonsetup import HERE  # noqa: F401

from wwpdb.utils.wf.process.ActionRegistry import ActionRegistry  # noqa: F401
from wwpdb.utils.wf.process.ActionRegistryIo import ActionRegistryIo  # noqa: F401
from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner  # noqa: F401


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        # vc = ProcessRunner()
        pass


if __name__ == '__main__':
    unittest.main()

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

import unittest

from wwpdb.utils.wf.process.ActionRegistry import ActionRegistry
from wwpdb.utils.wf.process.ActionRegistryIo import ActionRegistryIo
from wwpdb.utils.wf.process.ProcessRunner import ProcessRunner


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        #vc = ProcessRunner()
        pass

if __name__ == '__main__':
    unittest.main()


    

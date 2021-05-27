"""

File:    LocalDbApiTest.py

     Some test cases ..

"""
import sys
#
if __package__ is None or __package__ == '':
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT, mockTopPath  # pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT, mockTopPath  # noqa: F401


from wwpdb.utils.wf.dbapi.LocalDbApi import LocalDbApi


if __name__ == '__mainold__':
    __lfh = sys.stderr
    # fileName="test.log"
    c = LocalDbApi(__lfh, True)
    rd = []
    rd = c.getNewDepositedIds(1)

    for k in rd:
        __lfh.write("%s\n" % k)

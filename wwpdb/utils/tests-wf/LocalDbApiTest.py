"""

File:    LocalDbApiTest.py

     Some test cases ..

"""
import os,sys
#
from wwpdb.utils.wf.dbapi.LocalDbApi import LocalDbApi
from wwpdb.io.misc.FormatOut     import FormatOut

if __name__ == '__mainold__':
    
    
    __lfh = sys.stderr
    #fileName="test.log"
    c=LocalDbApi(__lfh, True)
    rd=[]
    rd= c.getNewDepositedIds(1)
    
    for k in rd:
        __lfh.write("%s\n" % k)
        

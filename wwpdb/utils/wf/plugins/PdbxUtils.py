##
# File:    PdxUtils.py
# Date:    10-April-2010
#
# Updates:
# 24-April-2010  jdw statusOp method to return a dictionary of common status items.
#
##
"""
Module of data access utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import traceback

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase

from  mmcif.core.mmciflib import ParseCifSimple


class CifFile(object):

    """
    CifFile
    """

    def __init__(self, fileName):
        self.__fileName = fileName
        self.__cifFile = ParseCifSimple(self.__fileName, verbose=False, intCaseSense=0, maxLineLength=1024, nullValue="?", parseLogFileName="")

    def getCifFile(self):
        return (self.__cifFile)

    @classmethod
    def getFileExt(cls):
        return ('cif')

    def write(self, fileName):
        self.__cifFile.Write(fileName)

    @classmethod
    def read(cls, fileName):
        return cls(fileName)


class PdbxUtils(UtilsBase):

    """ Utility class of methods to access data within PDBx files.

        Current supported operations include:

        Each method in this class implements the method calling interface of the
        `ProcessRunner()` class.   This interface provides the keyword arguments:

        - inputObjectD   dictionary of input objects
        - outputObjectD  dictionary of output objects
        - userParameterD  dictionary of user adjustable parameters
        - internalParameterD dictionary of internal parameters

        Each method in the class handles its own exceptions and returns
        True on success or False otherwise.

    """

    def __init__(self, verbose=True, log=sys.stderr):
        super(PdbxUtils, self).__init__(verbose, log)
        #
        self.__block = None
        """ Target block -
        """
        self.__blockList = []
        self.__targetBlockName = None
        self.__targetBlockIndex = 0
        self.__cifFile = None
        self.__blockList = []
        self._lfh = log

    def __getBlock(self, pdbxPath):
        """ Open the input PDBx file and set the target data block.

            Returns:

            True for success or False otherwise.

        """
        try:
            cf = CifFile(pdbxPath)
            self.__cifFile = cf.getCifFile()
            bL = []
            self.__blockList = self.__cifFile.GetBlockNames(bL)
            # print self.__blockList

            # take the target block by name if specified or just the first block otherwise
            if (self.__targetBlockName is not None and self.__targetBlockName in self.__blockList):
                self.__block = self.__cifFile.GetBlock(self.__targetBlockName)
            else:
                self.__block = self.__cifFile.GetBlock(self.__blockList[self.__targetBlockIndex])
            #
            return True
        except:
            if (self._verbose):
                traceback.print_exc(file=self._lfh)
            return False

    def __templateSelection(self, kwD):
        """ Template selection method.

        This method supports equality selection conditions within the target category.

        Selector defines the following selector parameters:
        - targetCategoryName  name of category to which selection is applied
        - targetAttributeNameList [attributeName, attributeName,...] the values of the
          attributes in this list will be returned subject to the selection condition.

        Selection Condition -
        - conditionList  [(attributeName,attributeValue,comparisonOp),,...]

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwD)
            pdbxPath = str(inpObjD["src"].getFilePathReference())
            if (not self.__getBlock(pdbxPath)):
                return False
            #

            targetCategory = str(inpObjD["src"].getSelectCategoryName())
            if (not self.__block.IsTablePresent(targetCategory)):
                return False

            myTable = self.__block.GetTable(targetCategory)

            conditionList = inpObjD["src"].getSelectConditionList()
            if (len(conditionList) > 0):
                aNL = []
                aVL = []
                for cTup in conditionList:
                    aNL.append(str(cTup[0]))
                    aVL.append(str(cTup[1]))
                aNT = tuple(aNL)
                aVT = tuple(aVL)
                #
                # print "aNt",aNT
                # print "aVt",aVT
                indices = myTable.Search(aVT, aNT)
                if (len(indices) > 0):
                    attributeList = inpObjD["src"].getSelectAttributeList()
                    rV = []
                    for atN in attributeList:
                        rV.append(myTable(indices[0], str(atN)))
                    outObjD['dst'].setValue(rV)
                    return True
        except:
            if (self._verbose):
                traceback.print_exc(file=self._lfh)
            return False

        return False

    def __templateFetchAttribute(self, kwD):
        """ Template fetch column method.

        This method supports recovering the values of an attribute (or column of attributes).

        Selector defines the following selector parameters:
        - targetCategoryName  name of the target category
        - targetAttributeName name of the target attribute

        Only container types *list* and *value* are support.
        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwD)
            pdbxPath = str(inpObjD["src"].getFilePathReference())
            if (not self.__getBlock(pdbxPath)):
                return False
            #
            targetCategory = str(inpObjD["src"].getSelectCategoryName())
            if (not self.__block.IsTablePresent(targetCategory)):
                return False

            attributeList = inpObjD["src"].getSelectAttributeList()
            targetAttribute = str(attributeList[0])

            myTable = self.__block.GetTable(targetCategory)
            cL = []
            colNames = list(myTable.GetColumnNames())
            rList = list(myTable.GetColumn(cL, targetAttribute))

            if (outObjD['dst'].getContainerTypeName() == 'value'):
                outObjD['dst'].setValue(rList[0])
            elif (outObjD['dst'].getContainerTypeName() == 'list'):
                outObjD['dst'].setValue(rList)
            else:
                return False
            #
            return True
        except:
            if (self._verbose):
                traceback.print_exc(file=self._lfh)
            return False

    def __getCategoryRowCount(self, kwD):
        """ Template method to count category size/test for existence .

        Input src defines pdbx file and dst will hold integer row count.

        User defined parameter 'category':
        - name of category to which the test is applied


        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwD)
            pdbxPath = str(inpObjD["src"].getFilePathReference())
            if (not self.__getBlock(pdbxPath)):
                outObjD['dst'].setValue(0)
                return True
            #
            if 'category' in uD:
                targetCategory = str(uD['category'])
            else:
                outObjD['dst'].setValue(0)
                return True

            if (not self.__block.IsTablePresent(targetCategory)):
                outObjD['dst'].setValue(0)
                return True

            myTable = self.__block.GetTable(targetCategory)
            outObjD['dst'].setValue(myTable.GetNumRows())

            return True
        except:
            if (self._verbose):
                traceback.print_exc(file=self._lfh)
            return False

        return False

    def categoryRowCountOp(self, **kwArgs):
        return self.__getCategoryRowCount(kwArgs)

    def selectOp(self, **kwArgs):
        return self.__templateSelection(kwArgs)

    def fetchOp(self, **kwArgs):
        return self.__templateFetchAttribute(kwArgs)

    def statusOp(self, **kwArgs):
        return self.__fetchStatusDictionary(kwArgs)

    def __fetchStatusDictionary(self, kwD):
        """
        depDB = {}
        Done -
        depDB["PDB_ID"]=self.accession
        depDB["INITIAL_DEPOSITION_DATE"] = datetime.date.today()
        depDB["DEPOSIT_SITE"]="PDBe"
        depDB["PROCESS_SITE"]="PDBe"
        depDB["STATUS_CODE"]=self.processState
        depDB["ANNOTATOR_INITIALS"]="AN"
        depDB["AUTHOR_RELEASE_STATUS_CODE"]="HPUB"
        depDB["EXP_METHOD"]="X-RAY"
        depDB["STATUS_CODE_EXP"]="comp"
        depDB["TITLE"]="A test deposition for " + self.depositionID
        #
        Todo -
        depDB["SG_CENTER"]=None
        depDB["AUTHOR_LIST"] = "A.Depositor, Anna.Depositor, Yeta,Depositor"

        """
        d = {}
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwD)
            pdbxPath = inpObjD["src"].getFilePathReference()
            if (not self.__getBlock(pdbxPath)):
                return False
            #
            targetCategory = 'struct'
            if (self.__block.IsTablePresent(targetCategory)):
                targetAttribute = 'title'
                myTable = self.__block.GetTable(targetCategory)
                colNames = list(myTable.GetColumnNames())
                cL = []
                rList = list(myTable.GetColumn(cL, targetAttribute))
                if (len(rList) > 0):
                    d['title'] = rList[0]
                else:
                    d['title'] = None
            #
            targetCategory = 'exptl'
            if (self.__block.IsTablePresent(targetCategory)):
                targetAttribute = 'method'
                myTable = self.__block.GetTable(targetCategory)
                colNames = list(myTable.GetColumnNames())
                cL = []
                rList = list(myTable.GetColumn(cL, targetAttribute))
                if (len(rList) > 0):
                    d['exp_method'] = rList[0]
                else:
                    d['exp_method'] = None

            targetCategory = 'pdbx_database_status'
            if (self.__block.IsTablePresent(targetCategory)):
                aList = [("recvd_initial_deposition_date", "recvd_initial_deposition_date"),
                         ("author_release_status_code", "author_release_status_code"),
                         ("deposit_site", "deposit_site"),
                         ("process_site", "process_site"),
                         ("status_code", "status_code"),
                         ("annotator_initials", "rcsb_annotator"),
                         ("status_code_mr", "status_code_mr"),
                         ("status_code_sf", "status_code_sf")]
                myTable = self.__block.GetTable(targetCategory)
                colNames = list(myTable.GetColumnNames())
                for aTup in aList:
                    if aTup[1] in colNames:
                        cL = []
                        rList = list(myTable.GetColumn(cL, aTup[1]))
                        if (len(rList) > 0):
                            # Cannot be unicode for comparisons
                            d[aTup[0]] = rList[0].encode('utf-8')
                        else:
                            d[aTup[0]] = None
            #
            #
            targetCategory = 'pdbx_SG_project'
            if (self.__block.IsTablePresent(targetCategory)):
                aList = [('full_name_of_center', 'full_name_of_center'),
                         ('initial_of_center', 'initial_of_center')]
                myTable = self.__block.GetTable(targetCategory)
                colNames = list(myTable.GetColumnNames())
                for aTup in aList:
                    if aTup[1] in colNames:
                        cL = []
                        rList = list(myTable.GetColumn(cL, aTup[1]))
                        if (len(rList) > 0):
                            d[aTup[0]] = rList[0]
                        else:
                            d[aTup[0]] = None
            #
            targetCategory = 'database_2'
            dbIdList = ['PDB', 'BMRRB', 'EMDB']
            accessionD = {}
            for dbId in dbIdList:
                accessionD[dbId] = []
            #
            if (self.__block.IsTablePresent(targetCategory)):
                myTable = self.__block.GetTable(targetCategory)
                for dbId in dbIdList:
                    indexList = myTable.Search((dbId,), ('database_id',))
                    if len(indexList) > 0:
                        tList = []
                        for idx in range(0, len(indexList)):
                            tList.append(myTable(indexList[idx], "database_code"))
                        accessionD[dbId] = tList
                    else:
                        accessionD[dbId] = []

            d['accessions'] = accessionD

            targetCategory = 'audit_author'
            if (self.__block.IsTablePresent(targetCategory)):
                targetAttribute = 'name'
                myTable = self.__block.GetTable(targetCategory)
                colNames = list(myTable.GetColumnNames())
                cL = []
                rList = list(myTable.GetColumn(cL, targetAttribute))
                if (len(rList) > 0):
                    d['audit_author'] = []
                    for r in rList:
                        d['audit_author'].append(r)
                else:
                    d['audit_author'] = []

            outObjD['dst'].setValue(d)
            return True
        except:
            if (self._verbose):
                traceback.print_exc(file=self._lfh)
            return False

        pass

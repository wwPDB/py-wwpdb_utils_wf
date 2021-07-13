##
# File:    ActionRegistryIo.py
# Date:    8-April-2010
#
# Updates:
#    7-Sep-2015  jdw -  Add lists to capture order of input's and output's
##
"""
I/O manager for the registry of action definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback
from xml.dom import minidom
from wwpdb.io.misc.FormatOut import FormatOut


class ActionRegistryIo(object):

    """I/O manager class action definitions for the action registry.

     The action registry xml encoding has the following organization::

         <?xml version='1.0' encoding='utf-8'?>
         <actionList version='0.01'>
           <action name="copy">
               <inputList>
                   <wfDataObject name=1>
                       <dataReferenceType>file</dataReferenceType>
                       <contentType>model</contentType>
                       <fileFormat>pdbx</fileFormat>
                       <containerType></containerType>
                       <valueType></valueType>
                       <selectorType></selectorType>
                   </wfDataObject>
               </inputList>
               <outputList>
                   <wfDataObject name=1>
                       <dataReferenceType>file</dataReferenceType>
                       <contentType>model</contentType>
                       <fileFormat>pdbx</fileFormat>
                       <containerType></containerType>
                       <valueType></valueType>
                       <selectorType></selectorType>
                   </wfDataObject>
               </outputList>
               <userParameters>
                   <parameter name="mode">r</parameter>
               </userParameters>
               <internalParameters>
                   <parameter name="force">-f</parameter>
               </internalParameters>
               <moduleName>FileUtils</moduleName>
               <methodName>copyOp</methodName>
           </action>
         </actionList>


    The action registry dictionary is stored in a dictionary using following organization:

    - *actionId*,  a unique action identifier referencing a dictionary with the following keys:

      + INPUT_INFO_LIST & OUTPUT_INFO_LIST,  list of required features of the input and out data objects stored as
        tuples of (reference_type, (data_type,container_type), selector_type)
      + USER_PARAMETER_DICTIONARY,  container for user settable parameters passed to the action method.
      + INTERNAL_PARAMETER_DICTIONARY,  container for internal parameters passed to the action method.
      + MODULE_NAME,   Python module(class) name containing the target method
      + METHOD_NAME,   Python method name

    Method prototype:

    method(inputObjList=[],outputObjList=[],parameterDictionary={})

    """

    def __init__(self, filePath="./examples/resources/actionData.xml", verbose=False, log=sys.stderr):
        #
        self.__lfh = log
        self.__verbose = verbose  # pylint: disable=unused-private-member
        #
        # self.lt = time.strftime("%Y%m%d", time.localtime())
        #
        self.__fileName = filePath
        self.__dict = {}
        self.__setup()
        #

    def __setup(self):
        try:
            self.__dom = minidom.parse(self.__fileName)
            self.__dict = self.__getActionDictionary()
            return True
        except Exception as _e:  # noqa: F841
            self.__lfh.write("+ActionRegistryIo.__setup() - read failed for %s\n" % self.__fileName)
            traceback.print_exc(file=self.__lfh)
            return False

    def getRegistry(self):
        """Returns the dictionary data structure representing the action registry."""
        return self.__dict

    def __getWfDataObjectList(self, el):
        oD = {}
        oL = []
        for child in el.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if len(child.childNodes) == 0:
                continue
            #
            if child.nodeName == "wfDataObject":
                dId = child.getAttributeNode("name").nodeValue
                tD = {"dataReferenceType": None, "contentType": None, "fileFormat": None, "containerType": None, "valueType": None, "selectorType": None}
                for tch in child.childNodes:
                    if tch.nodeName in tD.keys():
                        if len(tch.childNodes) > 0:
                            tD[tch.nodeName] = tch.childNodes[0].nodeValue
                oD[dId] = tD
                oL.append(dId)
        #
        return oD, oL

    def __getActionDictionary(self):
        """Parser for action registry data file.  Builds dictionary of action definitions."""
        aD = {}
        els = self.__dom.getElementsByTagName("action")
        for el in els:
            actionId = el.getAttributeNode("name").nodeValue
            rD = {}
            rD["MODULE_NAME"] = None
            rD["METHOD_NAME"] = None
            rD["INPUT_INFO_LIST"] = {}
            rD["OUTPUT_INFO_LIST"] = {}
            rD["INPUT_NAME_LIST"] = []
            rD["OUTPUT_NAME_LIST"] = []
            rD["USER_PARAMETER_DICT"] = {}
            rD["INTERNAL_PARAMETER_DICT"] = {}
            #
            for child in el.childNodes:
                if child.nodeType != child.ELEMENT_NODE:
                    continue
                if len(child.childNodes) == 0:
                    continue

                if child.nodeName == "moduleName":
                    rD["MODULE_NAME"] = child.childNodes[0].nodeValue

                if child.nodeName == "methodName":
                    rD["METHOD_NAME"] = child.childNodes[0].nodeValue

                elif child.nodeName == "userParameters":
                    pD = {}
                    for tch in child.childNodes:
                        if tch.nodeName == "parameter":
                            ky = tch.getAttributeNode("name").nodeValue
                            if len(tch.childNodes) > 0:
                                val = tch.childNodes[0].nodeValue
                            else:
                                val = None
                            pD[ky] = val
                    rD["USER_PARAMETER_DICT"] = pD

                elif child.nodeName == "internalParameters":
                    pD = {}
                    for tch in child.childNodes:
                        if tch.nodeName == "parameter":
                            ky = tch.getAttributeNode("name").nodeValue
                            if len(tch.childNodes) > 0:
                                val = tch.childNodes[0].nodeValue
                            else:
                                val = None
                            pD[ky] = val
                    rD["INTERNAL_PARAMETER_DICT"] = pD

                elif child.nodeName == "inputList":
                    rD["INPUT_INFO_LIST"], rD["INPUT_NAME_LIST"] = self.__getWfDataObjectList(child)
                elif child.nodeName == "outputList":
                    rD["OUTPUT_INFO_LIST"], rD["OUTPUT_NAME_LIST"] = self.__getWfDataObjectList(child)
                else:
                    pass

            aD[actionId] = rD
        return aD

    def dump(self):
        out = FormatOut()
        out.autoFormat("Action registry file", self.__dict, 3, 3)
        out.writeStream(self.__lfh)

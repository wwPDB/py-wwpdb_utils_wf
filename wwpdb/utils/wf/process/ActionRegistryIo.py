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
from typing import TYPE_CHECKING, Dict, List, Optional, TextIO, Tuple, cast
from xml.dom import minidom

from wwpdb.io.misc.FormatOut import FormatOut

from wwpdb.utils.wf.process.ActionRegistryTypes import ActionDataObjectDef, ActionParameterDict, ActionRegistryDict

if TYPE_CHECKING:
    from wwpdb.utils.wf.process.ActionRegistryTypes import ActionDef


class ActionRegistryIo:
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

    def __init__(self, filePath: str = "./examples/resources/actionData.xml", verbose: bool = False, log: TextIO = sys.stderr) -> None:
        #
        self.__lfh = log
        self.__verbose = verbose  # pylint: disable=unused-private-member
        #
        # self.lt = time.strftime("%Y%m%d", time.localtime())
        #
        self.__fileName = filePath
        self.__dict: ActionRegistryDict = {}
        self.__setup()
        #

    def __setup(self) -> bool:
        try:
            self.__dom = minidom.parse(self.__fileName)  # noqa: S318
            self.__dict = self.__getActionDictionary()
            return True
        except Exception as _e:  # noqa: F841,BLE001
            self.__lfh.write("+ActionRegistryIo.__setup() - read failed for %s\n" % self.__fileName)
            traceback.print_exc(file=self.__lfh)
            return False

    def getRegistry(self) -> ActionRegistryDict:
        """Returns the dictionary data structure representing the action registry."""
        return self.__dict

    def __getWfDataObjectList(self, el: minidom.Element) -> Tuple[Dict[str, ActionDataObjectDef], List[str]]:
        oD: Dict[str, ActionDataObjectDef] = {}
        oL: List[str] = []
        for child in el.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if len(child.childNodes) == 0:
                continue
            #
            if child.nodeName == "wfDataObject":
                dId = child.getAttributeNode("name").nodeValue  # type: ignore[union-attr]  # a missing name attribute raises here, see ERRORS.md
                tD: Dict[str, Optional[str]] = {
                    "dataReferenceType": None,
                    "contentType": None,
                    "fileFormat": None,
                    "containerType": None,
                    "valueType": None,
                    "selectorType": None,
                }
                for tch in child.childNodes:
                    if tch.nodeName in tD:
                        if len(tch.childNodes) > 0:
                            tD[tch.nodeName] = tch.childNodes[0].nodeValue
                oD[dId] = cast("ActionDataObjectDef", tD)  # tD holds exactly the ActionDataObjectDef keys
                oL.append(dId)
        #
        return oD, oL

    def __getActionDictionary(self) -> ActionRegistryDict:
        """Parser for action registry data file.  Builds dictionary of action definitions."""
        aD: ActionRegistryDict = {}
        els = self.__dom.getElementsByTagName("action")
        for el in els:
            actionId = el.getAttributeNode("name").nodeValue  # type: ignore[union-attr]  # a missing name attribute raises here, see ERRORS.md
            rD = cast("ActionDef", {})  # filled in key by key below
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
                    pD: ActionParameterDict = {}
                    for tch in child.childNodes:
                        if tch.nodeName == "parameter":
                            ky = tch.getAttributeNode("name").nodeValue  # type: ignore[union-attr]  # tch is an Element; a missing name attribute raises here, see ERRORS.md
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
                            ky = tch.getAttributeNode("name").nodeValue  # type: ignore[union-attr]  # tch is an Element; a missing name attribute raises here, see ERRORS.md
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

    def dump(self) -> None:
        out = FormatOut()
        out.autoFormat("Action registry file", self.__dict, 3, 3)
        out.writeStream(self.__lfh)

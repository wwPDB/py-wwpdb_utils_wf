##
# File:    ActionRegistry.py
# Date:    1-April-2010
#
# Updates:
#
# 21-Apr-2010 jdw Added method getActions()
#  7-Sep-2015 jdw Return names in parse order -
##
"""
Repository for process action definitions.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import traceback
from wwpdb.utils.wf.process.ActionRegistryIo import ActionRegistryIo
from wwpdb.utils.config.ConfigInfo import ConfigInfo


class ActionRegistry(object):

    """Container and manager class for the registry of supported process actions.

        The action registry has the following internal data orgaization:

        - A dictionary with unique action identifier referencing a dictionary with the following content:

          + INPUT_INFO_LIST & OUTPUT_INFO_LIST,  list of required features of the input and out
            data objects stored as tuples of (reference_type, (data_type,container_type), selector_type)
          + USER_PARAMETER_DICTIONARY,  container for user settable parameters passed to
            the action method.
          + INTERNAL_PARAMETER_DICTIONARY,  container for internal parameters passed to
            the action method.
          + MODULE_NAME,   Python module(class) name containing the target method
          + METHOD_NAME,   Python method name

        Method prototype:

        method(inputObjList=[],outputObjList=[],parameterDictionary={})

       """

    def __init__(self):
        self.__cI = ConfigInfo()
        regPath = self.__cI.get('SITE_REGISTRY_FILE_PATH')
        aR = ActionRegistryIo(filePath=regPath)
        self.__D = aR.getRegistry()

    def getActions(self):
        """Returns:

           List of action identifiers defined in the action registry. An empty list is
           returned if the an exception is encountered.

        """
        try:
            return self.__D.keys()
        except:
            return []

    def isDefinedAction(self, actionId):
        """ Returns:

            True if the input action identifier is defined in the registry or False otherwise.
        """
        if actionId in self.__D:
            return True
        else:
            return False

    def getMethodName(self, actionId):
        """ Returns:

            The Python method name associated with the input action identifier
            or None if the action is not defined.
        """
        try:
            return self.__D[actionId]['METHOD_NAME']
        except:
            return None

    def getModuleName(self, actionId):
        """ Returns:

            The Python module name containing the method associated with the input action identifier
            or None if the action is not defined.
        """

        try:
            return self.__D[actionId]['MODULE_NAME']
        except:
            return None

    def getUserParameterDict(self, actionId):
        """ Returns:

            The user parameter dictionary for the input action identifier
            or {} if the action is not defined.
        """

        try:
            return self.__D[actionId]['USER_PARAMETER_DICT']
        except:
            return {}

    def getInternalParameterDict(self, actionId):
        """ Returns:

            The internal parameter dictionary for the input action identifier
            or {} if the action is not defined.
        """

        try:
            return self.__D[actionId]['INTERNAL_PARAMETER_DICT']
        except:
            return {}

    def getInputObjectCount(self, actionId):
        """ Returns:

            The number of input data objects required for input action identifier
            or 0 if the action is not defined.
        """

        try:
            return len(self.__D[actionId]['INPUT_INFO_LIST'].keys())
        except:
            traceback.print_exc(file=sys.stderr)
            return 0

    def getInputObjectNames(self, actionId):
        """ Returns:

            The list of names of input data objects required for input action identifier
            or [] if the action is not defined.
        """

        try:
            return self.__D[actionId]['INPUT_NAME_LIST']
        except:
            traceback.print_exc(file=sys.stderr)
            return []

    def getOutputObjectCount(self, actionId):
        """ Returns:

            The number of output data objects required for the input action identifier
            or 0 if the action is not defined.
        """

        try:
            return len(self.__D[actionId]['OUTPUT_INFO_LIST'].keys())
        except:
            return 0

    def getOutputObjectNames(self, actionId):
        """ Returns:

            The list of names of output data objects required for the input action identifier
            or [] if the action is not defined.
        """

        try:
            return self.__D[actionId]['OUTPUT_NAME_LIST']
        except:
            return []

    def setUserParameter(self, actionId, paramKey, paramValue):
        """Set a user adjustable parameter for the input action.  The parameter is
           identifiers by *paramKey* and the value is specified as *paramValue*.

           Returns:

           True is the parameter setting was succesful or False otherwise.

        """
        try:
            self.__D[actionId]['USER_PARAMETER_DICT'][paramKey] = paramValue
            return True
        except:
            return False

    def getUserParameter(self, actionId, paramKey):
        """Returns:

           The value of a user adjustable parameter for the input action.  The
           user parameteris identified by the *paramKey*.

        """
        try:
            return self.__D[actionId]['USER_PARAMETER_DICT'][paramKey]
        except:
            return None

    def isSetInputReferenceType(self, actionId, inpName="1"):
        """ Is the reference type for the specified action and input object assigned?

            Returns:

            True if the reference type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['dataReferenceType'] is not None)
        except:
            return False

    def getInputReferenceType(self, actionId, inpName="1"):
        """Get the reference type for the specified action and input object.

           Returns:

           The reference type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['dataReferenceType']
        except:
            return None

    def isSetInputContainerType(self, actionId, inpName="1"):
        """ Is the container type for the specified action and input object assigned?

            Returns:

            True if the container type is assigned or False otherwise.

        """

        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['containerType'] is not None)
        except:
            return False

    def getInputContainerType(self, actionId, inpName="1"):
        """Get the container type for the specified action and input object.

           Returns:

           The container type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['containerType']
        except:
            return None

    def isSetInputValueType(self, actionId, inpName="1"):
        """ Is the value type for the specified action and input object assigned?

            Returns:

            True if the value type is assigned or False otherwise.

        """

        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['containerType'] is not None)
        except:
            return False

    def getInputValueType(self, actionId, inpName="1"):
        """Get the value type for the specified action and input object.

           Returns:

           The value type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['valueType']
        except:
            return None

    def isSetInputSelectorType(self, actionId, inpName="1"):
        """ Is the selector type for the specified action and input object assigned?

            Returns:

            True if the selector type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['selectorType'] is not None)
        except:
            return False

    def getInputSelectorType(self, actionId, inpName="1"):
        """Get the selector type for the specified action and input object.

           Returns:

           The selector type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['selectorType']
        except:
            return None

    def isSetInputContentType(self, actionId, inpName="1"):
        """ Is the content type for the specified action and input object assigned?

            Returns:

            True if the content type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['contentType'] is not None)
        except:
            return False

    def getInputContentType(self, actionId, inpName="1"):
        """Get the content type for the specified action and input object.

           Returns:

           The content type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['contentType']
        except:
            return None

    def isSetInputFileFormat(self, actionId, inpName="1"):
        """ Is the file format for the specified action and input object assigned?

            Returns:

            True if the file format is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['INPUT_INFO_LIST'][inpName]['fileFormat'] is not None)
        except:
            return False

    def getInputFileFormat(self, actionId, inpName="1"):
        """Get the file format for the specified action and input object.

           Returns:

           The file format if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['INPUT_INFO_LIST'][inpName]['fileFormat']
        except:
            return None

    def isSetOutputReferenceType(self, actionId, inpName="1"):
        """ Is the reference type for the specified action and output object assigned?

            Returns:

            True if the reference type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['dataReferenceType'] is not None)
        except:
            return False

    def getOutputReferenceType(self, actionId, inpName="1"):
        """Get the reference type for the specified action and output object.

           Returns:

           The reference type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['dataReferenceType']
        except:
            return None

    def isSetOutputContainerType(self, actionId, inpName="1"):
        """ Is the container type for the specified action and output object assigned?

            Returns:

            True if the container type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['containerType'] is not None)
        except:
            return False

    def getOutputContainerType(self, actionId, inpName="1"):
        """Get the container type for the specified action and output object.

           Returns:

           The container type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['containerType']
        except:
            return None

    def isSetOutputValueType(self, actionId, inpName="1"):
        """ Is the value type for the specified action and output object assigned?

            Returns:

            True if the value type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['valueType'] is not None)
        except:
            return False

    def getOutputValueType(self, actionId, inpName="1"):
        """Get the value type for the specified action and output object.

           Returns:

           The value type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['valueType']
        except:
            return None

    def isSetOutputSelectorType(self, actionId, inpName="1"):
        """ Is the selector type for the specified action and output object assigned?

            Returns:

            True if the selector type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['selectorType'] is not None)
        except:
            return False

    def getOutputSelectorType(self, actionId, inpName="1"):
        """Get the selector type for the specified action and output object.

           Returns:

           The selector type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['selectorType']
        except:
            return None

    def isSetOutputContentType(self, actionId, inpName="1"):
        """ Is the content type for the specified action and output object assigned?

            Returns:

            True if the content type is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['contentType'] is not None)
        except:
            return False

    def getOutputContentType(self, actionId, inpName="1"):
        """Get the content type for the specified action and output object.

           Returns:

           The content type if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['contentType']
        except:
            return None

    def isSetOutputFileFormat(self, actionId, inpName="1"):
        """ Is the file format for the specified action and output object assigned?

            Returns:

            True if the file format is assigned or False otherwise.

        """
        try:
            return (self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['fileFormat'] is not None)
        except:
            return False

    def getOutputFileFormat(self, actionId, inpName="1"):
        """Get the file format for the specified action and output object.

           Returns:

           The file format if this is defined or None otherwise.

        """
        try:
            return self.__D[actionId]['OUTPUT_INFO_LIST'][inpName]['fileFormat']
        except:
            return None

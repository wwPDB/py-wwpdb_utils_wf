##
# File:    DataValueContainer.py
# Date:    28-Mar-2010
#
# Updates:
#
##
"""
Container for data values.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import types
from datetime import datetime, date


class DataValueContainer(object):

    """ Container for data values.

        Supported container types include:
        - individual bool, int, float, string, date, or datetime values
        - lists of bool, int, float, string,  date, datetime values

    """

    def __init__(self):
        super(DataValueContainer, self).__init__()
        # sys.stderr.write("DataValueContainer.__init_()\n")
        #
        self.__valueTypeName = None
        """ A supported data type name such:
            - boolean
            - int or integer
            - float or double
            - string
            - date
            - datetime
            """
        #
        self.__valueType = type(None)
        """ Intrinsic Python type corresponding to the valueTypeName.

            Types are defined in the Python class `types`.
        """
        #
        self.__containerTypeName = None
        """ Container type setting:
            - value, a single value
            - list,  a list/vector of values
            - dict,  a dictionary of key/values pairs

        """
        #
        self.__value = None

    def isValueValid(self):
        """ Performs a sanity type check on the current value and container types.

            Returns:

            True if value and container types correspond to the current type settings or False otherwise.
        """
        if self.__containerTypeName == 'list':
            if isinstance(self.__value, types.ListType):
                for v in self.__value:
                    if not isinstance(v, self.__valueType):
                        return False
                return True
            else:
                return False
        elif self.__containerTypeName == 'dict':
            if isinstance(self.__value, types.DictType):
                return True
            else:
                return False

        else:
            if isinstance(self.__value, self.__valueType):
                return True
            else:
                return False

    def isValueSet(self):
        """ Performs a check if the current data value has been set.

            Returns:

            True if the value has been set or False otherwise.

        """
        return (self.__value is not None)

    def setValue(self, value):
        self.__value = value

    def getValue(self):
        return self.__value

    def setValueTypeName(self, typeName):
        """Set the data type name for the container.

        Supported types include:
        - boolean
        - int or integer
        - float or double
        - string
        - date
        - datetime

        Returns:

        True if the input typeName is a supported type or False otherwise.
        """
        if (str(typeName) in ['boolean', 'int', 'integer', 'float', 'double', 'string', 'date', 'datetime']):
            self.__valueTypeName = str(typeName)
            if typeName == 'bool' or typeName == 'boolean':
                self.__valueType = types.BooleanType
            elif typeName == 'integer' or typeName == 'int':
                self.__valueType = types.IntType
            elif typeName == 'float' or typeName == 'double':
                self.__valueType = types.IntType
            elif typeName == 'string':
                self.__valueType = types.StringType
            elif typeName == 'date':
                tt = date(2010, 1, 1)
                self.__valueType = tt.__class__
            elif typeName == 'datetime':
                tt = datetime(2010, 1, 1)
                self.__valueType = tt.__class__
            else:
                return False
            return True
        else:
            return False

    def setContainerTypeName(self, containerName):
        """Set the container type name.

        Supported container types include:
        - value,  a individual value
        - list,   list or vector of values
        - dict,   dictionary of key,value pairs

        Returns:

        True for supported container types or False otherwise.

        """
        if (containerName in ['value', 'list', 'dict']):
            self.__containerTypeName = containerName
            return True
        else:
            return False

    def getContainerTypeName(self):
        return self.__containerTypeName

    def getValueTypeName(self):
        return self.__valueTypeName

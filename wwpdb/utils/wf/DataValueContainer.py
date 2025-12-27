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

# For python 2/3 compatible comparison with isinstace
from builtins import str  # noqa: UP029,A004
from datetime import date, datetime


class DataValueContainer:
    """Container for data values.

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
        """Performs a sanity type check on the current value and container types.

        Returns:

        True if value and container types correspond to the current type settings or False otherwise.
        """
        if self.__containerTypeName == "list":
            if isinstance(self.__value, list):
                for v in self.__value:  # noqa: SIM110
                    if not isinstance(v, self.__valueType):
                        return False
                return True
            return False
        if self.__containerTypeName == "dict":
            if isinstance(self.__value, dict):
                return True
            return False

        if isinstance(self.__value, self.__valueType):
            return True
        return False

    def isValueSet(self):
        """Performs a check if the current data value has been set.

        Returns:

        True if the value has been set or False otherwise.

        """
        return self.__value is not None

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
        - datetime -- no TZ aware form -- might need an update

        Returns:

        True if the input typeName is a supported type or False otherwise.
        """
        if str(typeName) in ["boolean", "int", "integer", "float", "double", "string", "date", "datetime"]:
            self.__valueTypeName = str(typeName)
            if typeName in ("bool", "boolean"):
                self.__valueType = bool
            elif typeName in ("integer", "int", "float", "double"):
                self.__valueType = int
            elif typeName == "string":
                self.__valueType = str
            elif typeName == "date":
                tt = date(2010, 1, 1)
                self.__valueType = tt.__class__
            elif typeName == "datetime":
                tt = datetime(2010, 1, 1)  # noqa: DTZ001
                self.__valueType = tt.__class__
            else:
                return False
            return True
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
        if containerName in ["value", "list", "dict"]:
            self.__containerTypeName = containerName
            return True
        return False

    def getContainerTypeName(self):
        return self.__containerTypeName

    def getValueTypeName(self):
        return self.__valueTypeName

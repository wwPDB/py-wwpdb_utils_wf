##
# File:    DataSelector.py
# Date:    5-April-2010
#
# Updates:
#
##
"""
Container for data selection criteria.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


class DataSelector(object):

    """A container for data selection criteria.

    A selector defines the following parameters:

    - targetCategoryName  name of category to which selection is applied
    - targetAttributeNameList [attributeName, attributeName,...] the values of the
      attributes in this list will be returned subject to the selection condition.

    Selection conditions are stored as a list of tuples of name, value and operator:

    - conditionList  [(attributeName,attributeValue,comparisonOp),,...]

    """

    def __init__(self):
        super(DataSelector, self).__init__()
        # self.__verbose = False
        # sys.stderr.write("DataSelector.__init_()\n")
        self.__selectorType = None
        #
        self.__targetCategoryName = None
        self.__targetAttributeList = []
        self.__selectConditionList = []

    def getSelectorType(self):
        """Get the type of selector type.  Currently only attribute value selections are supported."""
        return self.__selectorType

    def setSelectCategoryName(self, categoryName):
        """Set the target category for this selection.

        Returns:

        True for success or False otherwise
        """
        try:
            self.__targetCategoryName = categoryName
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getSelectCategoryName(self):
        """Get the taget category for this selection."""
        return self.__targetCategoryName

    def addSelectAttributeName(self, attributeName):
        """Add an attribute to the list of attributes for this selection.

        Returns:

        True for success or False otherwise
        """
        try:
            if attributeName not in self.__targetAttributeList:
                self.__targetAttributeList.append(attributeName)
                self.__selectorType = "attribute"
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getSelectAttributeList(self):
        """Get the list attributes for the current selection"""
        return self.__targetAttributeList

    def addSelectCondition(self, attributeName, attributeValue, comparisonOp="equal"):
        """Add a selection condition to the current selection.

        A selection condition contains the following:
        - attributeName in the target category.
        - attributeValue
        - one of the comparison operators (equals, ...)

        Returns:

        True for success or False otherwise.

        """
        try:
            self.__selectConditionList.append((attributeName, attributeValue, comparisonOp))
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def getSelectConditionList(self):
        """Get the list selection conditions."""
        return self.__selectConditionList

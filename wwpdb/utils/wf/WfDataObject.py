##
# File:    WfDataObject.py
# Date:    5-April-2010
#
# Updates:
#    1-May-2015  jdw   add common output method
#    7-Sep-2015  jdw   add __str__ and __repl__
#
##
"""
Mixin container the workflow data object.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

try:
    import cStringIO as StringIO
except ImportError:
    import io as StringIO

from wwpdb.utils.wf.DataSelector import DataSelector
from wwpdb.io.locator.DataReference import DataFileReference
from wwpdb.utils.wf.DataValueContainer import DataValueContainer


class WfDataObject(DataSelector, DataValueContainer, DataFileReference):

    """Top-level container for workflow data object.

    This container includes some combination of the following:
    - A data file reference (`DataFileReference`)
    - A data value container (`DataValueContainer`)
    - A data selector (`DataSelector`)

    """

    # Inherit base __init__
    # def __init__(self):
    #    super(WfDataObject, self).__init__()
    # self.__verbose = False
    # sys.stderr.write("WfDataObject.__init_()\n")

    def printMe(self, ofh):
        if self.getReferenceType() in ["file"]:
            ofh.write("+WfDataObject.printMe() reference type    %s\n" % self.getReferenceType())
            ofh.write("+WfDataObject.printMe() version ID        %s\n" % self.getVersionId())
            ofh.write("+WfDataObject.printMe() data set ID       %s\n" % self.getDepositionDataSetId())
            ofh.write("+WfDataObject.printMe() partition number  %s\n" % self.getPartitionNumber())
            ofh.write("+WfDataObject.printMe() content type      %s\n" % self.getContentType())
            ofh.write("+WfDataObject.printMe() file format       %s\n" % self.getFileFormat())
            ofh.write("+WfDataObject.printMe() storage type      %s\n" % self.getStorageType())
            ofh.write("+WfDataObject.printMe() directory path    %s\n" % self.getDirPathReference())
            ofh.write("+WfDataObject.printMe() file path         %s\n" % self.getFilePathReference())
            if self.getSelectorType() is not None:
                ofh.write("+WfDataObject.printMe() selector type     %s\n" % self.getSelectorType())
                ofh.write("+WfDataObject.printMe() select category   %s\n" % self.getSelectCategoryName())
                ofh.write("+WfDataObject.printMe() select attributes %r\n" % self.getSelectAttributeList())
                ofh.write("+WfDataObject.printMe() select conditions %r\n" % self.getSelectConditionList())
        elif self.getContainerTypeName() in ["value", "list", "dict"]:
            ofh.write("+WfDataObject.printMe() container type %s\n" % self.getContainerTypeName())
            ofh.write("+WfDataObject.printMe() value type     %s\n" % self.getValueTypeName())
            ofh.write("+WfDataObject.printMe() is value set   %r\n" % self.isValueSet())
            ofh.write("+WfDataObject.printMe() is value valid %r\n" % self.isValueValid())
            ofh.write("+WfDataObject.printMe() data value     %r\n" % self.getValue())
        else:
            ofh.write("+WfDataObject.printMe() undefined data object\n")

    def __str__(self):
        output = StringIO.StringIO()
        self.printMe(ofh=output)
        contents = output.getvalue()
        output.close()
        return contents

    def __repr__(self):
        output = StringIO.StringIO()
        self.printMe(ofh=output)
        contents = output.getvalue()
        output.close()
        return contents


if __name__ == "__main__":
    wfd = WfDataObject()

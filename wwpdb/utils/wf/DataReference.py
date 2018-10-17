##
# File:    DataReference.py
# Date:    30-Mar-2010
#
#
# Updates:
#  17-Apr-2010 - jdw add isReferenceValid()
#  29-Apr-2010 - jdw add support for director references.
#  13-Sep-2010 - jdw added getFilePathExists()
#  29-Jun-2011 - jdw fix version sorting issue
#  25-Feb-2013   jdw provided defaulted siteId/verbose/log in DataFileReference constructor
#  26-Feb-2013   jdw added session/wf-session storage type.
#  02-Mar-2013   jdw add class ReferenceFileInfo()
#  02-Mar-2013   jdw added class ReferenceFileComponents()
#  05-Mar-2013   jdw add initialization for session data set id.
#  07-Mar-2013   jdw make sesssion data set ids always upper case.
#  22-Mar-2013   jdw make files in workflow instance storage use the deposition data set id as
#                    leading file name element
#  25-Mar-2013   jdw make session data set id distinct from archive/workflow depositionDataSetId.
#  21-May-2013   jdw add deposit storage type
#  19-Sep-2013   jdw fix issues in ReferenceFileComponents and ReferenceFileInfo
#  26-Feb-2014   jdw adjust debugging output
#  10-Mar-2014   jdw add support for symbolic partition information.
#  28-Jun-2014   jdw make getPartitionNumberSearchTarget() public add  getVersionIdSearchTarget()
#   5-Jul-2014   jdw add getContentTypeSearchTarget()
#  14-Sep-2014   jdw add contentTypeExists(contentType)
#  29-Apr-2015   jdw add inline storage type for internal workflow variables -
#   7-May-2015   lm  add tempdep storage type
#  17-May-2015   jw  Restore method call with typo in name - getDepositonDataSetId()
#  30-Aug-2015   jw  Fix typo in method name in class ReferenceFileComponents
#   2-Sep-2015   jdw add accessor for supported storageTypes
#  23-Oct-2017   jdw add logging
##
"""
Classes defining references and naming conventions for data resources.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Apache 2.0"
__version__ = "V0.01"

import os
import sys
import string
import glob
import traceback
#
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoData import ConfigInfoData

import logging
logger = logging.getLogger(__name__)


class DataReferenceBase(object):

    """ Base class for data references such as files, web services and
        database services.

    """

    def __init__(self):
        self._referenceType = None

    def setReferenceType(self, refType):
        self._referenceType = refType

    def getReferenceType(self):
        return self._referenceType


class ReferenceFileInfo(object):

    """ Accessors for nomenclature conventions for reference files.
    """

    def __init__(self, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__ciD = ConfigInfoData(siteId=None, verbose=self.__verbose, log=self.__lfh).getConfigDictionary()
        #
        self.__contentD = self.__ciD['CONTENT_TYPE_DICTIONARY']
        self.__formatD = self.__ciD['FILE_FORMAT_EXTENSION_DICTIONARY']
        #
        self.__acronymD = {}
        for k, v in self.__contentD.items():
            self.__acronymD[v[1]] = k
        #
        self.__extD = {}
        for fmt, ext in self.__formatD.items():
            if ext not in self.__extD:
                self.__extD[ext] = []
            self.__extD[ext].append(fmt)
        #

    def contentTypeExists(self, contentType):
        try:
            return (contentType in self.__contentD.keys())
        except Exception as e:
            return False

    def getContentType(self, acronymName):
        try:
            return self.__acronymD[acronymName]
        except Exception as e:
            return None

    def getFormatTypes(self, contentType):
        try:
            return self.__contentD[contentType][0]
        except Exception as e:
            return []

    def getContentTypeAcronym(self, contentType):
        try:
            return self.__contentD[contentType][1]
        except Exception as e:
            return None

    def getExtensionFormats(self, extension):
        try:
            return self.__extD[extension]
        except Exception as e:
            return []

    def dump(self, ofh):
        ofh.write("\n+RefernceFileInfo.dump() content dictionary %r\n" % self.__contentD.items())

        for k in sorted(self.__acronymD.keys()):
            v = self.__acronymD[k]
            ofh.write("\n+RefernceFileInfo.dump() acronym %s contentType %s\n" % (k, v))

        ofh.write("\n+RefernceFileInfo.dump() extension dictionary %r\n" % self.__extD.items())


class ReferenceFileComponents(object):

    """ Provides methods for deconstructing  reference file names in terms of
        of their constituent attributes.
    """

    def __init__(self, fileName=None, verbose=False, log=sys.stderr):
        self.__fileName = fileName
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        self.__reset()

        self.__rfI = ReferenceFileInfo(verbose=self.__verbose, log=self.__lfh)
        if self.__fileName is not None:
            self.__splitFileName()

    def __reset(self):
        self.__depositionDataSetId = None
        self.__filePartNumber = None
        self.__contentType = None
        self.__contentTypeAcronym = None
        self.__contentFormat = None
        self.__versionId = None

    def set(self, fileName):
        self.__fileName = fileName
        self.__reset()
        return self.__splitFileName()

    def get(self):
        """ Convenience method returning the elements of the reference file name
            in a single tuple.
        """
        return (self.__depositionDataSetId,
                self.__contentType,
                self.__contentFormat,
                self.__filePartNumber,
                self.__versionId)

    def __splitFileName(self):
        """ Internal method to decompose reference file name into components.
        """
        self.__reset()

        try:
            fFields = str(self.__fileName).strip().split('.')
            baseName = str(fFields[0]).strip()
            self.__formatExt = str(fFields[1]).strip()
            if (len(fFields) > 2):
                self.__versionId = int(str(fFields[2][1:]))

            nFields = baseName.split('_')
            self.__depositionDataSetId = str(nFields[0] + '_' + nFields[1]).upper()
            #
            if (self.__debug):
                logger.debug("+DataFileReferenceComponents.__splitFileName() fields %r\n" % nFields)
            #
            if self.__rfI.contentTypeExists(str(nFields[2])):
                self.__contentTypeAcronym = str(nFields[2])
                self.__contentType = str(nFields[2])
            else:

                self.__contentTypeAcronym = str(nFields[2])
                self.__contentType = self.__rfI.getContentType(self.__contentTypeAcronym)
            #
            self.__filePartNumber = int(nFields[3][1:])

            fList = self.__rfI.getFormatTypes(self.__contentType)
            fmtList = self.__rfI.getExtensionFormats(self.__formatExt)
            for fmt in fmtList:
                if fmt in fList:
                    self.__contentFormat = fmt
            return True
        except Exception as e:
            if (self.__debug):
                logger.debug("+DataFileReferenceComponents.__splitFileName() failed for %r\n" % self.__fileName)
                traceback.print_exc(self.__lfh)
        return False

    def getVersionId(self):
        """ Return version identifier (integer), current symbolic setting, or None
        """
        return self.__versionId

    def getDepositionDataSetId(self):
        """ Return the data set identier -  (uppoer case)
        """
        return self.__depositionDataSetId

    def getDepositonDataSetId(self):
        """ Return the data set identier -  (uppoer case)
        """
        return self.__depositionDataSetId

    def getPartitionNumber(self):
        """  Return the file partition number (integer)  or symbolic setting.
        """
        return self.__filePartNumber

    def getContentTypeAcronym(self):
        """  Return the content type acronym
        """
        self.__contentTypeAcronym

    def getContentType(self):
        """ Return the content type
        """
        return self.__contentType

    def getContentFormat(self):
        """ Return the content format using content acronym and file extension.
        """
        return self.__contentFormat


class DataFileReference(DataReferenceBase):

    """
    """

    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        super(DataFileReference, self).__init__()
        #
        self.__siteId = siteId
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        #
        self.__cI = ConfigInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #
        self.__contentType = None
        """A supported content type:
           - model
           - structure-factors
           - nmr-restraints
           - em-volume
           - others to be enumerated
           """
        self.__fileFormat = None
        """A supported file format:
           - pdbx/mmcif
           - pdb
           - pdbml
           - nmr-star
           - others to be enumerated
           """
        self.__storageType = None
        """Storage type:
           - archive or wf-archive
           - wf-instance
           - wf-shared
           - deposit
           - tempdep
           - session or wf-session
           - inline
           - others to be enumerated
           """
        self.__versionId = None
        """Version identifier:
           - latest
           - orginal
           - next
           - previous
           - version number (1,2,...,)
           """
        #
        self.__filePartNumber = 1
        """Placeholder for future integer index for file partitioning.
        """
        #
        self.__depositionDataSetId = None
        """Deposition data set identifier (e.g. D_123456)
        """
        self.__workflowInstanceId = None
        """Workflow instance identifier (e.g. W_123456)
        """
        #
        self.__workflowNameSpace = None
        """Workflow name space identifier (alpha-numeric character string)
        """
        #
        self.__contentInfoD = self.__cI.get('CONTENT_TYPE_DICTIONARY')
        """Dictionary of supported file formats for each recognized content type.
           An acronym for each content type is included.
        """
        #
        self.__formatExtensionD = self.__cI.get('FILE_FORMAT_EXTENSION_DICTIONARY')
        """Dictionary of recognized file formats and file name extensions"""
        #
        self.__storageTypeList = ['archive', 'autogroup', 'wf-archive', 'wf-instance', 'wf-shared', 'session', 'wf-session', 'deposit', 'inline', 'tempdep']
        """List of supported storage types/locations"""
        #
        self.__depositionDataSetIdPrefix = "D_"
        """A depostion data set identifier begins with this prefix and is followed
           by a string of digits (e.g. D_123456789)"""
        #
        self.__groupDataSetIdPrefix = "G_"
        """A group data set identifier begins with this prefix and is followed
           by a string of digits (e.g. G_1234567)"""
        #
        self.__workflowInstanceIdPrefix = "W_"
        """A workflow instance identifier begins with this prefix and is followed
           by a string of digits (e.g. W_123456789)"""
        #
        self.__versionNameList = ['latest', 'original', 'previous', 'next', 'none']
        self.__partitionNameList = ['latest', 'original', 'previous', 'next', 'none']
        #
        #
        self.__externalFilePath = None
        """Placeholder for referencing a file name that is *external* to the archive
           or workflow system.  Setting this path implies a content type of *external*
           and other attributes of the reference will be treated as unknown/unassignable.
        """
        self.__sessionPath = '.'
        """Optional path used as a file system directory for any files with 'session' storage type.

           The default value for the session storage is the current directory.
        """
        self.__sessionDataSetId = None
        """Optional session data set identifier (e.g. 1abc)
        """

        #

    def getSitePrefix(self):
        """Returns:

           Current setting of the site prefix.

        """
        return self.__cI.get("SITE_PREFIX")

    def setSessionPath(self, dirPath=None):
        """Set the full directory path for 'session' type storage.  The 'session' feature provides
           a means to support workflow file naming conventions for applications with transient
           storage requirements.

           Returns True for any non-null argument.  No check is performed for the existence of
           this path on input.
        """
        if dirPath is not None:
            self.__sessionPath = dirPath
            return True
        else:
            return False

    def setExternalFilePath(self, filePath, fileFormat='any'):
        """Set the full file path for this reference outside of the archive/workflow system.
           Other identifying attributes of this file reference are ignored/by-passed when
           this path is set.   This feature is provided to permit external data with alternative
           file name conventions to be used within data file references.

           File format may be optionall specified and must correspond to a supported
           format or the defaule 'any'.

           Returns:

           True if the assignment was successful or False otherwise.

        """
        if ((filePath is None) or (len(filePath) < 1)):
            return False

        if fileFormat in self.__formatExtensionD.keys():
            self.__fileFormat = fileFormat
        else:
            return False
        #
        # reset attributes -
        #
        self.__contentType = None
        self.__storageType = None
        self.__versionId = None
        self.__filePartNumber = 1
        self.__depositionDataSetId = None
        self.__workflowInstanceId = None
        self.__workflowNameSpace = None
        #
        self.__externalFilePath = None
        #
        try:
            self.__externalFilePath = os.path.abspath(filePath)
            (pth, fn) = os.path.split(self.__externalFilePath)
            if pth is None or fn is None:
                return False
            return True
        except Exception as e:
            pass

        return False

    def setContentTypeAndFormat(self, contentType, fileFormat):
        """Set the content type and file format for the file reference.

           Examples of supported content types include:
           - model
           - structure-factors
           - nmr-restraints
           - nmr-chemical-shifts
           - component-image
           - component-definition
           - validation-report
           - em-volume

           Supported formats for each content type are defined in file format
           dictionary (`self.__contentInfoD`).

           Returns:

           True for a recognized content type  or False otherwise.
           """
        tS = str(contentType).lower()
        try:
            self.__contentInfoD.keys()
        except Exception as e:
            logger.exception("Failing with %r" % str(e))

        if tS in self.__contentInfoD.keys():
            self.__contentType = tS
            fS = str(fileFormat).lower()
            if(fS in self.__contentInfoD[tS][0]) or ('any' in self.__contentInfoD[tS][0]):
                self.__contentType = tS
                self.__fileFormat = fS
                if self.__debug:
                    logger.debug("++setContentTypeAndFormat -- returning True with self.__contentType: %s \n" % (self.__contentType))
                    logger.debug("++setContentTypeAndFormat -- returning True with self.__fileFormat: %s \n" % (self.__fileFormat))
                self.setReferenceType('file')
                return True
            else:
                if self.__debug:
                    logger.debug("++setContentTypeAndFormat -- returning False with tS: %s \n" % (tS))
                    logger.debug("++setContentTypeAndFormat -- returning False with fS: %s \n" % (fS))
                return False
        else:
            if self.__debug:
                logger.debug("++setContentTypeAndFormat -- unrecognized cotentent type %r\n" % tS)
            return False

    def getStorageTypeList(self):
        return self.__storageTypeList

    def setStorageType(self, type):
        """Set the storage type for this file reference.

           Supported storage types include:
           - archive or wf-archive
           - wf-instance
           - wf-shared
           - deposit
           - tempdep
           - session or wf-session

           Returns:

           True for a recognized storage type or False otherwise.

        """
        tS = str(type).lower()
        if tS in self.__storageTypeList:
            self.__storageType = tS
            if tS not in ['inline', 'constant']:
                self.setReferenceType('file')
            return True
        else:
            return False

    def setVersionId(self, versionId):
        """Set the version identifier for this file reference.

           Supported version identifiers include:
           - latest, ...
           - orginal
           - an integer version number (1,2,...,)

           Returns:

           True for a valid version identifier or False otherwise.

        """
        tS = str(versionId).lower()
        if versionId in self.__versionNameList:
            self.__versionId = tS
            return True
        elif (self.__isInteger(tS)):
            self.__versionId = tS
            return True
        else:
            return False

    def __isInteger(self, str):
        """ Is the given string an integer?	"""
        ok = True
        try:
            num = int(str)
        except ValueError:
            ok = False
        return ok

    def setDepositionDataSetId(self, dId):
        """Set the deposition data set identifier.

        A depostion data set identifier begins with the prefix *D_* and is followed
        by a string of digits (e.g. D_123456789).

        Returns:

        True if the input identifier is a properly formed identifier
        or False otherwise.

        """
        tS = str(dId).upper()
        if (not tS.startswith(self.__depositionDataSetIdPrefix)) and (not self.__groupDataSetIdPrefix):
            return False
        tSL = tS.split('_')
        if ((len(tSL) > 1) and self.__isInteger(tSL[1])):
            self.__depositionDataSetId = tS
            return True
        else:
            return False

    def setWorkflowInstanceId(self, wId):
        """Set the workflow instance identifier.

        A workflow instance identifier begins with the prefix *W_* and is followed
        by a string of digits (e.g. W_123456789)

        Returns:

        True if the input identifier is a properly formed identifier
        or False otherwise.

        """
        tS = str(wId).upper()
        if not tS.startswith(self.__workflowInstanceIdPrefix):
            return False
        tSL = tS.split('_')
        if ((len(tSL) > 1) and self.__isInteger(tSL[1])):
            self.__workflowInstanceId = tS
            return True
        else:
            return False

    def setSessionDataSetId(self, sId):
        """Set the session data set identifier.

        Data set identifier applied for session storage. No conventions are
        assumed for this identifier.

        Returns:

        True if the input identifier is non-blank
        or False otherwise.

        """
        if sId is not None and len(sId) > 0:
            self.__sessionDataSetId = str(sId).upper()
            return True
        else:
            return False

    def setWorkflowNameSpace(self, wNameSpace):
        """Set the workflow name space identifier.

           This identifier must be an alpha numeric string containing only
           characters [a-zA-Z0-9].

           Returns:

           True if the input identifier is a properly formed identifier
           or False otherwise.

        """
        if ((wNameSpace is None) or (len(str(wNameSpace)) < 1)):
            return False
        for cv in str(wNameSpace):
            if ((cv not in string.letters) and (cv not in string.digits)):
                return False
        self.__workflowNameSpace = wNameSpace
        return True

    def setPartitionNumber(self, iPartitionNumber=1):
        """Set the integer file partition number.  This is used to identify the physical
           pieces of a single logical data file.

           Supported values for partition include:
           - latest, ...
           - orginal
           - an integer version number (1,2,...,)

           Returns:

           True if the input partition is properly formed or False otherwise.

        """
        ok = False
        try:
            tS = str(iPartitionNumber).lower()
            if iPartitionNumber in self.__partitionNameList:
                self.__filePartNumber = tS
                ok = True
            elif (self.__isInteger(tS)):
                self.__filePartNumber = int(tS)
                ok = True
            else:
                ok = False
        except Exception as e:
            ok = False
        if (self.__debug):
            logger.debug("+DataFileReference.setPartitionNumber() setting is  %r\n" % self.__filePartNumber)
        return ok

    def getPartitionNumber(self):
        """Returns:

           The current partition number  or *1* if this is not set.
        """
        return self.__filePartNumber

    def getContentType(self):
        """Returns:

           The current content type or *None* if this is not set.
        """
        return self.__contentType

    def getFileFormat(self):
        """Returns:

           The current file format or *None* if this is not set.
        """
        return self.__fileFormat

    def getStorageType(self):
        """Returns:

           The current storage type or *None* if this is not set.
        """

        return self.__storageType

    def getVersionId(self):
        """Returns:

           The current version identifier or *None* if this is not set.
        """
        return self.__versionId

    def getDepositionDataSetId(self):
        """Returns:

           The current deposition data set identifier  or *None* if this is not set.
        """
        return self.__depositionDataSetId

    def getWorkflowInstanceId(self):
        """Returns:

           The current workflow instance identifier  or *None* if this is not set.
        """
        return self.__workflowInstanceId

    def getWorkflowNameSpace(self):
        """Returns:

           The current workflow name space identifier  or *None* if this is not set.
        """
        return self.__workflowNameSpace

    #
    # ------------------------------------------------------------------------------------------------------------------------------------
    #
    # --- The following public methods derive information from the settings in the previous methods --
    #

    def isReferenceValid(self):
        """Test if the reference information is complete and the data reference is valid.

           Valid references are:

           - A path external to the archive/worflow system
           - A fully defined internal reference consisting or identifiers,
             content type, storage type, format, and version.

           Note that this is NOT an existence test.  References may be defined and validated
           before the file objects which they reference are created.

           Returns:

           True for either a valid external or internal reference or False otherwise.

        """
        if (self.__externalFilePath is not None):
            return True
        else:
            return (self.__isInternalReferenceValid())

    def getDirPathReference(self):
        """ Get the path to the directory containing the data file reference.

            Returns:

            The file system path to the directory containing the file reference or *None*
            if this cannot be determined.

        """
        if (self.__externalFilePath is not None):
            return self.__externalFilePath
        # if (self.__isInternalReferenceValid()):
        #    return self.__getInternalPath()
        else:
            return self.__getInternalPath()

    def getFilePathReference(self):
        """Get the versioned file path for an internal data file reference or the path
           to an external data file reference.

           Returns:

           The file system path to the file reference or *None* if this cannot be determined.

        """
        if (self.__externalFilePath is not None):
            return self.__externalFilePath
        if (not self.__isInternalReferenceValid()):
            return None
        return (self.__getInternalFilePath())

    def getFilePathExists(self, fP):
        try:
            if os.access(fP, os.R_OK):
                return True
            else:
                return False
        except Exception as e:
            if self.__verbose:
                traceback.print_exc(self.__lfh)
            return False

    def getFileVersionNumber(self):
        """Get the version number corresponding to the current data file reference.

           Returns:

           The version number 1-N of the current data reference or 0 otherwise.
           External references are treated as having no version and 0 is returned for
           these cases.

        """

        if (self.__externalFilePath is not None):
            return 0
        if (not self.__isInternalReferenceValid()):
            return 0
        return (self.__getInternalVersionNumber())

    #
    # ------------------------------------------------------------------------------------------------------------------------------------
    #
    # --- The following private worker methods support the public path and validation methods.
    #

    def __isInternalReferenceValid(self):
        """Test if the current reference information is complete for an internal reference.
           A reference is considered internal which points within the archive, workflow
           instance, deposit or session file systems.  Otherwise the reference is considered external
           and not subject to internal naming or path conventions.

           Note that this is NOT an existence test.  References may be defined and validated
           before the file objects which they reference are created.

           Returns:

           True if the internal reference is complete or False otherwise.
        """
        referenceType = self.getReferenceType()

        if (referenceType == 'file'):
            if ((self.__contentType is None) or
                    (self.__fileFormat is None) or
                    (self.__storageType is None) or
                    (self.__versionId is None)):
                    # logger.debug("self.__contentType is: %s \n" % (self.__contentType))
                    # logger.debug("self.__fileFormat is: %s \n" % (self.__fileFormat))
                    # logger.debug("self.__storageType is: %s \n" % (self.__storageType))
                    # logger.debug("self.__versionId is: %s \n" % (self.__versionId))

                return False

            if ((self.__storageType in ['archive', 'autogroup', 'wf-archive', 'wf-instance', 'wf-shared', 'deposit', 'tempdep']) and (self.__depositionDataSetId is None)):
                logger.debug("self.__depositionDataSetId is: %s \n" % (self.__depositionDataSetId))
                return False

            if ((self.__storageType in ['session', 'wf-session']) and (self.__sessionDataSetId is None)):
                return False

            if ((self.__storageType == 'wf-instance') and (self.__workflowInstanceId is None)):
                return False

            if ((self.__storageType == 'wf-shared') and (self.__workflowNameSpace is None)):
                return False

            return True

        elif (referenceType == 'directory'):
            if (self.__storageType is None):
                return False

            if ((self.__storageType in ['archive', 'autogroup', 'wf-archive', 'wf-instance', 'wf-shared', 'deposit', 'tempdep']) and
                    (self.__depositionDataSetId is None)):
                return False

            if ((self.__storageType == 'wf-instance') and (self.__workflowInstanceId is None)):
                return False

            if ((self.__storageType == 'wf-shared') and (self.__workflowNameSpace is None)):
                return False

            if ((self.__storageType in ['wf-session', 'session']) and (self.__sessionPath is None)):
                return False

            return True

        else:
            return False

    def __getExternalPath(self):
        """Get the path of the current external file reference.

           Returns:

           The external file path.  *None* is returned on failure.
        """
        try:
            (pth, fn) = os.path.split(self.__externalFilePath)
            return pth
        except Exception as e:
            return None

    def __getExternalFileNameBase(self):
        """Get the base file name for the current external file reference.

           Returns:

           The external base file name.  *None* is returned on failure.
        """
        try:
            (pth, fn) = os.path.split(self.__externalFilePath)
            return fn
        except Exception as e:
            return None

    def __getInternalPath(self):
        """Compute the path to the current file reference within the archive/workflow file system.

        The file path convention is:
        - archive files     = <SITE_ARCHIVE_STORAGE_PATH>/archive/<deposition data set id>/
        - deposit files     = <SITE_DEPOSIT_STORAGE_PATH>/archive/<deposition data set id>/
        - temp deposit files     = <SITE_TEMPDEP_STORAGE_PATH>/tempdep/<deposition data set id>/
        - workflow shared   = <SITE_WORKFLOW_STORAGE_PATH>/workflow/<deposition data set id>/shared/<self.__workflowNameSpace>
        - workflow instance = <SITE_WORKFLOW_STORAGE_PATH>/workflow/<deposition data set id>/instance/<self.__workflowInstanceId>
        - session files     = session path/

        Top-level site-specific path details are obtained from the SiteInfo() class.

        Returns:

        The path of the directory containing this data file reference.  *None* is returned on failure.

        """
        try:
            if (self.__storageType == 'archive' or self.__storageType == 'wf-archive'):
                tpth = os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'archive', self.__depositionDataSetId)
            elif (self.__storageType == 'autogroup'):
                tpth = os.path.join(self.__cI.get('SITE_DEPOSIT_STORAGE_PATH'), 'autogroup', self.__depositionDataSetId)
            elif (self.__storageType == 'deposit'):
                tpth = os.path.join(self.__cI.get('SITE_DEPOSIT_STORAGE_PATH'), 'deposit', self.__depositionDataSetId)
            elif (self.__storageType == 'tempdep'):
                tpth = os.path.join(self.__cI.get('SITE_TEMPDEP_STORAGE_PATH'), 'tempdep', self.__depositionDataSetId)
            elif (self.__storageType == 'wf-shared'):
                tpth = os.path.join(self.__cI.get('SITE_WORKFLOW_STORAGE_PATH'), 'workflow', self.__depositionDataSetId, 'shared', self.__workflowNameSpace)
            elif (self.__storageType == 'wf-instance'):
                tpth = os.path.join(self.__cI.get('SITE_WORKFLOW_STORAGE_PATH'), 'workflow', self.__depositionDataSetId, 'instance', self.__workflowInstanceId)
            elif (self.__storageType in ['session', 'wf-session']):
                tpth = self.__sessionPath
            else:
                tpth = None
            pth = os.path.abspath(tpth)
        except Exception as e:
            logger.exception("Failing with %r" % str(e))

            pth = None

        return pth

    def __getInternalFileNameBase(self):
        """Compute the base file name based on the current values of storage type, identifer, content type, file format.

        The file name convention is:
        - archive/shared  files  = <deposition data set id>_<content acronym>_<part number>.<format_extenstion>
        - instance files         = <deposition data set id>_<content acronym>_<part number>.<format_extension>
        - session  files         = <session data set id>_<content acronym>_<part number>.<format_extenstion>

        Returns:

        The base file name. This base file name lacks version details.

        """

        try:
            if (self.getReferenceType() != 'file'):
                return None

            if self.__storageType in ['archive', 'autogroup', 'wf-archive', 'wf-shared', 'deposit', 'tempdep']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P' + \
                    str(self.__filePartNumber) + '.' + \
                    self.__formatExtensionD[self.__fileFormat]
            elif self.__storageType in ['session', 'wf-session']:
                fn = self.__sessionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P' + \
                    str(self.__filePartNumber) + '.' + \
                    self.__formatExtensionD[self.__fileFormat]
            elif self.__storageType in ['wf-instance']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P' + \
                    str(self.__filePartNumber) + '.' + \
                    self.__formatExtensionD[self.__fileFormat]
            else:
                fn = None
        except Exception as e:
            logger.exception("Failing with %r" % str(e))
            fn = None

        return fn

    def __getInternalFilePath(self):
        """Compute the versioned file path for a file within the archive/worflow file system.

           If either the *latest*, *next*, or *previous* version of the referenced file is
           selected then a file system check is performed to determine the appropriate
           version number.

        Returns:

        File path including version or None on failure.
        """

        try:
            if (self.getReferenceType() != 'file'):
                return None
            dirPath = self.__getInternalPath()
            fN = self.__getInternalFileNameVersioned()
            pth = os.path.join(dirPath, fN)
            return pth
        except Exception as e:
            return None

    def getVersionIdSearchTarget(self):
        """  Create a search target for the files containing any version identifier consistent with the
             current file settings.

             Returns a the search target appropriate for glob() or None
        """
        try:
            if (self.getReferenceType() != 'file'):
                return None
            baseName = self.__getInternalFileNameBase()
            vst = baseName + ".V*"
            return vst
        except Exception as e:
            return None

    def __getInternalFileNameVersioned(self):
        """Compute the versioned file name for a file within the archive/worflow file system.

           If either the *latest*, *next*, or *previous* version of the referenced file is
           selected then a file system check is performed to determine the appropriate
           version number.

        Returns:

        File name including version or None on failure.
        """
        try:
            if (self.getReferenceType() != 'file'):
                return None
            dirPath = self.__getInternalPath()
            #
            # First resolve any symbolic partition information -
            #
            self.__filePartNumber = self.__getInternalPartitionNumber()
            #
            baseName = self.__getInternalFileNameBase()
            if self.__versionId == 'latest':
                iV = self.__latestVersion(dirPath, baseName)
                if (iV == 0):
                    # No version exists so start at 1
                    fn = baseName + '.V1'
                else:
                    #
                    fn = baseName + '.V' + str(int(iV))

            elif self.__versionId == 'next':
                iV = self.__latestVersion(dirPath, baseName)
                if (iV == 0):
                    # No version exists so start at 1
                    fn = baseName + '.V1'
                else:
                    #
                    fn = baseName + '.V' + str(int(iV + 1))

            elif self.__versionId == 'previous':
                iV = self.__latestVersion(dirPath, baseName)
                if (iV <= 2):
                    # No previous version.
                    fn = None
                else:
                    #
                    fn = baseName + '.V' + str(int(iV - 1))

            elif self.__versionId == 'original':
                fn = baseName + '.V1'
            elif self.__versionId == 'none':
                fn = baseName
            else:
                fn = baseName + '.V' + str(int(self.__versionId))

            return fn
        except Exception as e:
            return None

    def __getInternalVersionNumber(self):
        """Determine the version number corresponding to the current version Id setting.

           If either the *latest*, *next*, or *previous* version of the referenced file is
           selected then a file system check is performed to determine the appropriate
           version number.

        Returns:

        Return a version number from 1-N   or 0 failure.
        """
        try:
            if (self.getReferenceType() != 'file'):
                return 0
            dirPath = self.__getInternalPath()
            self.__filePartNumber = self.__getInternalPartitionNumber()
            baseName = self.__getInternalFileNameBase()
            if self.__versionId == 'latest':
                iV = self.__latestVersion(dirPath, baseName)
            elif self.__versionId == 'next':
                iV = self.__latestVersion(dirPath, baseName)
                iV += 1
            elif self.__versionId == 'previous':
                iV = self.__latestVersion(dirPath, baseName)
                iV -= 1
                if (iV < 0):
                    iV = 0
            elif self.__versionId == 'original':
                iV = 1
            else:
                iV = int(self.__versionId)
            return iV
        except Exception as e:
            if self.__debug:
                logger.exception("Failing with %r" % str(e))
        return 0

    def __latestVersion(self, dirPath, baseName):
        """ Get the latest version of file *baseName* in path *dirPath*.

            The convention for version numbering is <baseName>.V#

            Returns:

            The latest integer version number  or 0 if no versions exist.

        """
        try:
            fN = None
            if (self.getReferenceType() != 'file'):
                return 0
            vList = []
            fileList = os.listdir(dirPath)
            for fN in fileList:
                # logger.debug("__latestVersion - baseName %s fN %s\n" % (baseName,fN))
                if fN.startswith(baseName):
                    fSp = fN.split('.V')
                    if ((len(fSp) < 2) or (not fSp[1].isdigit())):
                        continue
                    vList.append(int(fSp[1]))
                    # logger.debug("__latestVersion - vList %r\n" % (fSp))
            if len(vList) > 0:
                vList.sort()
                return vList[-1]
            else:
                return 0
        except Exception as e:
            if self.debug:
                logger.exception("Failing -dirPath %s  baseName %s fN %s with %s" % (dirPath, baseName, fN, str(e)))

        return 0

    ##
    ##
    def __latestPartitionNumber(self, dirPath, searchTarget):
        """ Get the latest partition number of file in path *dirPath*
            consistent with current file settings.

            Returns:

            The latest integer partition number  or 0 if no files exist.

        """
        try:
            fN = None
            if (self.getReferenceType() != 'file'):
                return 0
            pList = []
            searchPath = os.path.join(dirPath, searchTarget)
            if (self.__debug):
                logger.debug("+DataFileReference.__lastestPartitionNumber() search target %s\n" % searchPath)
            pathList = glob.glob(searchPath)
            for pth in pathList:
                if (self.__debug):
                    logger.debug("+DataFileReference.__lastestPartitionNumber() search path %s\n" % pth)
                (td, fN) = os.path.split(pth)
                fL1 = fN.split('.')
                fL2 = fL1[0].split('_')
                pList.append(int(fL2[3][1:]))

            if (self.__debug):
                logger.debug("+DataFileReference.__lastestPartitionNumber() part number list  %r\n" % pList)
            if len(pList) > 0:
                pList.sort()
                return pList[-1]
            else:
                return 0
        except Exception as e:
            if self.__debug:
                logger.exception("Failing with %r" % str(e))

        return 0

    def getPartitionNumberSearchTarget(self):
        """Create a search target for the files containing any partition number consistent with the
           current file settings.   The seach target is independent of version identifier.

        The file name convention is:
        - archive/shared  files  = <deposition data set id>_<content acronym>_P*.<format_extenstion>
        - instance files         = <deposition data set id>_<content acronym>_P*.<format_extension>
        - session  files         = <session data set id>_<content acronym>_P*.<format_extenstion>

        Returns:

        A search string appopriate for glob().

        """

        try:
            if (self.getReferenceType() != 'file'):
                return None

            if self.__storageType in ['archive', 'autogroup', 'wf-archive', 'wf-shared', 'deposit', 'tempdep']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*' + '.' + \
                    self.__formatExtensionD[self.__fileFormat] + '*'
            elif self.__storageType in ['session', 'wf-session']:
                fn = self.__sessionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*' + '.' + \
                    self.__formatExtensionD[self.__fileFormat] + '*'
            elif self.__storageType in ['wf-instance']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*' + '.' + \
                    self.__formatExtensionD[self.__fileFormat] + '*'
            else:
                fn = None
        except Exception as e:
            logger.exception("Failing with %r" % str(e))

            fn = None

        return fn

    def getContentTypeSearchTarget(self):
        """Create a search target for the files containing any variation consistent with the
           content type in current file settings.   The seach target is independent of partition,
           format and version identifier.

        The file name convention is:
        - archive/shared  files  = <deposition data set id>_<content acronym>_P*
        - instance files         = <deposition data set id>_<content acronym>_P*
        - session  files         = <session data set id>_<content acronym>_P*

        Returns:

        A search string appopriate for glob().

        """

        try:
            # if (self.getReferenceType() != 'file'):
            #  return None

            if self.__storageType in ['archive', 'autogroup', 'wf-archive', 'wf-shared', 'deposit', 'tempdep']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*'
            elif self.__storageType in ['session', 'wf-session']:
                fn = self.__sessionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*'
            elif self.__storageType in ['wf-instance']:
                fn = self.__depositionDataSetId + '_' + \
                    self.__contentInfoD[self.__contentType][1] + '_P*'
            else:
                fn = None
        except Exception as e:
            logger.exception("Failing storage %r data set id %r content type %r with %r\n" %
                             (self.__storageType, self.__depositionDataSetId, self.__contentType, str(e)))
            fn = None

        return fn

    def __getInternalPartitionNumber(self):
        """Determine the partition number corresponding to the current partition number setting.

           If either the *latest*, *next*, or *previous* version of the referenced file is
           selected then a file system check is performed to determine the appropriate
           partition number.

        Returns:

        Return a partition number from 1-N   or 0 failure.
        """
        try:
            if (self.getReferenceType() != 'file'):
                return 0
            dirPath = self.__getInternalPath()
            searchTarget = self.getPartitionNumberSearchTarget()
            if self.__filePartNumber == 'latest':
                iP = self.__latestPartitionNumber(dirPath, searchTarget)
            elif self.__filePartNumber == 'next':
                iP = self.__latestPartitionNumber(dirPath, searchTarget)
                iP += 1
            elif self.__filePartNumber == 'previous':
                iP = self.__latestPartitionNumber(dirPath, searchTarget)
                iP -= 1
                if (iP < 0):
                    iP = 0
            elif self.__filePartNumber == 'original':
                iP = 1
            else:
                iP = int(self.__filePartNumber)
            return iP
        except Exception as e:
            logger.exception("Failing with %r" % str(e))

        return 0

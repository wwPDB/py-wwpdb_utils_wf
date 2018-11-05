##
# File:    EmUtils.py
# Date:    10-Feb-2014
#
# Updates:
#
#    15-Aug-2014 JDW add mapFixInPlaceOp(self,**kwArgs)
#    31-Aug-2015 jdw add mapFixInPlaceAltOp()
#    02-Oct-2015 jdw add mapFixInPlaceCfgOp
#    07-Oct-2015 jdw change api call in mapFixInPlaceCfgOp to deposit-update-map-header-in-place
##
"""
Module of EM utility operations supporting the call protocol of the ProcessRunner() class.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import json
import traceback

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility
from wwpdb.io.locator.PathInfo import PathInfo


class EmUtils(UtilsBase):

    """ Utility class to run validation operations.

        Current supported operations include:

        - create PDF report and supporting XML data file

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
        super(EmUtils, self).__init__(verbose, log)
        self.__cleanUp = False
        """Flag to remove any temporary directories created by this class.
        """

    def fsc_check_options(self, **kwArgs):
        """
        Set the options for xmllint
        """

        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inputPath = inpObjD["src"].getFilePathReference()
            outPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = outObjD["dst2"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(inputPath)
            #  add any extra command line options
            options = str(uD['options'])
            if ((options is not None) and (len(options) > 0)):
                dp.addInput(name="options", value=options)

            ret = dp.op("fsc_check")
            dp.expLog(logPath)
            dp.exp(outPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.fsc_check_options() - input FSC file path:  %s\n" % inputPath)
                self._lfh.write("+EmUtils.fsc_check_options() - output FSC file path:  %s\n" % outPath)
                self._lfh.write("+EmUtils.fsc_check_options() - log file path:         %s\n" % logPath)

            if (self.__cleanUp):
                dp.cleanup()

            return ret
        except:
            traceback.print_exc(file=self._lfh)
            return -100

    def mapFixOp(self, **kwArgs):
        """Run mapfix (Prior BIG VERSION) to correct header values in input map.

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpMapPath = inpObjD["src"].getFilePathReference()
            outMapPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = outObjD["dst2"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(inpMapPath)
            #  add any extra command line options
            options = str(uD['options'])
            if ((options is not None) and (len(options) > 0)):
                dp.addInput(name="options", value=options)

            dp.op("mapfix-big")
            dp.expLog(logPath)
            dp.exp(outMapPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.mapFixOp() - input map  file path:  %s\n" % inpMapPath)
                self._lfh.write("+EmUtils.mapFixOp() - output map file path:  %s\n" % outMapPath)
                self._lfh.write("+EmUtils.mapFixOp() - log file path:         %s\n" % logPath)

            if (self.__cleanUp):
                dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def mapFixInPlaceOp(self, **kwArgs):
        """Run mapfix (BIG VERSION) to correct header values in input map (in place).

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpMapPath = inpObjD["src"].getFilePathReference()
            outMapPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            rptPath = outObjD["dst2"].getFilePathReference()
            logPath = outObjD["dst3"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setDebugMode(flag=True)
            # dp.imp(inpMapPath)
            #  add any extra command line options
            options = str(uD['options'])
            if ((options is not None) and (len(options) > 0)):
                dp.addInput(name="options", value=options)

            dp.addInput(name="input_map_file_path", value=inpMapPath)
            dp.addInput(name="output_map_file_path", value=outMapPath)
            dp.op("deposit-update-map-header-in-place")
            #dp.op("annot-update-map-header-in-place")
            dp.exp(rptPath)
            dp.expLog(logPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.mapFixInPlaceOp() - input map  file path:  %s\n" % inpMapPath)
                self._lfh.write("+EmUtils.mapFixInPlaceOp() - output map file path:  %s\n" % outMapPath)
                self._lfh.write("+EmUtils.mapFixInPlaceOp() - report file path:      %s\n" % rptPath)
                self._lfh.write("+EmUtils.mapFixInPlaceOp() - log file path:         %s\n" % logPath)
                self._lfh.write("+EmUtils.mapFixInPlaceOp() - command option:        %s\n" % options)

            if (self.__cleanUp):
                dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def em2emSpiderOp(self, **kwArgs):
        """Run em2em to convert Spider map to CCP4 format

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpMapPath = inpObjD["src"].getFilePathReference()
            outMapPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = outObjD["dst2"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(inpMapPath)
            #  add any extra command line options
            pixelSpacingX = 1.0
            pixelSpacingY = 1.0
            pixelSpacingZ = 1.0
            pixelSpacingX = str(uD['pixel-spacing-x'])
            pixelSpacingY = str(uD['pixel-spacing-y'])
            pixelSpacingZ = str(uD['pixel-spacing-z'])
            dp.addInput(name="pixel-spacing-x", value=pixelSpacingX)
            dp.addInput(name="pixel-spacing-y", value=pixelSpacingY)
            dp.addInput(name="pixel-spacing-z", value=pixelSpacingZ)
            #
            dp.op("em2em-spider")
            dp.expLog(logPath)
            dp.exp(outMapPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.em2emSpiderOp() - input map  file path:  %s\n" % inpMapPath)
                self._lfh.write("+EmUtils.em2emSpiderOp() - output map file path:  %s\n" % outMapPath)
                self._lfh.write("+EmUtils.em2emSpiderOp() - log file path:         %s\n" % logPath)

            if (self.__cleanUp):
                dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def mapFixInPlaceAltOp(self, **kwArgs):
        """ MapFix operation on input map (in place).

             - with automatic input and output map file selection -

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpMapPath = inpObjD["src1"].getFilePathReference()
            inpArgsPath = inpObjD["src2"].getFilePathReference()
            outMapPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            rptPath = outObjD["dst2"].getFilePathReference()
            logPath = outObjD["dst3"].getFilePathReference()
            #
            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.setDebugMode(flag=True)
            #
            #  add any extra command line options
            options = None
            try:
                ifh = open(inpArgsPath, 'r')
                options = ifh.read()
                ifh.close()
                dp.addInput(name="options", value=options)
            except:
                pass
            dp.addInput(name="input_map_file_path", value=inpMapPath)
            dp.addInput(name="output_map_file_path", value=outMapPath)
            dp.op("annot-update-map-header-in-place")
            dp.exp(rptPath)
            dp.expLog(logPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.mapFixOp() - input map  file path:         %s\n" % inpMapPath)
                self._lfh.write("+EmUtils.mapFixOp() - command line args file path:  %s\n" % inpArgsPath)
                self._lfh.write("+EmUtils.mapFixOp() - output map file path:         %s\n" % outMapPath)
                self._lfh.write("+EmUtils.mapFixOp() - report file path:             %s\n" % rptPath)
                self._lfh.write("+EmUtils.mapFixOp() - log file path:                %s\n" % logPath)
                self._lfh.write("+EmUtils.mapFixOp() - command option:               %s\n" % options)

            if (self.__cleanUp):
                dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def mapFixInPlaceCfgOp(self, **kwArgs):
        """ execution wrapper for mapfix operations for all maps of a particular type.

            --- using explicit data file selection via configuraton file selection.

                map-content-type = one of em-volume, em-mask-volume, em-half-volume, em-additional-volume
                partlist = [1,2,3]
                cmdline-arg-list = ['-voxel ...   ','-voxel .... ','-voxel .... ']



        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpCfgPath = inpObjD["src1"].getFilePathReference()
            dataSetId = inpObjD["src1"].getDepositionDataSetId()
            dirPath = inpObjD["src1"].getDirPathReference()
            storageType = inpObjD["src1"].getStorageType()
            #
            #  Read data configuration information ---
            arg = None
            cTupL = []
            try:
                cD = json.load(open(inpCfgPath, 'r'))
                pL = cD['part-list']
                inpMileStone = cD['map-content-milestone'] if 'map-content-milestone' in cD else None
                mapContentType = cD['map-content-type']
                cmdLineArgList = cD['cmd-line-arg-list']
                for p, arg in zip(pL, cmdLineArgList):
                    cTupL.append((p, mapContentType, arg))
            except:
                self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - failed processing configuration file  %s\n" % inpCfgPath)
                traceback.print_exc(file=self._lfh)

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            pI = PathInfo(siteId=siteId, verbose=self._verbose, log=self._lfh)

            for p, mT, arg in cTupL:
                inpMapPath = pI.getFilePath(dataSetId, contentType=mT, formatType='map', fileSource=storageType, versionId="latest", partNumber=p, mileStone=inpMileStone)
                outMapPath = pI.getFilePath(dataSetId, contentType=mT, formatType='map', fileSource=storageType, versionId="next", partNumber=p, mileStone=None)
                rptPath = pI.getFilePath(dataSetId, contentType="mapfix-header-report", formatType='json', fileSource=storageType, versionId="next", partNumber=p, mileStone=None)
                logPath = pI.getFilePath(dataSetId, contentType="mapfix-report", formatType='txt', fileSource=storageType, versionId="next", partNumber=p, mileStone=None)

                dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
                dp.setDebugMode(flag=True)
                dp.addInput(name="options", value=arg)
                dp.addInput(name="input_map_file_path", value=inpMapPath)
                dp.addInput(name="output_map_file_path", value=outMapPath)
                dp.op("deposit-update-map-header-in-place")
                dp.exp(rptPath)
                dp.expLog(logPath)

                if (self._verbose):
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - config file path:             %s\n" % inpCfgPath)
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - input map  file path:         %s\n" % inpMapPath)
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - output map file path:         %s\n" % outMapPath)
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - report file path:             %s\n" % rptPath)
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - log file path:                %s\n" % logPath)
                    self._lfh.write("+EmUtils.mapFixInPlaceCfgOp() - command option:               %s\n" % arg)

                if (self.__cleanUp):
                    dp.cleanup()
            return True
        except:
            traceback.print_exc(file=self._lfh)
            return False

    def imageMagickOp(self, **kwArgs):
        """
        Run ImageMagick to convert uploaded image to 400x400 (for atlas pages)

        """
        try:
            (inpObjD, outObjD, uD, pD) = self._getArgs(kwArgs)
            inpImgPath = inpObjD["src"].getFilePathReference()
            outImgPath = outObjD["dst1"].getFilePathReference()
            dirPath = outObjD["dst1"].getDirPathReference()
            logPath = outObjD["dst2"].getFilePathReference()

            cI = ConfigInfo()
            siteId = cI.get("SITE_PREFIX")
            dp = RcsbDpUtility(tmpPath=dirPath, siteId=siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(inpImgPath)

            #  add any extra command line options
            options = str(uD['options'])
            if ((options is not None) and (len(options) > 0)):
                dp.addInput(name="options", value=options)

            ret = dp.op("img-convert")
            dp.expLog(logPath)
            dp.exp(outImgPath)

            if (self._verbose):
                self._lfh.write("+EmUtils.imageMagickOp() - input image  file path:  %s\n" % inpImgPath)
                self._lfh.write("+EmUtils.imageMagickOp() - output image file path:  %s\n" % outImgPath)
                self._lfh.write("+EmUtils.imageMagickOp() - log file path:         %s\n" % logPath)

            if (self.__cleanUp):
                dp.cleanup()

            return ret
        except:
            traceback.print_exc(file=self._lfh)
            return -100

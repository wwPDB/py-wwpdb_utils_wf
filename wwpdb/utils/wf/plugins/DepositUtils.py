import contextlib
import sys
import traceback

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase

with contextlib.suppress(ImportError):
    # We will have present on annotation system - but allow testing without
    from wwpdb.apps.deposit.depui.depositDataSync import (  # pylint: disable=no-name-in-module
        DepositDataSync,
        SyncDirection,
        print_sync_result,
    )


class DepositUtils(UtilsBase):
    def __init__(self, verbose=False, log=sys.stderr):
        super(DepositUtils, self).__init__(verbose, log)

    def syncToDepositOp(self, **kwargs):
        try:
            (inpObjD, _outObjD, _uD, _pD) = self._getArgs(kwargs)

            dep_id = inpObjD["src"].getDepositionDataSetId()
            config = ConfigInfo()

            if not config.get("SITE_ARCHIVE_UI_STORAGE_PATH"):
                self._lfh.write("+DepositUtils.syncToDepositOp No archive UI storage path configured. Skipping!\n")
                return True

            self._lfh.write("+DepositUtils.syncToDepositOp starting sync to deposit\n")

            syncer = DepositDataSync()
            result = syncer.sync_single(dep_id, SyncDirection.TO_DEPOSIT)
            print_sync_result(result, self._lfh)

            if not result["success"]:
                sys.exit(1)

            return True
        except Exception as _e:  # noqa: F841,BLE001
            if self._verbose:
                traceback.print_exc(file=self._lfh)
            return False

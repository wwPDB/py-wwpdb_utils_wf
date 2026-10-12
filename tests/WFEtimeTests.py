##
# File: WFEtimeTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the WFEtime time helper functions"""

import datetime
import sys
import time
import unittest
from decimal import Decimal
from unittest.mock import patch

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.dbapi import WFEtime

ZERO = datetime.datetime(2000, 1, 1, 0, 0, 0)  # noqa: DTZ001


class WFEtimeTests(unittest.TestCase):
    def testTimeZero(self) -> None:
        self.assertEqual(WFEtime.getTimeZero(), ZERO)

    def testTimeNow(self) -> None:
        fakeNow = datetime.datetime(2000, 1, 2, 0, 0, 1, 500000)  # noqa: DTZ001
        with patch("wwpdb.utils.wf.dbapi.WFEtime.datetime") as mockDt:
            mockDt.datetime.utcnow.return_value = fakeNow
            val = WFEtime.getTimeNow()
        self.assertIsInstance(val, Decimal)
        self.assertEqual(val, Decimal("86401.5"))

    def testTimeNowIsCurrent(self) -> None:
        val = WFEtime.getTimeNow()
        expected = (datetime.datetime.utcnow() - ZERO).total_seconds()  # noqa: DTZ003
        self.assertAlmostEqual(float(val), expected, delta=5.0)

    def testTimeSeconds(self) -> None:
        # Offsets are relative to local-time 2000-01-01 00:00:00
        self.assertEqual(datetime.datetime.fromtimestamp(WFEtime.getTimeSeconds(0)), ZERO)  # noqa: DTZ006
        self.assertAlmostEqual(WFEtime.getTimeSeconds("10.5") - WFEtime.getTimeSeconds(0), 10.5)
        self.assertIsInstance(WFEtime.getTimeSeconds(Decimal("1.25")), float)

    def testTimeString(self) -> None:
        self.assertEqual(WFEtime.getTimeString(0), "2000-01-01 00:00:00 ")
        self.assertEqual(WFEtime.getTimeString(3661), "2000-01-01 01:01:01 ")
        self.assertEqual(WFEtime.getTimeString(Decimal("86400.9")), "2000-01-02 00:00:00 ")

    def testTimeFromEpoc(self) -> None:
        ts = time.mktime(datetime.datetime(2010, 5, 6, 7, 8, 9).timetuple())  # noqa: DTZ001
        self.assertEqual(WFEtime.getTimeFromEpoc(ts), "2010-05-06 07:08:09 ")
        self.assertEqual(WFEtime.getTimeFromEpoc(str(ts + 0.75)), "2010-05-06 07:08:09 ")

    def testTimeReadableRemoved(self) -> None:
        # getTimeReadable() was unused and always raised AttributeError; it is commented out in WFEtime.py
        self.assertFalse(hasattr(WFEtime, "getTimeReadable"))


if __name__ == "__main__":
    unittest.main()

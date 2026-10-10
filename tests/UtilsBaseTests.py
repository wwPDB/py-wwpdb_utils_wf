##
# File: UtilsBaseTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the plugin base class UtilsBase"""

import io
import sys
import unittest
from typing import Any, Dict, Tuple

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.plugins.UtilsBase import UtilsBase


class _ArgsPlugin(UtilsBase):
    """Subclass exposing the protected argument unpacker, as real plugins use it"""

    def unpack(self, **kwArgs: Any) -> Tuple[Any, Any, Any, Any]:
        args: Tuple[Any, Any, Any, Any] = self._getArgs(kwArgs)
        return args


def _kwArgs() -> Dict[str, Any]:
    return {
        "inputObjectD": {"src": "in"},
        "outputObjectD": {"dst": "out"},
        "userParameterD": {"mode": "r"},
        "internalParameterD": {"force": "-f"},
    }


class UtilsBaseTests(unittest.TestCase):
    def testNoOp(self) -> None:
        self.assertTrue(UtilsBase(verbose=False, log=io.StringIO()).noOp(**_kwArgs()))

    def testNoOpRequiresAllArguments(self) -> None:
        kw = _kwArgs()
        del kw["internalParameterD"]
        with self.assertRaises(KeyError):
            UtilsBase(log=io.StringIO()).noOp(**kw)

    def testGetArgsOrder(self) -> None:
        kw = _kwArgs()
        kw["extra"] = "ignored"
        inp, out, usr, internal = _ArgsPlugin(log=io.StringIO()).unpack(**kw)
        self.assertIs(inp, kw["inputObjectD"])
        self.assertIs(out, kw["outputObjectD"])
        self.assertIs(usr, kw["userParameterD"])
        self.assertIs(internal, kw["internalParameterD"])

    def testDumpArgs(self) -> None:
        log = io.StringIO()
        UtilsBase(log=log).dumpArgs({"a": 1, "b": "two"})
        self.assertEqual(
            log.getvalue().splitlines(),
            ["+UtilsBase.dumArgs() key: a  value: 1 ", "+UtilsBase.dumArgs() key: b  value: 'two' "],
        )

    def testDumpArgsEmpty(self) -> None:
        log = io.StringIO()
        UtilsBase(log=log).dumpArgs({})
        self.assertEqual(log.getvalue(), "")


if __name__ == "__main__":
    unittest.main()

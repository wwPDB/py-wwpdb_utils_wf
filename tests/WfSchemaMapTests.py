##
# File: WfSchemaMapTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Consistency tests for the WfSchemaMap schema tables.

WfSchemaMap exposes its data only through single-underscore class-level tables which WfDbApi reads
directly; these tables are the module's interface, so they are read here in the same way.
"""

# ruff: noqa: SLF001
# pylint: disable=protected-access

import sys
import unittest
from typing import Dict, List, Set

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.schema.WfSchemaMap import WfSchemaMap


def _attributes(table: str) -> Dict[str, str]:
    attr = WfSchemaMap._schemaMap[table]["ATTRIBUTES"]
    assert isinstance(attr, dict)  # noqa: S101
    return attr


def _columnsByTableName() -> Dict[str, Set[str]]:
    """Map SQL table name -> set of SQL column names"""
    out: Dict[str, Set[str]] = {}
    for table in WfSchemaMap._schemaMap:
        tableName = WfSchemaMap._schemaMap[table]["TABLE_NAME"]
        assert isinstance(tableName, str)  # noqa: S101
        out.setdefault(tableName, set()).update(_attributes(table).values())
    return out


class WfSchemaMapTests(unittest.TestCase):
    def testInstantiate(self) -> None:
        self.assertIsInstance(WfSchemaMap(), WfSchemaMap)

    def testEveryTableHasNameAndAttributes(self) -> None:
        for table, tD in WfSchemaMap._schemaMap.items():
            with self.subTest(table=table):
                self.assertEqual(sorted(tD.keys()), ["ATTRIBUTES", "TABLE_NAME"])
                self.assertIsInstance(tD["TABLE_NAME"], str)
                attr = _attributes(table)
                self.assertGreater(len(attr), 0)
                for key, col in attr.items():
                    self.assertEqual(key, key.upper())
                    self.assertTrue(col)

    def testTableListMatchesSchema(self) -> None:
        self.assertEqual(sorted(WfSchemaMap._tables), sorted(WfSchemaMap._schemaMap.keys()))
        self.assertEqual(len(WfSchemaMap._tables), len(set(WfSchemaMap._tables)))
        self.assertTrue(set(WfSchemaMap._objectTables).issubset(WfSchemaMap._tables))

    def testTableListPositionsUsedByWfDbApi(self) -> None:
        # WfDbApi indexes _tables by position
        expected = {
            0: "DEPOSITION",
            1: "WF_CLASS_DICT",
            2: "WF_INSTANCE",
            3: "WF_TASK",
            4: "WF_REFERENCE",
            6: "DATABASE_PDB_OBS_SPR",
            7: "DATABASE_REF",
            8: "DATABASE_RELATED",
            9: "AUTHOR_CORRECTIONS",
            10: "RELEASE_REQUEST",
            11: "DEP_WITH_PROBLEMS",
        }
        for idx, name in expected.items():
            self.assertEqual(WfSchemaMap._tables[idx], name)

    def testCoreTableNames(self) -> None:
        names = {t: WfSchemaMap._schemaMap[t]["TABLE_NAME"] for t in WfSchemaMap._objectTables}
        self.assertEqual(
            names,
            {
                "DEPOSITION": "deposition",
                "WF_CLASS_DICT": "wf_class_dict",
                "WF_INSTANCE": "wf_instance",
                "WF_TASK": "wf_task",
                "WF_REFERENCE": "wf_reference",
                "DA_USERS": "da_users",
            },
        )

    @unittest.expectedFailure
    def testContactAuthorTableName(self) -> None:
        # Bug: CONTACT_AUTHOR maps to TABLE_NAME "release_request" instead of "contact_author"
        self.assertEqual(WfSchemaMap._schemaMap["CONTACT_AUTHOR"]["TABLE_NAME"], "contact_author")

    def testStatusColumns(self) -> None:
        self.assertEqual(WfSchemaMap._columnForStatus, ["STATUS_CODE", "INST_STATUS", "TASK_STATUS"])
        # WfDbApi derives its status list from the first three useful items
        self.assertEqual(WfSchemaMap._usefulItems[0:3], WfSchemaMap._columnForStatus)
        self.assertIn("STATUS_CODE", _attributes("DEPOSITION"))
        self.assertIn("INST_STATUS", _attributes("WF_INSTANCE"))
        self.assertIn("TASK_STATUS", _attributes("WF_TASK"))

    def testUsefulItemsAreKnownAttributes(self) -> None:
        allKeys: Set[str] = set()
        for table in WfSchemaMap._schemaMap:
            allKeys.update(_attributes(table).keys())
        # Only the leading entries are guaranteed to be schema attributes; later ones are legacy names
        for item in WfSchemaMap._usefulItems[0:5]:
            with self.subTest(item=item):
                self.assertIn(item, allKeys)

    def testObjectIds(self) -> None:
        self.assertEqual(WfSchemaMap._objIds, ["DEP_SET_ID", "WF_CLASS_ID", "WF_INST_ID", "WF_TASK_ID"])
        # Each object table carries the identifiers of itself and its parents
        for depth, table in enumerate(["DEPOSITION", "WF_CLASS_DICT", "WF_INSTANCE", "WF_TASK"]):
            attr = _attributes(table)
            self.assertIn(WfSchemaMap._objIds[depth], attr)
        for oid in WfSchemaMap._objIds:
            self.assertIn(oid, _attributes("WF_REFERENCE"))

    def testReferencePairsAndUserInfo(self) -> None:
        self.assertEqual(WfSchemaMap._referencePairs, ["HASH_ID", "VALUE"])
        for key in WfSchemaMap._referencePairs:
            self.assertIn(key, _attributes("WF_REFERENCE"))
        self.assertEqual(sorted(WfSchemaMap._userInfo), sorted(_attributes("DA_USERS").keys()))

    def testConstraintListColumnsExist(self) -> None:
        cols = _columnsByTableName()
        for key, qualified in WfSchemaMap._constraintList.items():
            with self.subTest(key=key):
                tableName, column = qualified.split(".")
                self.assertIn(tableName, cols)
                self.assertIn(column, cols[tableName])

    def testCrossTableSelectColumnsExist(self) -> None:
        cols = _columnsByTableName()
        sel = WfSchemaMap._selectColumns[2]
        assert isinstance(sel, list)  # noqa: S101
        for qualified in sel:
            with self.subTest(column=qualified):
                tableName, column = qualified.split(".")
                self.assertIn(column, cols[tableName])

    def testDepositionSelectColumns(self) -> None:
        sel = WfSchemaMap._selectColumns[1]
        assert isinstance(sel, list)  # noqa: S101
        self.assertEqual(sel[0], "DEP_SET_ID")
        depAttr = _attributes("DEPOSITION")
        for key in sel:
            self.assertIn(key, depAttr)

    def testJoinAndOrder(self) -> None:
        join = WfSchemaMap._tableJoinSyntext
        self.assertTrue(join.startswith(" FROM wf_instance"))
        for tableName in ("wf_class_dict", "deposition", "wf_task"):
            self.assertIn("left join %s" % tableName, join)
        self.assertEqual(sorted(WfSchemaMap._orderBy.keys()), [1, 2, 3])
        self.assertEqual(WfSchemaMap._orderBy[1], "order by dep_set_id")
        order3 = WfSchemaMap._orderBy[3]
        assert isinstance(order3, list)  # noqa: S101
        depCols: List[str] = list(_attributes("DEPOSITION").values())
        for col in order3:
            self.assertIn(col, depCols)


if __name__ == "__main__":
    unittest.main()

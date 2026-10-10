##
# File: DataContainerTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for DataSelector, DataValueContainer and WfDataObject"""

import io
import sys
import unittest
from datetime import date, datetime

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.wf.DataSelector import DataSelector
from wwpdb.utils.wf.DataValueContainer import DataValueContainer
from wwpdb.utils.wf.WfDataObject import WfDataObject


class DataSelectorTests(unittest.TestCase):
    def testDefaults(self) -> None:
        ds = DataSelector()
        self.assertIsNone(ds.getSelectorType())
        self.assertIsNone(ds.getSelectCategoryName())
        self.assertEqual(ds.getSelectAttributeList(), [])
        self.assertEqual(ds.getSelectConditionList(), [])

    def testCategoryName(self) -> None:
        ds = DataSelector()
        self.assertTrue(ds.setSelectCategoryName("entity_poly"))
        self.assertEqual(ds.getSelectCategoryName(), "entity_poly")

    def testAttributesAreUnique(self) -> None:
        ds = DataSelector()
        self.assertTrue(ds.addSelectAttributeName("entity_id"))
        self.assertTrue(ds.addSelectAttributeName("type"))
        self.assertTrue(ds.addSelectAttributeName("entity_id"))
        self.assertEqual(ds.getSelectAttributeList(), ["entity_id", "type"])
        self.assertEqual(ds.getSelectorType(), "attribute")

    def testConditions(self) -> None:
        ds = DataSelector()
        self.assertTrue(ds.addSelectCondition("entity_id", "1"))
        self.assertTrue(ds.addSelectCondition("type", "polymer", "not equal"))
        self.assertEqual(ds.getSelectConditionList(), [("entity_id", "1", "equal"), ("type", "polymer", "not equal")])
        # Conditions alone do not set the selector type
        self.assertIsNone(ds.getSelectorType())

    def testInstancesDoNotShareState(self) -> None:
        ds1 = DataSelector()
        ds2 = DataSelector()
        ds1.addSelectAttributeName("a")
        ds1.addSelectCondition("a", "1")
        self.assertEqual(ds2.getSelectAttributeList(), [])
        self.assertEqual(ds2.getSelectConditionList(), [])


class DataValueContainerTests(unittest.TestCase):
    def testDefaults(self) -> None:
        dv = DataValueContainer()
        self.assertIsNone(dv.getValue())
        self.assertFalse(dv.isValueSet())
        self.assertIsNone(dv.getContainerTypeName())
        self.assertIsNone(dv.getValueTypeName())

    def testSetValue(self) -> None:
        dv = DataValueContainer()
        dv.setValue(5)
        self.assertTrue(dv.isValueSet())
        self.assertEqual(dv.getValue(), 5)

    def testContainerTypeNames(self) -> None:
        dv = DataValueContainer()
        for name in ("value", "list", "dict"):
            self.assertTrue(dv.setContainerTypeName(name))
            self.assertEqual(dv.getContainerTypeName(), name)
        self.assertFalse(dv.setContainerTypeName("tuple"))
        # Rejected names leave the previous setting in place
        self.assertEqual(dv.getContainerTypeName(), "dict")

    def testValueTypeNames(self) -> None:
        dv = DataValueContainer()
        for name in ("boolean", "int", "integer", "float", "double", "string", "date", "datetime"):
            self.assertTrue(dv.setValueTypeName(name), name)
            self.assertEqual(dv.getValueTypeName(), name)
        self.assertFalse(dv.setValueTypeName("bool"))
        self.assertFalse(dv.setValueTypeName("complex"))
        self.assertEqual(dv.getValueTypeName(), "datetime")

    def _container(self, containerName: str, typeName: str, value: object) -> DataValueContainer:
        dv = DataValueContainer()
        self.assertTrue(dv.setContainerTypeName(containerName))
        self.assertTrue(dv.setValueTypeName(typeName))
        dv.setValue(value)
        return dv

    def testValidSingleValues(self) -> None:
        cases = [
            ("boolean", True),
            ("integer", 3),
            ("int", 3),
            ("string", "abc"),
            ("date", date(2020, 2, 3)),
            ("datetime", datetime(2020, 2, 3, 4, 5, 6)),  # noqa: DTZ001
        ]
        for typeName, value in cases:
            with self.subTest(typeName=typeName):
                self.assertTrue(self._container("value", typeName, value).isValueValid())

    def testInvalidSingleValues(self) -> None:
        self.assertFalse(self._container("value", "integer", "3").isValueValid())
        self.assertFalse(self._container("value", "string", 3).isValueValid())
        self.assertFalse(self._container("value", "date", "2020-01-01").isValueValid())

    @unittest.expectedFailure
    def testFloatValueIsValid(self) -> None:
        # Library maps "float"/"double" to int, so float values are rejected
        self.assertTrue(self._container("value", "float", 1.5).isValueValid())

    def testListValues(self) -> None:
        self.assertTrue(self._container("list", "string", ["a", "b"]).isValueValid())
        self.assertTrue(self._container("list", "string", []).isValueValid())
        self.assertFalse(self._container("list", "string", ["a", 1]).isValueValid())
        self.assertFalse(self._container("list", "string", "a").isValueValid())

    def testDictValues(self) -> None:
        self.assertTrue(self._container("dict", "string", {"a": 1}).isValueValid())
        self.assertFalse(self._container("dict", "string", ["a"]).isValueValid())

    def testUnsetValueIsInvalid(self) -> None:
        dv = DataValueContainer()
        dv.setContainerTypeName("value")
        dv.setValueTypeName("integer")
        self.assertFalse(dv.isValueValid())


class WfDataObjectTests(unittest.TestCase):
    def _render(self, wfo: WfDataObject) -> str:
        out = io.StringIO()
        wfo.printMe(out)
        return out.getvalue()

    def testUndefined(self) -> None:
        wfo = WfDataObject()
        self.assertIn("undefined data object", self._render(wfo))
        self.assertIn("undefined data object", str(wfo))
        self.assertIn("undefined data object", repr(wfo))

    def testValueContainer(self) -> None:
        wfo = WfDataObject()
        wfo.setContainerTypeName("list")
        wfo.setValueTypeName("integer")
        wfo.setValue([1, 2])
        text = self._render(wfo)
        self.assertIn("container type list", text)
        self.assertIn("value type     integer", text)
        self.assertIn("is value valid True", text)
        self.assertIn("[1, 2]", text)
        self.assertEqual(str(wfo), text)

    def testFileReference(self) -> None:
        wfo = WfDataObject()
        wfo.setDepositionDataSetId("D_000001")
        wfo.setStorageType("archive")
        wfo.setContentTypeAndFormat("model", "pdbx")
        wfo.setVersionId("latest")
        self.assertEqual(wfo.getReferenceType(), "file")
        text = self._render(wfo)
        self.assertIn("data set ID       D_000001", text)
        self.assertIn("content type      model", text)
        self.assertNotIn("selector type", text)

    def testFileReferenceWithSelector(self) -> None:
        wfo = WfDataObject()
        wfo.setDepositionDataSetId("D_000001")
        wfo.setStorageType("archive")
        wfo.setContentTypeAndFormat("model", "pdbx")
        wfo.setSelectCategoryName("entity")
        wfo.addSelectAttributeName("id")
        wfo.addSelectCondition("id", "1")
        text = self._render(wfo)
        self.assertIn("selector type     attribute", text)
        self.assertIn("select category   entity", text)
        self.assertIn("('id', '1', 'equal')", text)

    def testMixinsAreIndependent(self) -> None:
        wfo = WfDataObject()
        wfo.setValue("x")
        wfo.addSelectAttributeName("a")
        self.assertEqual(wfo.getValue(), "x")
        self.assertEqual(wfo.getSelectAttributeList(), ["a"])


if __name__ == "__main__":
    unittest.main()

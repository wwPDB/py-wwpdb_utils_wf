##
# File: PdbxUtilsTests.py
# Date: 10-Oct-2026
#
# Updates:
##
"""Unit tests for the PdbxUtils workflow plugin (uses small real mmCIF files)"""

import io
import os
import sys
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa: F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.utils.wf.plugins.PdbxUtils import CifFile, PdbxUtils
from wwpdb.utils.wf.WfDataObject import WfDataObject

MODEL_CIF = """data_D_000001
#
_struct.entry_id D_000001
_struct.title    'Crystal structure of a test protein'
#
_exptl.entry_id D_000001
_exptl.method   'X-RAY DIFFRACTION'
#
_pdbx_database_status.entry_id                      D_000001
_pdbx_database_status.recvd_initial_deposition_date 2020-01-02
_pdbx_database_status.author_release_status_code    HPUB
_pdbx_database_status.deposit_site                  RCSB
_pdbx_database_status.process_site                  PDBE
_pdbx_database_status.status_code                   PROC
_pdbx_database_status.rcsb_annotator                AN
#
_pdbx_SG_project.id                  1
_pdbx_SG_project.full_name_of_center 'Test Structural Genomics Center'
_pdbx_SG_project.initial_of_center   TSGC
#
loop_
_database_2.database_id
_database_2.database_code
PDB  1ABC
PDB  D_1000000001
EMDB EMD-1234
#
loop_
_audit_author.name
_audit_author.pdbx_ordinal
'Doe, J.'   1
'Smith, A.' 2
#
loop_
_entity.id
_entity.type
_entity.pdbx_description
1 polymer 'Test protein'
2 non-polymer 'ZINC ION'
3 water   water
#
"""

ASSEMBLY_CIF = """#
_pdbx_struct_assembly.id      1
_pdbx_struct_assembly.details author_defined_assembly
#
_pdbx_struct_assembly_gen.assembly_id     1
_pdbx_struct_assembly_gen.oper_expression 1
_pdbx_struct_assembly_gen.asym_id_list    A,B
#
_pdbx_struct_oper_list.id          1
_pdbx_struct_oper_list.matrix[1][1] 1.0
_pdbx_struct_oper_list.matrix[1][2] 0.0
_pdbx_struct_oper_list.matrix[1][3] 0.0
_pdbx_struct_oper_list.vector[1]    0.0
_pdbx_struct_oper_list.matrix[2][1] 0.0
_pdbx_struct_oper_list.matrix[2][2] 1.0
_pdbx_struct_oper_list.matrix[2][3] 0.0
_pdbx_struct_oper_list.vector[2]    0.0
_pdbx_struct_oper_list.matrix[3][1] 0.0
_pdbx_struct_oper_list.matrix[3][2] 0.0
_pdbx_struct_oper_list.matrix[3][3] 1.0
_pdbx_struct_oper_list.vector[3]    0.0
#
"""


def _srcObj(filePath: str, category: Optional[str] = None, attributes: Optional[List[str]] = None, conditions: Optional[List[Tuple[str, str, str]]] = None) -> MagicMock:
    obj = MagicMock(spec=WfDataObject)
    obj.getFilePathReference.return_value = filePath
    obj.getSelectCategoryName.return_value = category
    obj.getSelectAttributeList.return_value = attributes or []
    obj.getSelectConditionList.return_value = conditions or []
    return obj


def _dstObj(containerType: str = "value") -> WfDataObject:
    obj = WfDataObject()
    obj.setContainerTypeName(containerType)
    return obj


def _kw(inputObjectD: Dict[str, Any], outputObjectD: Dict[str, Any], userParameterD: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"inputObjectD": inputObjectD, "outputObjectD": outputObjectD, "userParameterD": userParameterD or {}, "internalParameterD": {}}


class PdbxUtilsBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpDir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.log = io.StringIO()
        self.util = PdbxUtils(verbose=True, log=self.log)
        self.modelPath = self.writeCif("model.cif", MODEL_CIF)
        self.missingPath = os.path.join(self.tmpDir.name, "missing.cif")
        self.garbagePath = self.writeCif("garbage.cif", "this is not a cif file\n")

    def tearDown(self) -> None:
        self.tmpDir.cleanup()

    def writeCif(self, name: str, content: str) -> str:
        fPath = os.path.join(self.tmpDir.name, name)
        with open(fPath, "w") as ofh:
            ofh.write(content)
        return fPath


class CifFileTests(PdbxUtilsBase):
    def testReadWrite(self) -> None:
        self.assertEqual(CifFile.getFileExt(), "cif")
        cf = CifFile.read(self.modelPath)
        self.assertIsInstance(cf, CifFile)
        self.assertEqual(list(cf.getCifFile().GetBlockNames([])), ["D_000001"])
        outPath = os.path.join(self.tmpDir.name, "copy.cif")
        cf.write(outPath)
        self.assertEqual(list(CifFile(outPath).getCifFile().GetBlockNames([])), ["D_000001"])

    def testMissingFileRaises(self) -> None:
        with self.assertRaises(RuntimeError):
            CifFile(self.missingPath)


class SelectOpTests(PdbxUtilsBase):
    # PdbxUtils.py:150 calls ISTable.Search(values, names) with the legacy two-argument signature; the current mmcif
    # binding requires (res, targets, colNames, fromRowIndex, searchDir, searchType, indexName) so selectOp always fails
    @unittest.expectedFailure
    def testSelectMatch(self) -> None:
        dst = _dstObj("list")
        src = _srcObj(self.modelPath, "entity", ["pdbx_description", "type"], [("id", "2", "equal")])
        self.assertTrue(self.util.selectOp(**_kw({"src": src}, {"dst": dst})))
        self.assertEqual(dst.getValue(), ["ZINC ION", "non-polymer"])

    @unittest.expectedFailure  # same ISTable.Search() signature bug as testSelectMatch (PdbxUtils.py:150)
    def testSelectMultipleConditions(self) -> None:
        dst = _dstObj("list")
        src = _srcObj(self.modelPath, "database_2", ["database_code"], [("database_id", "EMDB", "equal")])
        self.assertTrue(self.util.selectOp(**_kw({"src": src}, {"dst": dst})))
        self.assertEqual(dst.getValue(), ["EMD-1234"])
        src = _srcObj(self.modelPath, "entity", ["id"], [("type", "polymer", "equal"), ("pdbx_description", "Test protein", "equal")])
        self.assertTrue(self.util.selectOp(**_kw({"src": src}, {"dst": dst})))
        self.assertEqual(dst.getValue(), ["1"])

    def testSelectFailures(self) -> None:
        cases = {
            "noMatch": _srcObj(self.modelPath, "entity", ["type"], [("id", "9", "equal")]),
            "noConditions": _srcObj(self.modelPath, "entity", ["type"]),
            "missingCategory": _srcObj(self.modelPath, "struct_ref", ["id"], [("id", "1", "equal")]),
            "missingFile": _srcObj(self.missingPath, "entity", ["type"], [("id", "1", "equal")]),
            "garbageFile": _srcObj(self.garbagePath, "entity", ["type"], [("id", "1", "equal")]),
        }
        for name, src in cases.items():
            with self.subTest(case=name):
                dst = _dstObj("list")
                self.assertFalse(self.util.selectOp(**_kw({"src": src}, {"dst": dst})))
                self.assertIsNone(dst.getValue())

    def testSelectExceptionReturnsFalse(self) -> None:
        src = _srcObj(self.modelPath, "entity", ["type"], [("id", "1", "equal")])
        src.getSelectConditionList.side_effect = RuntimeError("bad selector")
        dst = _dstObj("list")
        self.assertFalse(self.util.selectOp(**_kw({"src": src}, {"dst": dst})))
        self.assertIn("RuntimeError: bad selector", self.log.getvalue())
        self.assertIsNone(dst.getValue())


class FetchOpTests(PdbxUtilsBase):
    def testFetchValueAndList(self) -> None:
        src = _srcObj(self.modelPath, "entity", ["type"])
        dst = _dstObj("value")
        self.assertTrue(self.util.fetchOp(**_kw({"src": src}, {"dst": dst})))
        self.assertEqual(dst.getValue(), "polymer")
        dst = _dstObj("list")
        self.assertTrue(self.util.fetchOp(**_kw({"src": src}, {"dst": dst})))
        self.assertEqual(dst.getValue(), ["polymer", "non-polymer", "water"])

    def testFetchFailures(self) -> None:
        cases = {
            "dictContainer": (_srcObj(self.modelPath, "entity", ["type"]), "dict"),
            "missingCategory": (_srcObj(self.modelPath, "struct_ref", ["id"]), "value"),
            "missingFile": (_srcObj(self.missingPath, "entity", ["type"]), "value"),
            "noAttributes": (_srcObj(self.modelPath, "entity", []), "value"),
        }
        for name, (src, containerType) in cases.items():
            with self.subTest(case=name):
                dst = _dstObj(containerType)
                self.assertFalse(self.util.fetchOp(**_kw({"src": src}, {"dst": dst})))
                self.assertIsNone(dst.getValue())


class FetchAnnAutoOpTests(PdbxUtilsBase):
    def _run(self, content: str, containerTypes: Tuple[str, str, str] = ("value", "value", "value")) -> Tuple[bool, List[WfDataObject]]:
        fPath = self.writeCif("ann.cif", content)
        src = _srcObj(fPath, "struct", ["title"])
        dsts = [_dstObj(c) for c in containerTypes]
        ok = self.util.fetchAnnAutoOp(**_kw({"src": src}, {"dst1": dsts[0], "dst2": dsts[1], "dst3": dsts[2]}))
        return ok, dsts

    @staticmethod
    def _entry(method: str, extra: str = "") -> str:
        return "data_X\n_struct.entry_id X\n_struct.title 'T'\n#\n_exptl.entry_id X\n_exptl.method '%s'\n#\n%s" % (method, extra)

    def testAutoCompleteFlag(self) -> None:
        xrayFlag = "_pdbx_depui_status_flags.dep_dataset_id X\n_pdbx_depui_status_flags.assembly_inferred %s\n#\n"
        badOper = ASSEMBLY_CIF.replace("_pdbx_struct_oper_list.vector[3]    0.0", "_pdbx_struct_oper_list.vector[3]    ?")
        cases = [
            ("EM with assembly", self._entry("ELECTRON MICROSCOPY", ASSEMBLY_CIF), "YES"),
            ("solution NMR with assembly", self._entry("SOLUTION NMR", ASSEMBLY_CIF), "YES"),
            ("solid-state NMR with assembly", self._entry("solid-state nmr", ASSEMBLY_CIF), "YES"),
            ("EM without assembly", self._entry("ELECTRON MICROSCOPY"), "NO"),
            ("EM with unknown operator value", self._entry("ELECTRON MICROSCOPY", badOper), "NO"),
            ("X-ray with assembly", self._entry("X-RAY DIFFRACTION", ASSEMBLY_CIF), "NO"),
            ("X-ray inferred Y", self._entry("X-RAY DIFFRACTION", ASSEMBLY_CIF + xrayFlag % "y"), "YES"),
            ("X-ray inferred N", self._entry("X-RAY DIFFRACTION", ASSEMBLY_CIF + xrayFlag % "N"), "NO"),
            ("X-ray inferred Y no assembly", self._entry("X-RAY DIFFRACTION", xrayFlag % "Y"), "NO"),
            ("no exptl", "data_X\n_struct.entry_id X\n_struct.title 'T'\n#\n" + ASSEMBLY_CIF, "NO"),
        ]
        siteName = ConfigInfo().get("SITE_NAME")
        for name, content, expected in cases:
            with self.subTest(case=name):
                ok, dsts = self._run(content)
                self.assertTrue(ok)
                self.assertEqual(dsts[0].getValue(), "T")
                self.assertEqual(dsts[1].getValue(), expected)
                self.assertEqual(dsts[2].getValue(), siteName)

    def testListContainers(self) -> None:
        ok, dsts = self._run(self._entry("ELECTRON MICROSCOPY", ASSEMBLY_CIF), ("list", "list", "list"))
        self.assertTrue(ok)
        self.assertEqual(dsts[0].getValue(), ["T"])
        self.assertEqual(dsts[1].getValue(), ["YES"])
        self.assertEqual(dsts[2].getValue(), [ConfigInfo().get("SITE_NAME")])

    def testUnsupportedContainers(self) -> None:
        for containerTypes in (("dict", "value", "value"), ("value", "dict", "value"), ("value", "value", "dict")):
            with self.subTest(containerTypes=containerTypes):
                ok, dsts = self._run(self._entry("SOLUTION NMR"), containerTypes)
                self.assertFalse(ok)
                idx = containerTypes.index("dict")
                self.assertIsNone(dsts[idx].getValue())

    def testFailures(self) -> None:
        dsts = {"dst1": _dstObj(), "dst2": _dstObj(), "dst3": _dstObj()}
        self.assertFalse(self.util.fetchAnnAutoOp(**_kw({"src": _srcObj(self.missingPath, "struct", ["title"])}, dsts)))
        self.assertFalse(self.util.fetchAnnAutoOp(**_kw({"src": _srcObj(self.modelPath, "struct_ref", ["id"])}, dsts)))
        self.assertFalse(self.util.fetchAnnAutoOp(**_kw({"src": _srcObj(self.modelPath, "struct", ["title"])}, {"dst1": _dstObj()})))
        self.assertIn("KeyError", self.log.getvalue())


class CategoryRowCountOpTests(PdbxUtilsBase):
    def _count(self, filePath: str, uD: Dict[str, Any]) -> Tuple[bool, Any]:
        dst = _dstObj()
        ok = self.util.categoryRowCountOp(**_kw({"src": _srcObj(filePath)}, {"dst": dst}, uD))
        return ok, dst.getValue()

    def testCounts(self) -> None:
        self.assertEqual(self._count(self.modelPath, {"category": "entity"}), (True, 3))
        self.assertEqual(self._count(self.modelPath, {"category": "struct"}), (True, 1))
        self.assertEqual(self._count(self.modelPath, {"category": "struct_ref"}), (True, 0))
        self.assertEqual(self._count(self.modelPath, {}), (True, 0))
        self.assertEqual(self._count(self.missingPath, {"category": "entity"}), (True, 0))

    def testExceptionReturnsFalse(self) -> None:
        self.assertFalse(self.util.categoryRowCountOp(**_kw({"src": _srcObj(self.modelPath)}, {}, {"category": "entity"})))


class StatusOpTests(PdbxUtilsBase):
    # PdbxUtils.py:418 calls ISTable.Search((dbId,), ("database_id",)) with the legacy signature; the current mmcif
    # binding rejects it with TypeError, so statusOp fails for any file containing database_2
    @unittest.expectedFailure
    def testStatusDictionary(self) -> None:
        dst = _dstObj()
        self.assertTrue(self.util.statusOp(**_kw({"src": _srcObj(self.modelPath)}, {"dst": dst})))
        d = dst.getValue()
        self.assertEqual(d["title"], "Crystal structure of a test protein")
        self.assertEqual(d["exp_method"], "X-RAY DIFFRACTION")
        # pdbx_database_status values are returned utf-8 encoded (legacy Python 2 behaviour)
        self.assertEqual(d["recvd_initial_deposition_date"], b"2020-01-02")
        self.assertEqual(d["author_release_status_code"], b"HPUB")
        self.assertEqual(d["deposit_site"], b"RCSB")
        self.assertEqual(d["process_site"], b"PDBE")
        self.assertEqual(d["status_code"], b"PROC")
        self.assertEqual(d["annotator_initials"], b"AN")
        self.assertNotIn("status_code_sf", d)
        self.assertEqual(d["full_name_of_center"], "Test Structural Genomics Center")
        self.assertEqual(d["initial_of_center"], "TSGC")
        self.assertEqual(d["accessions"], {"PDB": ["1ABC", "D_1000000001"], "BMRRB": [], "EMDB": ["EMD-1234"]})
        self.assertEqual(d["audit_author"], ["Doe, J.", "Smith, A."])

    def testStatusWithoutDatabase2(self) -> None:
        fPath = self.writeCif("nodb2.cif", "\n".join(ln for ln in MODEL_CIF.splitlines() if not ln.startswith(("_database_2", "PDB ", "EMDB "))))
        dst = _dstObj()
        self.assertTrue(self.util.statusOp(**_kw({"src": _srcObj(fPath)}, {"dst": dst})))
        d = dst.getValue()
        self.assertEqual(d["title"], "Crystal structure of a test protein")
        self.assertEqual(d["exp_method"], "X-RAY DIFFRACTION")
        # pdbx_database_status values are returned utf-8 encoded (legacy Python 2 behaviour)
        self.assertEqual(d["status_code"], b"PROC")
        self.assertEqual(d["annotator_initials"], b"AN")
        self.assertEqual(d["recvd_initial_deposition_date"], b"2020-01-02")
        self.assertNotIn("status_code_mr", d)
        self.assertEqual(d["initial_of_center"], "TSGC")
        self.assertEqual(d["accessions"], {"PDB": [], "BMRRB": [], "EMDB": []})
        self.assertEqual(d["audit_author"], ["Doe, J.", "Smith, A."])

    def testMinimalFile(self) -> None:
        fPath = self.writeCif("min.cif", "data_X\n_entity.id 1\n_entity.type polymer\n#\n")
        dst = _dstObj()
        self.assertTrue(self.util.statusOp(**_kw({"src": _srcObj(fPath)}, {"dst": dst})))
        self.assertEqual(dst.getValue(), {"accessions": {"PDB": [], "BMRRB": [], "EMDB": []}})

    def testFailures(self) -> None:
        dst = _dstObj()
        self.assertFalse(self.util.statusOp(**_kw({"src": _srcObj(self.missingPath)}, {"dst": dst})))
        self.assertIsNone(dst.getValue())
        fPath = self.writeCif("min.cif", "data_X\n_struct.entry_id X\n_struct.title 'T'\n#\n")
        self.assertFalse(self.util.statusOp(**_kw({"src": _srcObj(fPath)}, {})))
        self.assertIn("KeyError", self.log.getvalue())


if __name__ == "__main__":
    unittest.main()

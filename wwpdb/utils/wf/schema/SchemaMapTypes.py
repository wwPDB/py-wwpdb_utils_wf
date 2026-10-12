"""
File:    SchemaMapTypes.py
Type definitions for the table definitions held in `WfSchemaMap._schemaMap`.

"""

from typing import Dict, Union

from typing_extensions import TypedDict


class SchemaTableDef(TypedDict):
    """Definition of one table in `WfSchemaMap._schemaMap`."""

    TABLE_NAME: str
    """Name of the table in the database"""
    ATTRIBUTES: Dict[str, str]
    """Logical attribute name -> database column name"""


class EmptySchemaTableDef(TypedDict):
    """Returned as `{}` by `WfDbApi` when no table matches the given ids.  Callers test `len(tableDef) > 0`."""


MaybeSchemaTableDef = Union[SchemaTableDef, EmptySchemaTableDef]

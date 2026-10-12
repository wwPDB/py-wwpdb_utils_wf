"""
File:    ActionRegistryTypes.py
Type definitions for the action registry built by `ActionRegistryIo` and read by `ActionRegistry`.

"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class ActionDataObjectDef(TypedDict):
    """Required features of one input or output data object (`<wfDataObject>`).  None means no requirement."""

    dataReferenceType: Optional[str]
    contentType: Optional[str]
    fileFormat: Optional[str]
    containerType: Optional[str]
    valueType: Optional[str]
    selectorType: Optional[str]


# User and internal parameters.  Values read from the registry file are strings (or None when empty), but
# ActionRegistry.setUserParameter() and ProcessRunner.setParameterDict() accept values of any type.
ActionParameterDict = Dict[str, Any]


class ActionDef(TypedDict):
    """Definition of one action (`<action>`) in the registry."""

    MODULE_NAME: Optional[str]
    """Python module (and class) name holding the method"""
    METHOD_NAME: Optional[str]
    """Python method name"""
    INPUT_INFO_LIST: Dict[str, ActionDataObjectDef]
    """Input object name -> required features"""
    OUTPUT_INFO_LIST: Dict[str, ActionDataObjectDef]
    """Output object name -> required features"""
    INPUT_NAME_LIST: List[str]
    """Input object names in registry order"""
    OUTPUT_NAME_LIST: List[str]
    """Output object names in registry order"""
    USER_PARAMETER_DICT: ActionParameterDict
    INTERNAL_PARAMETER_DICT: ActionParameterDict


# Action identifier -> action definition
ActionRegistryDict = Dict[str, ActionDef]

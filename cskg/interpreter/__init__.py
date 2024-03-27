from enum import StrEnum
from astroid import NodeNG, InferenceError, Module, ClassDef, FunctionDef, Const
from astroid.typing import SuccessfulInferenceResult
from astroid.util import Uninferable
from astroid.bases import Proxy
from loguru import logger

from cskg.entity import (
    ExternalModuleEntity,
    ExternalClassEntity,
    ExternalFunctionEntity,
    ExternalVariableEntity,
)


def get_module_prefix(folder_path: str):
    return ".".join(folder_path.split("/")[0:-1])


def remove_module_prefix(qualified_name: str, folder_path: str):
    module_prefix = get_module_prefix(folder_path)
    if qualified_name.startswith(module_prefix):
        return qualified_name.replace(module_prefix + ".", "")
    return qualified_name


def get_inferred_types(
    node: NodeNG, inferred_type_method=None
) -> list[SuccessfulInferenceResult]:
    try:
        if inferred_type_method:
            inferred_types = inferred_type_method()
        else:
            inferred_types = node.inferred()
    except InferenceError or StopIteration:
        return []

    inferred_types = filter(lambda node: node is not Uninferable, inferred_types)
    inferred_types = list(inferred_types)

    return inferred_types


def get_inferred_type(node: NodeNG, inferred_type_method=None) -> NodeNG | None:
    inferred_types = get_inferred_types(node, inferred_type_method)
    inferred_type = inferred_types[0] if len(inferred_types) > 0 else None

    if isinstance(inferred_type, NodeNG):
        return inferred_type

    elif isinstance(inferred_type, Proxy):
        return inferred_type._proxied

    return None


class FunctionType(StrEnum):
    FUNCTION = "function"
    METHOD = "method"
    CLASSMETHOD = "classmethod"
    STATICMETHOD = "staticmethod"


def visit_external_entity(node: Module | ClassDef | FunctionDef | Const):
    if node is None:
        return

    root = node.root()
    if isinstance(root, Module) and root.file is not None:
        return

    if isinstance(node, Module):
        yield ExternalModuleEntity(
            name=node.name,
            qualified_name=node.qname(),
            file_path=None,
        )
    elif isinstance(node, ClassDef):
        yield ExternalClassEntity(
            name=node.name,
            qualified_name=node.qname(),
            file_path=None,
        )
    elif isinstance(node, FunctionDef):
        yield ExternalFunctionEntity(
            name=node.name,
            qualified_name=node.qname(),
            file_path=None,
            subtype=FunctionType(node.type),
        )
    elif isinstance(node, Const):
        yield ExternalVariableEntity(
            name=node.name,
            qualified_name=node.pytype(),
            file_path=None,
        )

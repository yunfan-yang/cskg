from enum import StrEnum
from typing import Callable, overload
from astroid import NodeNG, InferenceError, Module, ClassDef, FunctionDef
from astroid.typing import SuccessfulInferenceResult, InferenceResult
from astroid.util import Uninferable
from astroid.bases import Proxy
from loguru import logger

from cskg.utils.entity import (
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


@overload
def get_inferred_types(node: NodeNG) -> list[SuccessfulInferenceResult]: ...


@overload
def get_inferred_types(
    lambda_x: Callable[[], list[InferenceResult]]
) -> list[SuccessfulInferenceResult]: ...


def get_inferred_types(
    node_or_lambda: NodeNG | Callable[[], list[InferenceResult]],
) -> list[SuccessfulInferenceResult]:
    try:
        if isinstance(node_or_lambda, NodeNG):
            inferred_types = node_or_lambda.inferred()
        else:
            inferred_types = node_or_lambda()

        inferred_types = filter(lambda node: node is not Uninferable, inferred_types)
        inferred_types = list(inferred_types)
        return inferred_types
    except InferenceError or StopIteration:
        return []
    except Exception:
        logger.error(f"Failed to get inferred types for {node_or_lambda}")
        return []


@overload
def get_inferred_type(node: NodeNG) -> NodeNG | None: ...


@overload
def get_inferred_type(
    node: NodeNG,
    inferred_type_method: Callable[[], list[InferenceResult]],
) -> NodeNG | None: ...


def get_inferred_type(
    node_or_lambda: NodeNG | Callable[[], list[InferenceResult]],
) -> NodeNG | None:
    inferred_types = get_inferred_types(node_or_lambda)
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
    LAMBDA = "lambda"


def visit_external_entity(node: NodeNG):
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
    # elif isinstance(node, Const):
    #     yield ExternalVariableEntity(
    #         name=node.name,
    #         qualified_name=node.pytype(),
    #         file_path=None,
    #     )

from typing import Iterator, overload
from astroid import NodeNG, InferenceError
from astroid.typing import SuccessfulInferenceResult
from astroid.util import Uninferable
from astroid.bases import Proxy


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

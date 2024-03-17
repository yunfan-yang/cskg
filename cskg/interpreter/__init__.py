from astroid import NodeNG, InferenceError
from astroid.typing import SuccessfulInferenceResult
from astroid.util import Uninferable
from astroid.bases import Proxy
from loguru import logger


def get_module_prefix(folder_path):
    return ".".join(folder_path.split("/")[0:-1])


def remove_module_prefix(qualified_name, folder_path):
    module_prefix = get_module_prefix(folder_path)
    if qualified_name.startswith(module_prefix):
        return qualified_name.replace(module_prefix + ".", "")
    return qualified_name


def get_inferred_type(node: NodeNG) -> NodeNG | None:
    try:
        inferred_types = node.inferred()
    except InferenceError:
        return None

    inferred_types = filter(lambda node: node is not Uninferable, inferred_types)
    inferred_type = next(inferred_types, None)

    if isinstance(inferred_type, NodeNG):
        return inferred_type

    elif isinstance(inferred_type, Proxy):
        return inferred_type._proxied

    return None

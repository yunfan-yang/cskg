from astroid import (
    InferenceError,
    FunctionDef,
    Call,
    Uninferable,
)
from loguru import logger

from interpreter import remove_module_prefix, get_module_prefix


def visit_function(node: FunctionDef, current_file_path: str = None):
    name = node.name
    qualified_name = remove_module_prefix(node.qname(), current_file_path)
    args = node.args

    function_ent = {
        "type": "function",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield function_ent
    yield from visit_function_called_nodes(node, current_file_path)


def visit_function_called_nodes(node: FunctionDef, current_file_path: str = None):
    """
    Visit body and write down node function calls other functions.
    """

    calls = list(node.nodes_of_class(Call))
    funcs = [call.func for call in calls]

    logger.debug(f"function calls: {calls}")
    logger.debug(f"function nodes: {funcs}")

    for func in funcs:
        try:
            """
            Multiple Possible Inferences:
            In Python, a name (like that of a function) can refer to multiple different objects over the course
            of a program's execution. Astroid's inference engine takes this into account and attempts to infer
            all possible objects a name could refer to at a given point in the code.
            For example, if a function name is reassigned multiple times to different callable objects,
            inferred() will return all of these possibilities.
            """
            inference_results = func.inferred()
        except InferenceError:
            logger.error(f"Could not infer function call (hard): {func}")
            continue

        inferred_nodes = filter(lambda node: node is not Uninferable, inference_results)
        inferred_node: FunctionDef = next(inferred_nodes, None)

        if not inferred_node:
            logger.error(f"Could not infer function call (soft): {func}")
            continue

        function_qualified_name = node.qname()
        called_function_qualified_name = inferred_node.qname()

        prefix = get_module_prefix(current_file_path)
        if not called_function_qualified_name.startswith(prefix):
            continue

        function_qualified_name = remove_module_prefix(
            function_qualified_name, current_file_path
        )

        called_function_qualified_name = remove_module_prefix(
            called_function_qualified_name, current_file_path
        )

        calls_rel = {
            "type": "calls_rel",
            "function_qualified_name": function_qualified_name,
            "called_function_qualified_name": called_function_qualified_name,
        }

        yield calls_rel

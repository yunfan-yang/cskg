from astroid import InferenceError, FunctionDef, Call, NodeNG, Uninferable
from loguru import logger

from interpreter.nodes import visit_children


def visit_function(node: FunctionDef, current_file_path: str = None):
    name = node.name
    qualified_name = node.qname()
    args = node.args

    function_ent = {
        "type": "function",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield function_ent

    yield from visit_function_inferred_nodes(node)
    yield from visit_children(node, current_file_path)


def visit_function_inferred_nodes(node: FunctionDef):
    """
    Visit body and write down node function calls other functions.
    """
    calls = [
        body_node_child
        for body_node in node.body
        for body_node_child in body_node.nodes_of_class(Call)
    ]

    for call in calls:
        try:
            """
            Multiple Possible Inferences:
            In Python, a name (like that of a function) can refer to multiple different objects over the course
            of a program's execution. Astroid's inference engine takes this into account and attempts to infer
            all possible objects a name could refer to at a given point in the code.
            For example, if a function name is reassigned multiple times to different callable objects,
            inferred() will return all of these possibilities.
            """
            called_function = call.func
            inference_results = called_function.inferred()
        except InferenceError:
            logger.error(f"Could not infer function call: {call}")
            continue

        inferred_nodes = filter(lambda node: node is not Uninferable, inference_results)
        inferred_node = next(inferred_nodes, None)

        if not inferred_node:
            logger.error(f"Could not infer function call (soft): {call}")
            continue

        function_qualified_name = node.qname()
        called_function_qualified_name = inferred_node.qname()

        calls_rel = {
            "type": "calls_rel",
            "function_qualified_name": function_qualified_name,
            "called_function_qualified_name": called_function_qualified_name,
        }

        yield calls_rel

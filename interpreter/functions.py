from typing import Union
import astroid

from interpreter.nodes import visit_children


CallableNode = Union[
    astroid.FunctionDef, astroid.BoundMethod, astroid.UnboundMethod, astroid.Lambda
]


def visit_function(node: astroid.FunctionDef, current_file_path: str = None):
    name = node.name
    qualified_name = node.qname()
    args = node.args

    fnr = {
        "type": "function",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield fnr

    yield from visit_function_inferred_nodes(node)
    yield from visit_children(node, current_file_path)


def visit_function_inferred_nodes(node: astroid.FunctionDef):
    # Visit body and write down function calls
    calls = [
        body_node_child
        for body_node in node.body
        for body_node_child in body_node.get_children()
        if isinstance(body_node_child, astroid.Call)
    ]

    for call in calls:
        inferred_nodes = []
        try:
            """
            Multiple Possible Inferences:
            In Python, a name (like that of a function) can refer to multiple different objects over the course
            of a program's execution. Astroid's inference engine takes this into account and attempts to infer
            all possible objects a name could refer to at a given point in the code.
            For example, if a function name is reassigned multiple times to different callable objects,
            inferred() will return all of these possibilities.
            """

            inferred_nodes = call.func.inferred()
        except astroid.exceptions.InferenceError:
            pass

        # All arguments values passed to the inferred functions
        args_objects = call.args
        # args_values = [arg.value for arg in args_objects]

        # All parameters of the inferred functions
        for inferred_node in inferred_nodes:
            if isinstance(inferred_node, CallableNode):
                params_objects = inferred_node.args.args
                params_names = (
                    [param.name for param in params_objects] if params_objects else []
                )

                function_qualified_name = node.qname()
                called_function_qualified_name = inferred_node.qname()

                crr = {
                    "type": "calls_rel",
                    "function_qualified_name": function_qualified_name,
                    "called_function_qualified_name": called_function_qualified_name,
                }
                yield crr

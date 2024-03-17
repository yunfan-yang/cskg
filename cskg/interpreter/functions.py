from astroid import (
    InferenceError,
    FunctionDef,
    Call,
    Uninferable,
    ParentMissingError,
)
from loguru import logger

from cskg.interpreter import get_module_prefix
from cskg.interpreter.args import get_arguments_list, get_comprehensive_arguments_list
from cskg.interpreter.vars import visit_local_variables


def visit_function(function: FunctionDef, current_file_path: str = None):
    name = function.name
    qualified_name = function.qname()

    # Function subtype
    function_subtype = get_function_subtype(function)
    args = get_arguments_list(function)
    args_flat = [f"{arg_name}: {arg_type}" for arg_name, arg_type in args]

    logger.debug(f"function: {qualified_name} ({function_subtype})")

    # Class
    if function_subtype == "function":
        # Function
        function_ent = {
            "type": "function",
            "name": name,
            "qualified_name": qualified_name,
            "file_path": current_file_path,
            "args": args_flat,
        }
        yield function_ent

        # Module
        module = function.root()
        contains_mf_rel = {
            "type": "contains_mf_rel",
            "module_qualified_name": module.qname(),
            "function_qualified_name": qualified_name,
        }
        yield contains_mf_rel

    else:
        # Method
        class_node = function.parent.frame()
        class_name = class_node.name
        class_qualified_name = class_node.qname()
        method_ent = {
            "type": "method",
            "subtype": function_subtype,
            "name": name,
            "qualified_name": qualified_name,
            "args": args_flat,
            "class_name": class_name,
            "class_qualified_name": class_qualified_name,
            "file_path": current_file_path,
        }
        yield method_ent

        # Class
        contains_cf_rel = {
            "type": "contains_cf_rel",
            "class_qualified_name": qualified_name,
            "function_qualified_name": qualified_name,
        }
        yield contains_cf_rel

    yield from visit_function_called_nodes(function, current_file_path)
    yield from visit_function_return_node(function, current_file_path)
    yield from visit_function_arguments_nodes(function, current_file_path)
    yield from visit_local_variables(function, current_file_path)


def visit_function_called_nodes(function: FunctionDef, current_file_path: str = None):
    """
    Visit body and write down node function calls other functions.
    """

    calls = list(function.nodes_of_class(Call))
    called_funcs = [call.func for call in calls]

    # logger.debug(f"function calls: {calls}")
    # logger.debug(f"function infers: {called_funcs}")

    for called_func in called_funcs:
        try:
            """
            Multiple Possible Inferences:
            In Python, a name (like that of a function) can refer to multiple different objects over the course
            of a program's execution. Astroid's inference engine takes this into account and attempts to infer
            all possible objects a name could refer to at a given point in the code.
            For example, if a function name is reassigned multiple times to different callable objects,
            inferred() will return all of these possibilities.
            """
            inference_results = called_func.inferred()
        except InferenceError:
            logger.error(f"Could not infer function call (hard): {called_func}")
            continue

        inferred_nodes = filter(lambda node: node is not Uninferable, inference_results)
        inferred_node: FunctionDef = next(inferred_nodes, None)

        if not inferred_node:
            logger.error(f"Could not infer function call (soft): {called_func}")
            continue

        function_qualified_name = function.qname()
        callee_qualified_name = inferred_node.qname()

        prefix = get_module_prefix(current_file_path)
        if not callee_qualified_name.startswith(prefix):
            continue

        calls_rel = {
            "type": "calls_rel",
            "caller_qualified_name": function_qualified_name,
            "callee_qualified_name": callee_qualified_name,
        }

        yield calls_rel


def visit_function_return_node(function: FunctionDef, current_file_path: str):
    """
    Visit body and write down node function returns
    """

    try:
        inference_results = function.infer_call_result(None)
    except InferenceError:
        logger.error(f"Could not infer function return: {function}")
        return

    inferred_nodes = filter(lambda node: node is not Uninferable, inference_results)
    inferred_nodes = list(inferred_nodes)

    # logger.debug(f"function returns: {inferred_nodes}")

    for inferred_node in inferred_nodes:
        # logger.debug(f"inferred_node: {inferred_node}")

        return_type = None

        if hasattr(inferred_node, "pytype"):
            return_type = inferred_node.pytype()
        elif hasattr(inferred_node, "qname"):
            return_type = inferred_node.qname()
        else:
            return_type = type(inferred_node).__name__

        prefix = get_module_prefix(current_file_path)
        if not return_type.startswith(prefix):
            continue

        function_qualified_name = function.qname()
        class_qualified_name = return_type
        returns_rel = {
            "type": "returns_rel",
            "function_qualified_name": function_qualified_name,
            "class_qualified_name": class_qualified_name,
        }

        yield returns_rel


def visit_function_arguments_nodes(function: FunctionDef, current_file_path: str):
    arguments_list = get_arguments_list(function)

    for argument_name, inferred_type_qualified_name in arguments_list:
        prefix = get_module_prefix(current_file_path)
        if not inferred_type_qualified_name.startswith(prefix):
            continue

        function_qualified_name = function.qname()
        yield {
            "type": "takes_rel",
            "function_qualified_name": function_qualified_name,
            "argument_name": argument_name,
            "argument_type_qualified_name": inferred_type_qualified_name,
        }


def get_function_subtype(function: FunctionDef):
    """
    Get function subtype: `function`, `method`, `classmethod`, `staticmethod`
    """
    try:
        return function.type
    except ParentMissingError:
        return "function"
    except Exception as e:
        raise e

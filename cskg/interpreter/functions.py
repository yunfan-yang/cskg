from astroid import (
    InferenceError,
    FunctionDef,
    Call,
    Uninferable,
    ParentMissingError,
    NodeNG,
)
from loguru import logger

from cskg.interpreter import get_inferred_type, get_inferred_types
from cskg.interpreter.params import (
    get_parameters_list,
    get_comprehensive_parameters_list,
)
from cskg.interpreter.vars import visit_local_variables


def visit_function(function: FunctionDef):
    name = function.name
    qualified_name = function.qname()
    file_path = function.root().file

    # Function subtype
    function_subtype = get_function_subtype(function)
    args = get_parameters_list(function)
    args_flat = [f"{arg_name}: {arg_type}" for arg_name, arg_type in args]

    logger.debug(f"function: {qualified_name} ({function_subtype})")

    # Class
    if function_subtype == "function":
        # Function
        function_ent = {
            "type": "function",
            "name": name,
            "qualified_name": qualified_name,
            "file_path": file_path,
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
            "file_path": file_path,
        }
        yield method_ent

        # Class
        contains_cf_rel = {
            "type": "contains_cf_rel",
            "class_qualified_name": qualified_name,
            "function_qualified_name": qualified_name,
        }
        yield contains_cf_rel

    yield from visit_function_called_nodes(function)
    yield from visit_function_return_node(function)
    yield from visit_function_arguments_nodes(function)
    yield from visit_local_variables(function)


def visit_function_called_nodes(function: FunctionDef):
    """
    Visit body and write down node function calls other functions.
    """

    calls = list(function.nodes_of_class(Call))
    called_funcs = [call.func for call in calls]

    for called_func in called_funcs:
        inferred_node = get_inferred_type(called_func)
        if not isinstance(inferred_node, NodeNG):
            logger.error(f"Could not infer function call (soft): {called_func}")
            continue

        function_qualified_name = function.qname()
        callee_qualified_name = inferred_node.qname()
        calls_rel = {
            "type": "calls_rel",
            "caller_qualified_name": function_qualified_name,
            "callee_qualified_name": callee_qualified_name,
        }

        yield calls_rel


def visit_function_return_node(function: FunctionDef):
    """
    Visit body and write down node function returns
    """
    inferred_nodes = get_inferred_types(function, lambda: function.infer_call_result(None))

    for inferred_node in inferred_nodes:
        return_type = None

        if hasattr(inferred_node, "pytype"):
            return_type = inferred_node.pytype()
        elif hasattr(inferred_node, "qname"):
            return_type = inferred_node.qname()
        else:
            return_type = type(inferred_node).__name__

        function_qualified_name = function.qname()
        class_qualified_name = return_type
        returns_rel = {
            "type": "returns_rel",
            "function_qualified_name": function_qualified_name,
            "class_qualified_name": class_qualified_name,
        }

        yield returns_rel


def visit_function_arguments_nodes(function: FunctionDef):
    arguments_list = get_parameters_list(function)

    for argument_name, inferred_type_qualified_name in arguments_list:
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

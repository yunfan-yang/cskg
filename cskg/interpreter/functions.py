from astroid import (
    FunctionDef,
    Call,
    ParentMissingError,
)
from astroid.nodes import LocalsDictNodeNG, BaseContainer
from loguru import logger

from cskg.interpreter import get_inferred_type, get_inferred_types
from cskg.interpreter.params import visit_parameters
from cskg.interpreter.vars import visit_local_variables


def visit_function(function: FunctionDef):
    name = function.name
    qualified_name = function.qname()
    file_path = function.root().file

    # Function subtype
    function_subtype = get_function_subtype(function)
    # logger.debug(f"function: {qualified_name} ({function_subtype})")

    # Class
    if function_subtype == "function":
        # Function
        function_ent = {
            "type": "function_ent",
            "file_path": file_path,
            "name": name,
            "qualified_name": qualified_name,
            "subtype": function_subtype,
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
            "type": "method_ent",
            "subtype": function_subtype,
            "name": name,
            "qualified_name": qualified_name,
            "class_name": class_name,
            "class_qualified_name": class_qualified_name,
            "file_path": file_path,
        }
        yield method_ent

        # Class
        contains_cf_rel = {
            "type": "contains_cf_rel",
            "class_qualified_name": qualified_name,
            "method_qualified_name": qualified_name,
        }
        yield contains_cf_rel

    yield from visit_function_called_nodes(function)
    yield from visit_function_return_node(function)
    yield from visit_local_variables(function)
    yield from visit_parameters(function)


def visit_function_called_nodes(function: FunctionDef):
    """
    Visit body and write down node function calls other functions.
    """

    calls = list(function.nodes_of_class(Call))
    for call in calls:
        # Arguments
        args = call.args  # The positional arguments being given to the call
        keywords = call.keywords  # The keyword arguments being given to the call

        arguments = []

        for arg in args:
            inferred_node = get_inferred_type(arg)
            if isinstance(inferred_node, LocalsDictNodeNG):
                arguments.append(inferred_node.qname())
            elif isinstance(inferred_node, BaseContainer):
                arguments.append(inferred_node.pytype())
            else:
                arguments.append("Any")

        for keyword in keywords:
            arg_name = keyword.arg
            if not arg_name:
                continue
            inferred_node = get_inferred_type(keyword.value)
            if isinstance(inferred_node, LocalsDictNodeNG):
                arguments.append(arg_name + "=" + inferred_node.qname())
            else:
                arguments.append(arg_name + "=" + "Any")

        # Callee function
        called_func = call.func  # What is being called
        inferred_node = get_inferred_type(called_func)
        if not isinstance(inferred_node, LocalsDictNodeNG):
            logger.error(f"Could not infer function call (soft): {called_func}")
            continue

        function_qualified_name = function.qname()
        callee_qualified_name = inferred_node.qname()
        calls_rel = {
            "type": "calls_rel",
            "caller_qualified_name": function_qualified_name,
            "callee_qualified_name": callee_qualified_name,
            "arguments": arguments,
        }

        yield calls_rel


def visit_function_return_node(function: FunctionDef):
    """
    Visit body and write down node function returns
    """
    inferred_nodes = get_inferred_types(
        function, lambda: function.infer_call_result(None)
    )

    for inferred_node in inferred_nodes:
        return_type = None

        if isinstance(inferred_node, LocalsDictNodeNG):
            return_type = inferred_node.qname()
        elif isinstance(inferred_node, BaseContainer):
            return_type = inferred_node.pytype()
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

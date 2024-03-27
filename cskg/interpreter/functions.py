from astroid import (
    FunctionDef,
    Call,
    ParentMissingError,
)
from astroid.nodes import LocalsDictNodeNG, BaseContainer
from loguru import logger

from cskg.entity import FunctionEntity, MethodEntity, ModuleEntity, ClassEntity
from cskg.relationship import ContainsRel, ReturnsRel, CallsRel, YieldsRel
from cskg.interpreter import (
    FunctionType,
    get_inferred_type,
    get_inferred_types,
    visit_external_entity,
)
from cskg.interpreter.params import visit_parameters
from cskg.interpreter.vars import visit_local_variables


def visit_function(function: FunctionDef):
    name = function.name
    qualified_name = function.qname()
    file_path = function.root().file
    is_abstract = function.is_abstract()

    # Function subtype
    function_subtype = get_function_subtype(function)
    # logger.debug(f"function: {qualified_name} ({function_subtype})")

    # Class
    if function_subtype == "function":
        # Function
        function_ent = FunctionEntity(
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            subtype=function_subtype,
        )
        yield function_ent

        # Module
        module = function.root()
        contains_mf_rel = ContainsRel(
            from_type=ModuleEntity,
            from_qualified_name=module.qname(),
            to_type=FunctionEntity,
            to_qualified_name=qualified_name,
        )
        yield contains_mf_rel

    else:
        # Method
        class_node = function.parent.frame()
        class_name = class_node.name
        class_qualified_name = class_node.qname()
        method_ent = MethodEntity(
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            subtype=function_subtype,
            class_name=class_name,
            class_qualified_name=class_qualified_name,
            is_abstract=is_abstract,
        )
        yield method_ent

        # Class
        contains_cf_rel = ContainsRel(
            from_type=ClassEntity,
            from_qualified_name=class_qualified_name,
            to_type=MethodEntity,
            to_qualified_name=qualified_name,
        )
        yield contains_cf_rel

    yield from visit_function_called_nodes(function)
    yield from visit_function_return_node(function)
    yield from visit_function_yield_node(function)
    yield from visit_local_variables(function)
    yield from visit_parameters(function, function_subtype)


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
            argument_type = get_inferred_node_qname(inferred_node)
            arguments.append(argument_type)

        for keyword in keywords:
            arg_name = keyword.arg
            if not arg_name:
                continue
            inferred_node = get_inferred_type(keyword.value)
            argument_type = get_inferred_node_qname(inferred_node)
            arguments.append(f"{arg_name}={argument_type}")

        # Callee function
        called_func = call.func  # What is being called
        inferred_node = get_inferred_type(called_func)
        if not isinstance(inferred_node, LocalsDictNodeNG):
            logger.error(f"Could not infer function call (soft): {called_func}")
            continue

        yield from visit_external_entity(inferred_node)

        function_qualified_name = function.qname()
        callee_qualified_name = inferred_node.qname()
        calls_rel = CallsRel(
            from_type=FunctionEntity,
            from_qualified_name=function_qualified_name,
            to_type=FunctionEntity,
            to_qualified_name=callee_qualified_name,
            arguments=arguments,
        )

        yield calls_rel


def visit_function_return_node(function: FunctionDef):
    """
    Visit body and write down node function returns
    """
    inferred_nodes = get_inferred_types(
        function, lambda: function.infer_call_result(None)
    )

    for inferred_node in inferred_nodes:
        yield from visit_external_entity(inferred_node)

        return_type = get_inferred_node_qname(inferred_node)
        function_qualified_name = function.qname()
        class_qualified_name = return_type
        returns_rel = ReturnsRel(
            from_type=FunctionEntity,
            from_qualified_name=function_qualified_name,
            to_type=ClassEntity,
            to_qualified_name=class_qualified_name,
        )
        yield returns_rel


def visit_function_yield_node(function: FunctionDef):
    """
    Visit body and write down node function yields
    """
    inferred_nodes = get_inferred_types(
        function, lambda: function.infer_yield_result(None)
    )

    for inferred_node in inferred_nodes:
        yield from visit_external_entity(inferred_node)

        return_type = get_inferred_node_qname(inferred_node)
        function_qualified_name = function.qname()
        class_qualified_name = return_type
        yields_rel = YieldsRel(
            from_type=FunctionEntity,
            from_qualified_name=function_qualified_name,
            to_type=ClassEntity,
            to_qualified_name=class_qualified_name,
        )
        yield yields_rel


def get_function_subtype(function: FunctionDef) -> FunctionType:
    """
    Get function subtype: `function`, `method`, `classmethod`, `staticmethod`
    """
    try:
        return FunctionType(function.type)
    except ParentMissingError:
        return FunctionType.FUNCTION
    except Exception as e:
        raise e


def get_inferred_node_qname(inferred_node):
    if isinstance(inferred_node, LocalsDictNodeNG):
        return inferred_node.qname()
    elif isinstance(inferred_node, BaseContainer):
        return inferred_node.pytype()
    else:
        return "Any"

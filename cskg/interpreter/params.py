from astroid import (
    AssignName,
    Arguments,
    FunctionDef,
)
from astroid.exceptions import NoDefault
from loguru import logger

from cskg.utils.entity import ExternalClassEntity, FunctionEntity, ClassEntity
from cskg.utils.relationship import TakesRel
from cskg.interpreter.vars import (
    get_variable_inferred_type_qname,
    get_variable_inferred_type,
)
from cskg.interpreter.utils import FunctionType, visit_external_entity


def visit_parameters(function: FunctionDef, function_subtype: FunctionType):
    function_qname = function.qname()
    arguments_obj = function.args
    is_method = function_subtype in [FunctionType.METHOD, FunctionType.CLASSMETHOD]

    for index, param_assign_name in enumerate(arguments_obj.arguments):
        # Skip method self/cls
        if is_method and index == 0:
            continue

        param_name = param_assign_name.name
        default_value = get_parameter_default_value(arguments_obj, param_assign_name)

        inferred_type = get_variable_inferred_type(param_assign_name)
        inferred_type_qname = get_variable_inferred_type_qname(param_assign_name)

        if inferred_type_qname:
            yield from visit_external_entity(inferred_type)
            takes_rel = TakesRel(
                from_type=FunctionEntity,
                from_qualified_name=function_qname,
                to_type=ClassEntity,
                to_qualified_name=inferred_type_qname,
                param_name=param_name,
                default_value=default_value,
            )
            yield takes_rel
        else:
            any_ent = ExternalClassEntity(
                name="Any",
                qualified_name="builtins.Any",
                file_path=None,
            )
            yield any_ent

            takes_rel = TakesRel(
                from_type=FunctionEntity,
                from_qualified_name=function_qname,
                to_type=ClassEntity,
                to_qualified_name=any_ent.qualified_name,
                param_name=param_name,
                default_value=default_value,
            )
            yield takes_rel


def get_parameter_default_value(arguments_obj: Arguments, assign_name: AssignName):
    param_name = assign_name.name

    try:
        default_value_obj = arguments_obj.default_value(param_name)
        return default_value_obj.as_string()
    except NoDefault:
        return None

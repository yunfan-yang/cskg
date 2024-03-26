from astroid import (
    AssignName,
    Name,
    Arguments,
    FunctionDef,
    Const,
)
from astroid.exceptions import NoDefault
from astroid.nodes import LocalsDictNodeNG
from loguru import logger

from cskg.entity import FunctionEntity, ClassEntity
from cskg.interpreter.vars import get_variable_inferred_type_qname
from cskg.relationship import TakesRel
from cskg.interpreter import FunctionType, get_inferred_type


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

        inferred_type_qname = get_variable_inferred_type_qname(param_assign_name)
        takes_rel = TakesRel(
            from_type=FunctionEntity,
            from_qualified_name=function_qname,
            to_type=ClassEntity,
            to_qualified_name=inferred_type_qname,
            param_name=param_name,
            default_value=default_value,
        )
        yield takes_rel


def get_parameter_default_value(arguments_obj: Arguments, assign_name: AssignName):
    param_name = assign_name.name

    try:
        default_value_obj = arguments_obj.default_value(param_name)

        # If default value is a Name, infer its type
        if isinstance(default_value_obj, Name):
            default_value_inferred_type = get_inferred_type(default_value_obj)

            # If inferrable and inferred type is a LocalsDictNodeNG, get its qname
            if isinstance(default_value_inferred_type, LocalsDictNodeNG):
                return default_value_inferred_type.qname()

            # Pure name
            else:
                return default_value_obj.name

        # If default value is a Const, get its value
        elif isinstance(default_value_obj, Const):
            return default_value_obj.value

        # If default value is not a Name or a Const, need further investigation
        else:
            raise Exception(f"Unknown default value type: {type(default_value_obj)}")

    except NoDefault:
        return None

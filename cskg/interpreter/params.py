from astroid import (
    InferenceError,
    Uninferable,
    AssignName,
    Name,
    Arguments,
    FunctionDef,
    Const,
)
from astroid.typing import InferenceResult
from astroid.exceptions import NoDefault
from astroid.nodes import LocalsDictNodeNG
from loguru import logger

from cskg.interpreter import get_inferred_type

ComprehensiveArgument = tuple[AssignName, Name, InferenceResult]
ComprehensiveArgumentList = list[ComprehensiveArgument]
ArgumentList = list[tuple[str, str]]


def get_comprehensive_parameters_list(arguments: Arguments):
    args = arguments.args
    annotations = arguments.annotations

    # Zip arguments and annotations
    arguments_annotations: list[tuple[AssignName, Name]] = zip(args, annotations)
    inferred_types = []

    for argument, annotation in arguments_annotations:
        # Infer argument type
        try:
            inference_results = argument.inferred()
        except InferenceError:
            logger.error(f"Could not infer argument (hard): {argument}")

        # Infer annotation type
        try:
            if annotation is not None:
                inference_results = annotation.inferred()
        except InferenceError:
            logger.error(f"Could not infer annotation (hard): {annotation}")

        inferred_nodes = filter(lambda node: node is not Uninferable, inference_results)
        inferred_node = next(inferred_nodes, None)

        inferred_types.append(inferred_node)

    comprehesive_list: ComprehensiveArgumentList = list(
        zip(args, annotations, inferred_types)
    )
    return comprehesive_list


def get_parameters_list(node: FunctionDef):
    comprehensive_arguments_list = get_comprehensive_parameters_list(node.args)
    arguments_list: ArgumentList = []

    for argument, annotation, inferred_type in comprehensive_arguments_list:
        if inferred_type:
            inferred_type_qualified_name = inferred_type.qname()
        elif annotation:
            inferred_type_qualified_name = str(annotation)
        else:
            inferred_type_qualified_name = "Any"

        argument_name = argument.name
        arguments_list.append((argument_name, inferred_type_qualified_name))

    return arguments_list


def visit_parameters(function: FunctionDef):
    function_qname = function.qname()
    arguments_obj = function.args

    for assign_name_obj in arguments_obj.arguments:
        param_name = assign_name_obj.name
        param_qname = f"{function_qname}.{param_name}"
        default_value = get_parameter_default_value(arguments_obj, assign_name_obj)

        # NOTE: Parameters are also local variables, and them entities are declared in
        # variables visitor, therfore, no variables and instantiates_rel are declared here.

        # Takes rel
        takes_rel = {
            "type": "takes_rel",
            "function_qualified_name": function.qname(),
            "param_qualified_name": param_qname,
            "default_value": default_value,
        }
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
                default_value = default_value_inferred_type.qname()

            # Pure name
            else:
                default_value = default_value_obj.name

        # If default value is a Const, get its value
        elif isinstance(default_value_obj, Const):
            default_value = default_value_obj.value

        # If default value is not a Name or a Const, need further investigation
        else:
            raise Exception(f"Unknown default value type: {type(default_value_obj)}")

    except NoDefault:
        return None

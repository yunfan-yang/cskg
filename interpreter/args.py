from astroid import (
    InferenceError,
    Uninferable,
    AssignName,
    Name,
    Arguments,
    FunctionDef,
)
from astroid.typing import InferenceResult
from loguru import logger

ComprehensiveArgument = tuple[AssignName, Name, InferenceResult]
ComprehensiveArgumentList = list[ComprehensiveArgument]
ArgumentList = list[tuple[str, str]]


def get_comprehensive_arguments_list(arguments: Arguments):
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


def get_arguments_list(node: FunctionDef):
    comprehensive_arguments_list = get_comprehensive_arguments_list(node.args)
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

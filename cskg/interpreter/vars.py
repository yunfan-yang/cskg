from astroid import (
    Module,
    ClassDef,
    FunctionDef,
    NodeNG,
    AssignName,
    Const,
)
from astroid.nodes import LocalsDictNodeNG
from loguru import logger

from cskg.entity import VariableEntity, ClassEntity, FunctionEntity, ModuleEntity
from cskg.relationship import ContainsRel, InstantiatesRel
from cskg.interpreter import get_inferred_type


def visit_local_variables(node: Module | ClassDef | FunctionDef):
    qname = node.qname()
    file_path = node.root().file

    # var_assign_name: AssignName
    for var_name, var_assign_name in node.items():
        # Only variables
        if not isinstance(var_assign_name, AssignName):
            continue

        var_qname = qname + "." + var_name
        access = get_variable_access(var_name)

        # Variable entity
        variable_ent = VariableEntity(
            name=var_name,
            qualified_name=var_qname,
            access=access,
            file_path=file_path,
        )
        yield variable_ent

        # Containment relationships
        yield from get_contains_rel(node, var_qname)

        # Variable instantiate from class
        var_inferred_type = get_inferred_type(var_assign_name)
        if isinstance(var_inferred_type, Const):
            inferred_type_qname = var_inferred_type.pytype()
        elif not isinstance(var_inferred_type, LocalsDictNodeNG):
            logger.error(
                f"Invalid inferred type for var {var_assign_name}: {var_inferred_type}"
            )
            continue
        else:
            inferred_type_qname = var_inferred_type.qname()

        instantiates_rel = InstantiatesRel(
            from_type=ClassEntity,
            from_qualified_name=inferred_type_qname,
            to_type=VariableEntity,
            to_qualified_name=var_qname,
        )
        yield instantiates_rel


def get_variable_access(variable_name: str):
    if variable_name.startswith("__") and not variable_name.endswith("__"):
        return "private"
    if variable_name.startswith("_"):
        return "protected"
    return "public"


def get_contains_rel(node: NodeNG, var_qname: str):
    qname = node.qname()

    if isinstance(node, ClassDef):
        contains_cv_rel = ContainsRel(
            from_type=ClassEntity,
            from_qualified_name=qname,
            to_type=VariableEntity,
            to_qualified_name=var_qname,
        )
        yield contains_cv_rel
    elif isinstance(node, FunctionDef):
        contains_fv_rel = ContainsRel(
            from_type=FunctionEntity,
            from_qualified_name=qname,
            to_type=VariableEntity,
            to_qualified_name=var_qname,
        )
        yield contains_fv_rel
    elif isinstance(node, Module):
        contains_mv_rel = ContainsRel(
            from_type=ModuleEntity,
            from_qualified_name=qname,
            to_type=VariableEntity,
            to_qualified_name=var_qname,
        )
        yield contains_mv_rel
    else:
        raise ValueError(f"Node {node} is not a ClassDef or FunctionDef")

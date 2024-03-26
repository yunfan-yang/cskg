from astroid import Module

from cskg.entity import ModuleEntity
from cskg.interpreter.nodes import visit_children
from cskg.interpreter.vars import visit_local_variables


def visit_module(module: Module):
    name = get_module_name(module)
    qualified_name = module.qname()
    file_path = module.root().file

    module_ent = ModuleEntity(
        name=name,
        qualified_name=qualified_name,
        file_path=file_path,
    )
    yield module_ent

    yield from visit_local_variables(module)
    yield from visit_children(module)


def get_module_name(module: Module):
    return module.qname().split(".").pop(-1)

from astroid import Module

from cskg.interpreter.nodes import visit_children
from cskg.interpreter.vars import visit_local_variables


def visit_module(module: Module, current_file_path: str = None):
    name = module.name
    qualified_name = module.qname()

    module_ent = {
        "type": "module",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }

    yield module_ent
    yield from visit_local_variables(module, current_file_path)

    yield from visit_children(module, current_file_path)
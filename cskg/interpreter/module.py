from astroid import Module

from cskg.interpreter.nodes import visit_children
from cskg.interpreter.vars import visit_local_variables


def visit_module(module: Module):
    name = module.name
    qualified_name = module.qname()
    file_path = module.root().file

    module_ent = {
        "type": "module_ent",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": file_path,
    }
    yield module_ent
    
    yield from visit_local_variables(module)
    yield from visit_children(module)

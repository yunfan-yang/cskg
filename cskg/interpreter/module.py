from astroid import Module


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
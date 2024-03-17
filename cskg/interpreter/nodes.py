import astroid


def visit_node(node: astroid.NodeNG, current_file_path: str):
    if isinstance(node, astroid.Module):
        from cskg.interpreter.module import visit_module

        yield from visit_module(node, current_file_path)

    elif isinstance(node, astroid.ClassDef):
        from cskg.interpreter.classes import visit_class

        yield from visit_class(node, current_file_path)

    elif isinstance(node, astroid.FunctionDef):
        from cskg.interpreter.functions import visit_function

        yield from visit_function(node, current_file_path)


def visit_children(node: astroid.NodeNG, current_file_path: str):
    for child in node.get_children():
        yield from visit_node(child, current_file_path)

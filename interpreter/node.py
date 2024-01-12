import astroid


def visit_node(node, current_file_path: str = None):
    if isinstance(node, astroid.ClassDef):
        from interpreter.classes import visit_class

        yield from visit_class(node, current_file_path)

    elif isinstance(node, astroid.FunctionDef):
        from interpreter.functions import visit_function

        yield from visit_function(node, current_file_path)


def visit_children(node: astroid.NodeNG, current_file_path: str = None):
    children = node.get_children()
    for child in children:
        yield from visit_node(child, current_file_path)

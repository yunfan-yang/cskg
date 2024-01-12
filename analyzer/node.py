import astroid


def visit_node(node):
    if isinstance(node, astroid.ClassDef):
        from analyzer.classes import visit_class

        yield from visit_class(node)

    elif isinstance(node, astroid.FunctionDef):
        from analyzer.functions import visit_function

        yield from visit_function(node)


def visit_children(node: astroid.NodeNG):
    children = node.get_children()
    for child in children:
        yield from visit_node(child)

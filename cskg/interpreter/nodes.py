import astroid


def visit_node(node: astroid.NodeNG):
    if isinstance(node, astroid.Module):
        from cskg.interpreter.module import visit_module

        yield from visit_module(node)

    elif isinstance(node, astroid.ClassDef):
        from cskg.interpreter.classes import visit_class

        yield from visit_class(node)

    elif isinstance(node, astroid.FunctionDef):
        from cskg.interpreter.functions import visit_function

        yield from visit_function(node)


def visit_children(node: astroid.NodeNG):
    for child in node.get_children():
        yield from visit_node(child)

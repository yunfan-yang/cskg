import astroid

from analyzer.node import visit_children


def visit_class(node: astroid.ClassDef, current_file_path: str = None):
    name = node.name
    qualified_name = node.qname()

    # Create class
    cls = {
        "type": "class",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield cls

    # Visit parents
    parent_classes = node.ancestors(recurs=False)
    for parent_class in parent_classes:
        ihs = {
            "type": "inherits",
            "class_qualified_name": qualified_name,
            "inherited_class_qualified_name": parent_class.qname(),
        }
        yield ihs

    # Visit children
    yield from visit_children(node)

import astroid

from cskg.interpreter.nodes import visit_children


def visit_class(node: astroid.ClassDef, current_file_path: str = None):
    name = node.name
    qualified_name = node.qname()

    # Create class
    class_ent = {
        "type": "class",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield class_ent

    # Visit parents
    parent_classes = node.ancestors(recurs=False)
    for parent_class in parent_classes:
        child_qualified_name = qualified_name
        parent_qualified_name = parent_class.qname()
        inherits_rel = {
            "type": "inherits_rel",
            "child_qualified_name": child_qualified_name,
            "parent_qualified_name": parent_qualified_name,
        }
        yield inherits_rel

    # Visit children
    # yield from visit_children(node, current_file_path)
    children_nodes = visit_children(node, current_file_path)

    for child_node in children_nodes:
        yield child_node

        if child_node["type"] == "function" or child_node["type"] == "method":
            function_qualified_name = child_node["qualified_name"]
            contains_cf_rel = {
                "type": "contains_cf_rel",
                "class_qualified_name": qualified_name,
                "function_qualified_name": function_qualified_name,
            }
            yield contains_cf_rel

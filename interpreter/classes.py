import astroid

from interpreter import remove_module_prefix
from interpreter.nodes import visit_children


def visit_class(node: astroid.ClassDef, current_file_path: str = None):
    name = node.name
    qualified_name = remove_module_prefix(node.qname(), current_file_path)

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
        inherited_class_qualified_name = remove_module_prefix(
            parent_class.qname(), current_file_path
        )
        inherits_rel = {
            "type": "inherits_rel",
            "class_qualified_name": qualified_name,
            "inherited_class_qualified_name": inherited_class_qualified_name,
        }
        yield inherits_rel

    # Visit children
    # yield from visit_children(node, current_file_path)
    children_nodes = visit_children(node, current_file_path)

    for child_node in children_nodes:
        yield child_node

        if child_node["type"] == "function":
            function_qualified_name = remove_module_prefix(
                child_node["qualified_name"], current_file_path
            )
            contains_rel = {
                "type": "contains_rel",
                "class_qualified_name": qualified_name,
                "function_qualified_name": function_qualified_name,
            }
            yield contains_rel

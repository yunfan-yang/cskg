from astroid import ClassDef

from cskg.interpreter.nodes import visit_children


def visit_class(cls: ClassDef, current_file_path: str = None):
    name = cls.name
    qualified_name = cls.qname()
    module_qname = cls.root().qname()

    # Create class
    class_ent = {
        "type": "class",
        "name": name,
        "qualified_name": qualified_name,
        "file_path": current_file_path,
    }
    yield class_ent

    # Module contains class
    contains_mc_rel = {
        "type": "contains_mc_rel",
        "module_qualified_name": module_qname,
        "class_qualified_name": qualified_name,
    }
    yield contains_mc_rel

    # Visit parents
    parent_classes = cls.ancestors(recurs=False)
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
    children_nodes = visit_children(cls, current_file_path)

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

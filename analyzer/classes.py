import json
import astroid

from analyzer.models import ClassRow, InheritsRelRow
from analyzer.node import visit_children


def visit_class(node: astroid.ClassDef, current_file_path: str = None):
    name = node.name
    qualified_name = node.qname()

    # Create class
    attributes = {"file_path": current_file_path}
    clr = ClassRow(
        name=name,
        qualified_name=qualified_name,
        is_created=False,
        attributes=json.dumps(attributes),
    )
    yield clr

    # Visit parents
    parent_classes = node.ancestors(recurs=False)
    for parent_class in parent_classes:
        ihs = InheritsRelRow(
            class_qualified_name=qualified_name,
            inherited_class_qualified_name=parent_class.qname(),
        )
        yield ihs

    # Visit children
    yield from visit_children(node)

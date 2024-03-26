from astroid import ClassDef

from cskg.entity import ModuleEntity, ClassEntity
from cskg.relationship import ContainsRel, InheritsRel
from cskg.interpreter.nodes import visit_children
from cskg.interpreter.vars import visit_local_variables


def visit_class(cls: ClassDef):
    name = cls.name
    qualified_name = cls.qname()
    module_qname = cls.root().qname()
    file_path = cls.root().file
    is_abstract = is_abstract_class(cls)

    # Create class
    class_ent = ClassEntity(
        name=name,
        qualified_name=qualified_name,
        file_path=file_path,
        is_abstract=is_abstract,
        is_external_entity=False,
    )
    yield class_ent

    # Module contains class
    contains_mc_rel = ContainsRel(
        from_type=ModuleEntity,
        from_qualified_name=module_qname,
        to_type=ClassEntity,
        to_qualified_name=qualified_name,
    )
    yield contains_mc_rel

    # Visit parents
    parent_classes = cls.ancestors(recurs=False)
    for parent_class in parent_classes:
        child_qualified_name = qualified_name
        parent_qualified_name = parent_class.qname()
        inherits_rel = InheritsRel(
            from_type=ClassEntity,
            from_qualified_name=child_qualified_name,
            to_type=ClassEntity,
            to_qualified_name=parent_qualified_name,
        )  # CHILD -[INHERITS]-> PARENT
        yield inherits_rel

    # Visit children
    yield from visit_children(cls)
    yield from visit_local_variables(cls)


def is_abstract_class(cls: ClassDef):
    """Check if the provided class node is an abstract class."""
    # Check if it has abstract method
    for method in cls.mymethods():
        if method.is_abstract():
            return True

    # Check if it inherits from ABC
    for parent in cls.ancestors():
        if parent.name == "ABC":
            return True

    return False

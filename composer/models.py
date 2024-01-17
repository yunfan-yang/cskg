from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    RelationshipTo,
)


class Calls(StructuredRel):
    ...


class Inherits(StructuredRel):
    ...


class Contains(StructuredRel):
    ...


class Function(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=False)
    file_path = StringProperty(required=True)

    ## Relationships
    calls = RelationshipTo("Function", "CALLS", model=Calls)


class Class(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    file_path = StringProperty(required=True)

    ## Relationships
    inherits = RelationshipTo("Class", "INHERITS", model=Inherits)
    contains = RelationshipTo("Function", "CONTAINS", model=Contains)

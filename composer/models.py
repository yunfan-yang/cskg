from neomodel import (
    StructuredNode,
    StringProperty,
    RelationshipTo,
)


class Function(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=False)
    file_path = StringProperty(required=True)

    ## Relationships
    calls = RelationshipTo("Function", "CALLS")


class Class(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    file_path = StringProperty(required=True)

    ## Relationships
    inherits = RelationshipTo(StructuredNode, "INHERITS")
    contains = RelationshipTo(StructuredNode, "CONTAINS")

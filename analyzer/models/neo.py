from neomodel import (
    config,
    StructuredNode,
    StringProperty,
    RelationshipTo,
)

config.AUTO_INSTALL_LABELS = True


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
    contains = RelationshipTo(StructuredNode, "CONTAINS")
    inherits = RelationshipTo(StructuredNode, "INHERITS")

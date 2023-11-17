from neomodel import (
    config,
    StructuredNode,
    StringProperty,
    IntegerProperty,
    UniqueIdProperty,
    RelationshipTo,
)


class Class(StructuredNode):
    id = UniqueIdProperty()
    name = StringProperty(required=True)
    full_name = StringProperty(unique_index=True, required=True)
    description = StringProperty(required=True)
    file_path = StringProperty(required=True)

    ## Relationships
    relates_to = RelationshipTo("Class", "RELATES_TO")
    invokes = RelationshipTo("Function", "INVOKES")


class Function(StructuredNode):
    id = UniqueIdProperty()
    name = StringProperty(required=True)
    full_name = StringProperty(unique_index=True, required=True)
    description = StringProperty(required=True)

    ## Relationships
    invokes = RelationshipTo("Function", "INVOKES")
    belongs_to = RelationshipTo("Class", "BELONGS_TO")

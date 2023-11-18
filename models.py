from os import environ

from dotenv import load_dotenv
from neomodel import (
    config,
    StructuredNode,
    StructuredRel,
    StringProperty,
    IntegerProperty,
    UniqueIdProperty,
    Relationship,
    RelationshipTo,
    RelationshipFrom,
)


load_dotenv()

config.DATABASE_URL = environ.get("NEO4J_URL")


class Calls(StructuredRel):
    args = StringProperty(required=True)
    keywords = StringProperty(required=True)


class Function(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    full_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=True)
    returns = StringProperty(required=True)

    ## Relationships
    calls = RelationshipTo("Function", "CALLS", model=Calls)


class Class(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    full_name = StringProperty(unique_index=True, required=True)

    ## Relationships
    contains = Relationship("Function", "CONTAINS")

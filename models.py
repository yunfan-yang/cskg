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
from sqlalchemy import create_engine

load_dotenv()

NEO4J_URL = environ.get("NEO4J_URL")
POSTGRES_URL = environ.get("POSTGRES_URL")

config.DATABASE_URL = NEO4J_URL
engine = create_engine(POSTGRES_URL)


class Calls(StructuredRel):
    args = StringProperty(required=True)
    keywords = StringProperty(required=True)


class Function(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=True)

    ## Relationships
    calls = RelationshipTo("Function", "CALLS", model=Calls)


class Class(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)

    ## Relationships
    contains = RelationshipTo(StructuredNode, "CONTAINS")

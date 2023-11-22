from os import environ

from dotenv import load_dotenv
from neomodel import (
    config,
    StructuredNode,
    StructuredRel,
    StringProperty,
    ArrayProperty,
    IntegerProperty,
    UniqueIdProperty,
    Relationship,
    RelationshipTo,
    RelationshipFrom,
)
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

NEO4J_URL = environ.get("NEO4J_URL")
POSTGRES_URL = environ.get("POSTGRES_URL")

config.DATABASE_URL = NEO4J_URL
engine = create_engine(POSTGRES_URL)


class CallsRel(StructuredRel):
    args = StringProperty(required=True)
    keywords = StringProperty(required=True)


class FunctionNode(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=True)
    file_path = StringProperty(required=True)

    inferred_nodes = ArrayProperty()

    ## Relationships
    calls = RelationshipTo("Function", "CALLS", model=CallsRel)


class ClassNode(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    file_path = StringProperty(required=True)

    ## Relationships
    contains = RelationshipTo(StructuredNode, "CONTAINS")


class PostgresBase(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"schema": "public"}


class CallsRelRow(PostgresBase):
    __tablename__ = "calls_rel"
    id = Column(Integer, primary_key=True)
    function_qualified_name = Column(String)
    called_function_qualified_name = Column(String)
    args = Column(String)
    keywords = Column(String)

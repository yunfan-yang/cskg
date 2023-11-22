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
from sqlalchemy import UniqueConstraint, create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase, Session

load_dotenv()

NEO4J_URL = environ.get("NEO4J_URL")
POSTGRES_URL = environ.get("POSTGRES_URL")

config.DATABASE_URL = NEO4J_URL
postgres_engine = create_engine(POSTGRES_URL)
postgres_session = Session(bind=postgres_engine)


class Function(StructuredNode):
    name = StringProperty(required=True)
    qualified_name = StringProperty(unique_index=True, required=True)
    args = StringProperty(required=True)
    file_path = StringProperty(required=True)

    ## Relationships
    calls = RelationshipTo("Function", "CALLS")


class Class(StructuredNode):
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

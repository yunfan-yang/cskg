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
    install_all_labels,
)
from sqlalchemy import UniqueConstraint, create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Session

load_dotenv()

NEO4J_URL = environ.get("NEO4J_URL")
POSTGRES_URL = environ.get("POSTGRES_URL")

config.DATABASE_URL = NEO4J_URL
config.AUTO_INSTALL_LABELS = True

postgres_engine = create_engine(POSTGRES_URL)
postgres_session = Session(bind=postgres_engine)


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


class PostgresBase(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"schema": "public"}


class ClassRow(PostgresBase):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    qualified_name = Column(String)
    is_created = Column(Boolean, default=False, nullable=False)
    attributes = Column(String)


class FunctionRow(PostgresBase):
    __tablename__ = "functions"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    qualified_name = Column(String)
    is_created = Column(Boolean, default=False, nullable=False)
    attributes = Column(String)


class CallsRelRow(PostgresBase):
    __tablename__ = "calls_rel"
    id = Column(Integer, primary_key=True)
    function_qualified_name = Column(String)
    called_function_qualified_name = Column(String)
    is_linked = Column(Boolean, default=False, nullable=False)


class InheritsRelRow(PostgresBase):
    __tablename__ = "inherits_rel"
    id = Column(Integer, primary_key=True)
    class_qualified_name = Column(String)
    inherited_class_qualified_name = Column(String)
    is_linked = Column(Boolean, default=False, nullable=False)

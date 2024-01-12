from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase


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

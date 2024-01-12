import neomodel
from analyzer.code_analyzer import CodeAnalyzer

from analyzer.models import (
    postgres_session,
    CallsRelRow,
    InheritsRelRow,
    ClassRow,
    FunctionRow,
)

# Clean database
postgres_session.query(ClassRow).delete()
postgres_session.query(FunctionRow).delete()
postgres_session.query(CallsRelRow).delete()
postgres_session.query(InheritsRelRow).delete()
postgres_session.commit()
neomodel.db.cypher_query("MATCH (n) DETACH DELETE n")
neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Function_qualified_name")
neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Class_qualified_name")

# Analyze codebase
ca = CodeAnalyzer("targets/requests")
ca.analyze()

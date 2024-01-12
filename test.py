import json
import os
from dotenv import load_dotenv
import neomodel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pymongo import MongoClient

from analyzer.code_analyzer import CodeAnalyzer


load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
POSTGRES_URL = os.environ.get("POSTGRES_URL")
MONGO_URL = os.environ.get("MONGO_URL")

neomodel.config.DATABASE_URL = NEO4J_URL
neomodel.config.AUTO_INSTALL_LABELS = True

postgres_engine = create_engine(POSTGRES_URL)
postgres_session = Session(bind=postgres_engine)

mongo_client = MongoClient(MONGO_URL)
database = mongo_client.code_analyzer
classes = database.classes
functions = database.functions
calls_rel = database.calls_rel
inherits_rel = database.inherits_rel

# Clean database
# postgres_session.query(ClassRow).delete()
# postgres_session.query(FunctionRow).delete()
# postgres_session.query(CallsRelRow).delete()
# postgres_session.query(InheritsRelRow).delete()
# postgres_session.commit()
# neomodel.db.cypher_query("MATCH (n) DETACH DELETE n")
# neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Function_qualified_name")
# neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Class_qualified_name")


# Analyze codebase
ca = CodeAnalyzer("targets/requests")
generator = ca.analyze()

while True:
    try:
        node = next(generator)

        if node.get("type") == "class":
            classes.insert_one(node)
        elif node.get("type") == "function":
            functions.insert_one(node)
        elif node.get("type") == "calls":
            calls_rel.insert_one(node)
        elif node.get("type") == "inherits":
            inherits_rel.insert_one(node)
    except:
        break

mongo_client.close()

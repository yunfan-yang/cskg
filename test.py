import json
import os
from dotenv import load_dotenv
import neomodel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pymongo import MongoClient
from loguru import logger

from interpreter.interpreter import CodeInterpreter


load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
POSTGRES_URL = os.environ.get("POSTGRES_URL")
MONGO_URL = os.environ.get("MONGO_URL")

neomodel.config.DATABASE_URL = NEO4J_URL
neomodel.config.AUTO_INSTALL_LABELS = True

postgres_engine = create_engine(POSTGRES_URL)
postgres_session = Session(bind=postgres_engine)

mongo_client = MongoClient(MONGO_URL)
database = mongo_client.code_interpreter

classes = database.classes
functions = database.functions
calls_rel = database.calls_rel
inherits_rel = database.inherits_rel

classes.drop()
functions.drop()
calls_rel.drop()
inherits_rel.drop()

# Clean database
# neomodel.db.cypher_query("MATCH (n) DETACH DELETE n")
# neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Function_qualified_name")
# neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Class_qualified_name")

logger.add("logs/default.log")

# Analyze codebase
ca = CodeInterpreter("targets/requests")
generator = ca.analyze()

while True:
    try:
        node = next(generator)

        logger.info(node)

        if node.get("type") == "class":
            classes.insert_one(node)
        elif node.get("type") == "function":
            functions.insert_one(node)
        elif node.get("type") == "calls_rel":
            calls_rel.insert_one(node)
        elif node.get("type") == "inherits_rel":
            inherits_rel.insert_one(node)
    except:
        break

mongo_client.close()

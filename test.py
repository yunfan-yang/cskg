import os
from dotenv import load_dotenv
import neomodel
from pymongo import MongoClient
from loguru import logger

from interpreter.interpreter import CodeInterpreter

# Load environment variables
load_dotenv()

NEO4J_URL = os.environ.get("NEO4J_URL")
MONGO_URL = os.environ.get("MONGO_URL")

neomodel.config.DATABASE_URL = NEO4J_URL
neomodel.config.AUTO_INSTALL_LABELS = True

# Instantiate mongo db client
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client.code_interpreter

# List all collections and drop all
for collection_name in mongo_db.list_collection_names():
    mongo_db.drop_collection(collection_name)


# Clean neo database
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

        node_type = node.get("type")
        mongo_db[node_type].insert_one(node)
    except:
        break

mongo_client.close()

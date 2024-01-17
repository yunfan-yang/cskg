from typing import Any
from pymongo import MongoClient
import neomodel
from loguru import logger

from composer.composer import GraphComposer
from interpreter.interpreter import CodeInterpreter

logger.add("logs/default.log")


DRIVER_CONFIGURATIONS = dict[str, Any]
# Configurations:
# {
#     "NEO4J_URL": str,
#     "MONGO_URL": str,
# }


class Driver:
    def __init__(self, folder_path: str, configurations: DRIVER_CONFIGURATIONS):
        self.folder_path = folder_path
        self.configurations = configurations
        self.interpreter = None
        self.graph_composer = None
        self.__init_database()

    def __init_database(self):
        neo4j_url = self.configurations.get("NEO4J_URL")
        mongo_url = self.configurations.get("MONGO_URL")

        # Load neomodel configurations
        neomodel.config.DATABASE_URL = neo4j_url
        neomodel.config.AUTO_INSTALL_LABELS = True
        self.neo_db = neomodel.db

        # Instantiate mongo db client
        mongo_client = MongoClient(mongo_url)
        mongo_db = mongo_client.code_interpreter
        self.mongo_db = mongo_db

        # Clean up
        _mongo_drop_all(self.mongo_db)
        _neo_drop_all(self.neo_db)

        # Create indexes
        # self.mongo_db.class_.create_index("qualified_name", unique=True)
        # self.mongo_db.function.create_index("qualified_name", unique=True)

    def run(self):
        # Instantiate
        self.interpreter = CodeInterpreter(self.folder_path)
        self.graph_composer = GraphComposer()

        # Interpretate codebase
        generator = self.interpreter.interpret()
        while True:
            try:
                node = next(generator)
                logger.info(node)
                node_type = node.get("type")
                self.mongo_db[node_type].insert_one(node)
            except StopIteration:
                break
            except Exception as e:
                logger.error(e)
                break
        logger.info("Interpretation done")

        # Compose graph
        self.graph_composer.classes = self.mongo_db.class_.find()
        self.graph_composer.functions = self.mongo_db.function.find()
        self.graph_composer.calls_rel = self.mongo_db.calls_rel.find()
        self.graph_composer.inherits_rel = self.mongo_db.inherits_rel.find()

        self.graph_composer.compose()
        logger.info("Composition done")

        logger.info("Done")


def _mongo_drop_all(mongo_db):
    for collection_name in mongo_db.list_collection_names():
        mongo_db.drop_collection(collection_name)


def _neo_drop_all(neo_db):
    neo_db.cypher_query("MATCH (n) DETACH DELETE n")

    constraints = neo_db.cypher_query("SHOW CONSTRAINTS")[0]
    for constraint in constraints:
        constraint_info = constraint[0]
        neomodel.db.cypher_query(f"DROP CONSTRAINT {constraint_info}")

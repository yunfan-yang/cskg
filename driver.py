from typing import Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
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
        self.neo_db.set_connection(neo4j_url)

        # Instantiate mongo db client
        mongo_client = MongoClient(mongo_url)
        mongo_db = mongo_client.code_interpreter
        self.mongo_db = mongo_db

        # Clean up
        _mongo_drop_all(self.mongo_db)
        _neo_drop_all(self.neo_db)

        # Create indexes
        self.mongo_db["class"].create_index("qualified_name", unique=True)
        self.mongo_db.function.create_index("qualified_name", unique=True)

    def run(self):
        # Instantiate
        self.interpreter = CodeInterpreter(self.folder_path)
        self.graph_composer = GraphComposer()

        # Interpretate codebase
        self.__interpret_code()
        logger.info("Interpretation done")

        # Compose graph
        self.__compose_graph()
        logger.info("Composition done")

        logger.info("Done")

    def __interpret_code(self):
        generator = self.interpreter.interpret()
        while True:
            try:
                node = next(generator)
                logger.info(node)
                node_type = node.get("type")
                self.mongo_db[node_type].insert_one(node)
            except StopIteration:
                break
            except DuplicateKeyError as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)
                break

    def __compose_graph(self):
        entities_collections = ["class", "function"]
        relationships_collections = ["calls_rel", "inherits_rel", "contains_rel"]

        for collection_name in entities_collections:
            self.graph_composer.entities.extend(self.mongo_db[collection_name].find())

        for collection_name in relationships_collections:
            self.graph_composer.relationships.extend(
                self.mongo_db[collection_name].find()
            )

        self.graph_composer.compose()


def _mongo_drop_all(mongo_db):
    for collection_name in mongo_db.list_collection_names():
        mongo_db.drop_collection(collection_name)


def _neo_drop_all(neo_db):
    clear_neo4j_database(neo_db, clear_constraints=True, clear_indexes=True)

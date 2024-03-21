from typing import Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from loguru import logger

from cskg.interpreter.interpreter import CodeInterpreter
from cskg.composer.composer import GraphComposer

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
                raise e

    def __compose_graph(self):
        classes = self.mongo_db["class_ent"].find()
        functions = self.mongo_db["function_ent"].find()
        methods = self.mongo_db["method_ent"].find()
        variables = self.mongo_db["variable_ent"].find()
        calls_rels = self.mongo_db["calls_rel"].find()
        inherits_rels = self.mongo_db["inherits_rel"].find()
        contains_rels = self.mongo_db["contains_rel"].find()
        takes_rels = self.mongo_db["takes_rel"].find()
        returns_rels = self.mongo_db["returns_rel"].find()
        yields_rels = self.mongo_db["yields_rel"].find()
        instantiates_rels = self.mongo_db["instantiates_rel"].find()

        self.graph_composer.add_entities(classes)
        self.graph_composer.add_entities(functions)
        self.graph_composer.add_entities(methods)
        self.graph_composer.add_entities(variables)
        self.graph_composer.add_relationships(calls_rels)
        self.graph_composer.add_relationships(inherits_rels)
        self.graph_composer.add_relationships(contains_rels)
        self.graph_composer.add_relationships(takes_rels)
        self.graph_composer.add_relationships(returns_rels)
        self.graph_composer.add_relationships(yields_rels)
        self.graph_composer.add_relationships(instantiates_rels)

        self.graph_composer.compose()


def _mongo_drop_all(mongo_db):
    for collection_name in mongo_db.list_collection_names():
        mongo_db.drop_collection(collection_name)


def _neo_drop_all(neo_db):
    clear_neo4j_database(neo_db, clear_constraints=True, clear_indexes=True)

import time
from typing import Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from loguru import logger

from interpreter.interpreter import CodeInterpreter
from composer.composer import GraphComposer
from composer.node_composers import EntityComposer, RelationshipComposer


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

        # Initialize logger file
        filename = time.strftime("%Y-%m-%d_%H-%M-%S")
        logger.add(f"logs/{filename}.log")

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
        class_composer = EntityComposer(
            "CLASS", included_fields=["qualified_name", "name", "file_path"]
        )
        function_composer = EntityComposer(
            "FUNCTION",
            included_fields=["name", "qualified_name", "file_path"],
        )
        calls_rel_composer = RelationshipComposer(
            "CALLS",
            from_field=("function_qualified_name", "function"),
            to_field=("callee_qualified_name", "function"),
        )
        inherits_rel_composer = RelationshipComposer(
            "INHERITS",
            from_field=("child_qualified_name", "class"),
            to_field=("parent_qualified_name", "class"),
        )
        contains_rel_composer = RelationshipComposer(
            "CONTAINS",
            from_field=("class_qualified_name", "class"),
            to_field=("function_qualified_name", "function"),
        )
        returns_rel_composer = RelationshipComposer(
            "RETURNS",
            from_field=("function_qualified_name", "function"),
            to_field=("class_qualified_name", "class"),
        )

        classes = self.mongo_db["class"].find()
        functions = self.mongo_db["function"].find()
        calls_rels = self.mongo_db["calls_rel"].find()
        inherits_rels = self.mongo_db["inherits_rel"].find()
        contains_rels = self.mongo_db["contains_rel"].find()
        returns_rels = self.mongo_db["returns_rel"].find()

        self.graph_composer.add_entities(classes, class_composer)
        self.graph_composer.add_entities(functions, function_composer)
        self.graph_composer.add_relationships(calls_rels, calls_rel_composer)
        self.graph_composer.add_relationships(inherits_rels, inherits_rel_composer)
        self.graph_composer.add_relationships(contains_rels, contains_rel_composer)
        self.graph_composer.add_relationships(returns_rels, returns_rel_composer)

        self.graph_composer.compose()


def _mongo_drop_all(mongo_db):
    for collection_name in mongo_db.list_collection_names():
        mongo_db.drop_collection(collection_name)


def _neo_drop_all(neo_db):
    clear_neo4j_database(neo_db, clear_constraints=True, clear_indexes=True)

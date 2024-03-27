from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from loguru import logger

from cskg.entity import *
from cskg.relationship import *
from cskg.interpreter.interpreter import CodeInterpreter
from cskg.composer.composer import GraphComposer


class Driver:
    def __init__(self, folder_path: str, neo4j_url: str, mongo_url: str):
        self.folder_path = folder_path
        self.neo4j_url = neo4j_url
        self.mongo_url = mongo_url
        self.interpreter = None
        self.graph_composer = None

        # Load neomodel configurations
        neomodel.config.DATABASE_URL = self.neo4j_url
        neomodel.config.AUTO_INSTALL_LABELS = True
        self.neo_db = neomodel.db
        self.neo_db.set_connection(self.neo4j_url)

        # Instantiate mongo db client
        mongo_client = MongoClient(self.mongo_url)
        mongo_db = mongo_client.code_interpreter
        self.mongo_client = mongo_client
        self.mongo_db = mongo_db

        # Clean up
        _mongo_drop_all(self.mongo_db)
        _neo_drop_all(self.neo_db)

        # Create indexes (for only Entity classes)
        for entity_class in Entity.visit_subclasses():
            self.mongo_db[entity_class.type].create_index("qualified_name", unique=True)

    def run(self):
        # Instantiate
        self.interpreter = CodeInterpreter(self.folder_path)
        self.graph_composer = GraphComposer()

        # Interpretate codebase
        self.interpret_code()
        logger.info("Interpretation done")

        # Compose graph
        self.compose_graph()
        logger.info("Composition done")

        logger.info("Done")

    def interpret_code(self):
        generator = self.interpreter.interpret()

        with self.mongo_client.start_session() as session:
            while True:
                try:
                    obj = next(generator)
                    self.mongo_db[obj.type].insert_one(obj, session=session)
                    logger.info(obj)
                except StopIteration:
                    break
                except DuplicateKeyError as e:
                    logger.error(e)
                except Exception as e:
                    raise e

    def compose_graph(self):
        # All entities
        for entity_class in Entity.visit_subclasses():
            entities = self.mongo_db[entity_class.type].find()
            self.graph_composer.add_entities(entities)

        # All relationships
        for relationship_class in Relationship.visit_subclasses():
            relationships = self.mongo_db[relationship_class.type].find()
            self.graph_composer.add_relationships(relationships)

        self.graph_composer.compose()


def _mongo_drop_all(mongo_db):
    for collection_name in mongo_db.list_collection_names():
        mongo_db.drop_collection(collection_name)


def _neo_drop_all(neo_db):
    clear_neo4j_database(neo_db, clear_constraints=True, clear_indexes=True)

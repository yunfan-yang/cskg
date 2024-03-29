from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from os.path import abspath
from loguru import logger

from cskg.utils.graph_component import GraphComponent
from cskg.utils.entity import *
from cskg.utils.relationship import *
from cskg.interpreter.interpreter import CodeInterpreter
from cskg.composer.composer import GraphComposer
from cskg.detectors.detector import AbstractDetector


class Driver:
    def __init__(self, folder_path: str, neo4j_url: str, mongo_url: str):
        self.folder_path = folder_path
        self.folder_abs_path = abspath(folder_path)
        self.neo4j_url = neo4j_url
        self.mongo_url = mongo_url

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

    def run(self):
        # Interpretate codebase
        self.interpret_code()
        logger.info("Interpretation done")

        # Compose graph
        self.compose_graph()
        logger.info("Composition done")

        # Detect smells
        self.detect_smells()
        logger.info("Smell detection done")

        logger.info("Done")

    def interpret_code(self):
        # Drop everything in mongo
        for collection_name in self.mongo_db.list_collection_names():
            self.mongo_db.drop_collection(collection_name)

        # Create collections
        for component_class in GraphComponent.visit_subclasses():
            if component_class.type:
                # Create collection
                collection = self.mongo_db.create_collection(
                    component_class.type,
                    check_exists=False,
                )

                # Create index for entity classes
                if isinstance(component_class, Entity):
                    collection.create_index("qualified_name", unique=True)

        # Instantiate code interpreter
        interpreter = CodeInterpreter(self.folder_path)

        # Insert components into mongo
        with self.mongo_client.start_session() as session:
            for component in interpreter.visit():
                try:
                    colection = self.mongo_db.get_collection(component.type)
                    colection.insert_one(component, session=session)
                    logger.info(component)
                except DuplicateKeyError as e:
                    logger.warning(e)  # Ignore duplicate key error
                except Exception as e:
                    raise e

    def compose_graph(self):
        # Drop everything in neo4j
        clear_neo4j_database(self.neo_db, clear_constraints=True, clear_indexes=True)

        # Instantiate graph composer
        graph_composer = GraphComposer()

        # Add all entities to composer
        for entity_class in Entity.visit_subclasses():
            collection = self.mongo_db.get_collection(entity_class.type)
            entities = collection.find()
            graph_composer.add_entities(entities)

        # Add all relationships to composer
        for relationship_class in Relationship.visit_subclasses():
            collection = self.mongo_db.get_collection(relationship_class.type)
            relationships = collection.find()
            graph_composer.add_relationships(relationships)

        # Compose graph
        graph_composer.compose()

    def detect_smells(self):
        for detector_class in AbstractDetector.visit_subclasses():
            detector = detector_class.create_instance(self.neo_db)
            detector.detect()

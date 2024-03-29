from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from neo4j.exceptions import ClientError
from os.path import abspath
from loguru import logger
from tqdm import tqdm

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

    def run(self, interpret=True, compose=True, detect=True):
        # Interpretate codebase
        if interpret:
            logger.info("Interpreting code")
            self.interpret_code()
            logger.info("Interpretation done")

        # Compose graph
        if compose:
            logger.info("Composing graph")
            self.compose_graph()
            logger.info("Composition done")

        # Detect smells
        if detect:
            logger.info("Detecting smells")
            self.detect_smells()
            logger.info("Detection done")

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
                if issubclass(component_class, Entity):
                    collection.create_index("qualified_name", unique=True)

        # Instantiate code interpreter
        interpreter = CodeInterpreter(self.folder_path)

        # Insert components into mongo
        with self.mongo_client.start_session() as session:
            for component in interpreter.visit():
                try:
                    colection = self.mongo_db.get_collection(component.type)
                    colection.insert_one(component, session=session)
                    logger.debug(component)
                except DuplicateKeyError as e:
                    logger.warning(e)  # Ignore duplicate key error

    def compose_graph(self):
        # Drop everything in neo4j
        clear_neo4j_database(self.neo_db, clear_constraints=True, clear_indexes=True)

        # Create indexes for entities
        for entity_class in Entity.visit_subclasses():
            entity_type = entity_class.type
            entity_label = entity_class.label
            index_cypher = f"""
                CREATE INDEX {entity_type}_qualified_name FOR (n:{entity_label}) ON (n.qualified_name)
            """
            logger.debug(index_cypher)
            constraint_cypher = f"""
                CREATE CONSTRAINT {entity_type}_qualified_name_constraint ON (n:{entity_label}) ASSERT n.qualified_name IS UNIQUE
            """
            logger.debug(constraint_cypher)

            try:
                self.neo_db.cypher_query(index_cypher)
                self.neo_db.cypher_query(constraint_cypher)
            except ClientError:
                ...

        # Instantiate graph composer
        graph_composer = GraphComposer()

        total_components = 0

        # Add all entities to composer
        for entity_class in Entity.visit_subclasses():
            collection = self.mongo_db.get_collection(entity_class.type)

            entity_count = collection.count_documents({})
            total_components += entity_count

            entity_collection_iter = collection.find()
            graph_composer.add_entity_collections(entity_collection_iter)

        # Add all relationships to composer
        for relationship_class in Relationship.visit_subclasses():
            collection = self.mongo_db.get_collection(relationship_class.type)

            relationship_count = collection.count_documents({})
            total_components += relationship_count

            relationship_collection_iter = collection.find()
            graph_composer.add_relationship_collection(relationship_collection_iter)

        # Compose graph
        bar = tqdm(total=total_components, desc="Composing graph", unit="components")
        batch_size = 10000
        query_count = 0

        with self.neo_db.transaction:
            for cypher, params in graph_composer.visit():
                logger.debug(f"{cypher}\n{params}")
                self.neo_db.cypher_query(cypher, params)
                query_count += 1
                bar.update(1)

                if query_count % batch_size == 0:
                    self.neo_db.commit()
                    self.neo_db.begin()
        bar.close()

    def detect_smells(self):
        for detector_class in AbstractDetector.visit_subclasses():
            detector = detector_class.create_instance(self.neo_db)
            detector.detect()

    def __del__(self):
        self.mongo_client.close()
        self.neo_db.close_connection()
        logger.info("Connections closed")

from pymongo import MongoClient
import neomodel
from os.path import abspath
from loguru import logger

from cskg.interpreter.interpreter import CodeInterpreter
from cskg.composer.composer import GraphComposer
from cskg.detectors.detector import AbstractDetector


class Driver:
    def __init__(self, folder_path: str, neo4j_url: str, mongo_url: str):
        self.folder_path = folder_path
        self.folder_abs_path = abspath(folder_path)
        self.neo4j_url = neo4j_url
        self.is_neo4j_connected = False
        self.mongo_url = mongo_url
        self.is_mongo_connected = False

        # Connect to neo4j
        try:
            neomodel.config.DATABASE_URL = self.neo4j_url
            neomodel.config.AUTO_INSTALL_LABELS = True
            self.neo_db = neomodel.db
            self.neo_db.set_connection(self.neo4j_url)
            self.neo_db.cypher_query("RETURN datetime() AS datetime")
            self.is_neo4j_connected = True
            logger.info(f"Connected to neo4j database at {self.neo_db.url}")
            logger.info(f"Database edition: {self.neo_db.database_edition}")
            logger.info(f"Database version: {self.neo_db.database_version}")
        except:
            self.is_neo4j_connected = False
            logger.info(f"Failed to connect to neo4j database at {self.neo_db.url}")

        # Connect to mongo
        try:
            self.mongo_client = MongoClient(self.mongo_url)
            self.code_interpreter_db = self.mongo_client.get_database(
                "code_interpreter"
            )
            self.code_smells_db = self.mongo_client.get_database("code_smells")

            host_port = f"{self.mongo_client.HOST}:{self.mongo_client.PORT}"
            version = self.mongo_client.server_info()["version"]

            self.code_interpreter_db.command("dbstats")
            self.is_mongo_connected = True

            logger.info(f"Connected to mongo database at {host_port}")
            logger.info(f"MongoDB version: {version}")
        except:
            logger.info(f"Failed to connect to mongo database at {host_port}")
            self.is_mongo_connected = False

    def run(self, interpret=True, compose=True, detect=True):
        if not self.is_neo4j_connected and not self.is_mongo_connected:
            return

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
        interpreter = CodeInterpreter(self.folder_path, self.code_interpreter_db)
        interpreter.interpret()

    def compose_graph(self):
        graph_composer = GraphComposer(self.code_interpreter_db, self.neo_db)
        graph_composer.compose()

    def detect_smells(self):
        for detector_class in AbstractDetector.visit_subclasses():
            detector = detector_class.create_instance(self.code_smells_db, self.neo_db)
            detector.detect()

    def __del__(self):
        self.mongo_client.close()
        self.neo_db.close_connection()
        logger.info("Connections closed")

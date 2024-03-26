from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import neomodel
from neomodel import clear_neo4j_database
from bson.regex import Regex
from loguru import logger

from cskg.entity import ClassEntity
from cskg.interpreter.interpreter import CodeInterpreter
from cskg.composer.composer import GraphComposer


class Driver:
    def __init__(self, folder_path: str, neo4j_url: str, mongo_url: str):
        self.folder_path = folder_path
        self.neo4j_url = neo4j_url
        self.mongo_url = mongo_url
        self.interpreter = None
        self.graph_composer = None
        self.__init_database()

    def __init_database(self):
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

    def __populate_external_entities(self):
        with self.mongo_client.start_session() as session:
            takes_rels = self.mongo_db.takes_rel
            class_ents = self.mongo_db["class_ent"]
            module_prefix = self.interpreter.get_module_prefix()
            regex_expr = Regex(f"^(?!{module_prefix}\.)")

            pipeline = [
                {
                    "$match": {
                        "to_type": ClassEntity.type,
                        "to_qualified_name": regex_expr,
                    }
                },
                {
                    "$group": {
                        "_id": "$to_qualified_name",
                        "qualified_name": {"$first": "$to_qualified_name"},
                    }
                },
                {
                    "$project": ClassEntity(
                        _id=False,
                        name="$qualified_name",
                        qualified_name="$qualified_name",
                        file_path="<external>",
                        is_external_entity={"$literal": True},
                    )
                },
            ]

            external_classes = takes_rels.aggregate(pipeline, session=session)
            class_ents.insert_many(external_classes, session=session)

    def run(self):
        # Instantiate
        self.interpreter = CodeInterpreter(self.folder_path)
        self.graph_composer = GraphComposer()

        # Interpretate codebase
        self.__interpret_code()
        self.__populate_external_entities()
        logger.info("Interpretation done")

        # Compose graph
        self.__compose_graph()
        logger.info("Composition done")

        logger.info("Done")

    def __interpret_code(self):
        generator = self.interpreter.interpret()

        with self.mongo_client.start_session() as session:
            while True:
                try:
                    node = next(generator)
                    logger.info(node)
                    node_type = node.get("type")
                    self.mongo_db[node_type].insert_one(node, session=session)
                except StopIteration:
                    break
                except DuplicateKeyError as e:
                    logger.error(e)
                except Exception as e:
                    raise e

    def __compose_graph(self):
        modules = self.mongo_db["module_ent"].find()
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

        self.graph_composer.add_entities(modules)
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

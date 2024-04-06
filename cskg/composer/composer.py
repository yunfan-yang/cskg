import json
from typing import Any, Iterable
from pymongo.database import Database as MongoDatabase
from loguru import logger
from neo4j.exceptions import ClientError
from neomodel import clear_neo4j_database
from neomodel.util import Database as NeoDatabase
from tqdm import tqdm

from cskg.utils.entity import Entity
from cskg.utils.relationship import Relationship


class GraphComposer:

    def __init__(self, mongo_db: MongoDatabase, neo_db: NeoDatabase):
        self.mongo_db = mongo_db
        self.neo_db = neo_db

        # Drop everything in neo4j
        clear_neo4j_database(self.neo_db, clear_constraints=True, clear_indexes=True)

        self.create_indexes()
        self.count_total_components()

    def create_indexes(self):
        # Create indexes for entities
        for entity_class in Entity.visit_subclasses():
            entity_type = entity_class.type
            entity_label = entity_class.label
            index_cypher = f"""
                CREATE INDEX {entity_type}_qualified_name FOR (n:{entity_label}) ON (n.qualified_name)
            """
            logger.debug(index_cypher)

            try:
                self.neo_db.cypher_query(index_cypher)
            except ClientError as e:
                logger.error(e)
                ...

    def count_total_components(self):
        total_components = 0

        for entity_class in Entity.visit_subclasses():
            collection = self.mongo_db.get_collection(entity_class.type)
            total_components += collection.count_documents({})

        for relationship_class in Relationship.visit_subclasses():
            collection = self.mongo_db.get_collection(relationship_class.type)
            total_components += collection.count_documents({})

        return total_components

    def compose(self):
        # Compose graph
        total_components = self.count_total_components()
        bar = tqdm(total=total_components, desc="Composing graph", unit="components")
        with self.neo_db.transaction:
            for cypher, params, bulk_size in self.visit():
                self.neo_db.cypher_query(cypher, params)
                self.neo_db.commit()
                bar.update(bulk_size)
                bar.write(f"Batch committed ({bar.n}/{bar.total})")

                self.neo_db.begin()
        bar.close()

    def visit(self):
        yield from self.visit_entities()
        yield from self.visit_relationships()

    def visit_entities(self):
        for entity_class in Entity.visit_subclasses():
            # Get entity collection
            entity_label = entity_class.label
            collection = self.mongo_db.get_collection(entity_class.type)
            entity_collection = collection.find(
                {},
                {"_id": False, "label": False, "extra_labels": False},
            )

            # Bulk insert entities
            for entity_bulk in bulk(entity_collection, 10000):
                logger.debug(type(entity_bulk))
                query = f"""
                    UNWIND $entities AS entity
                    CREATE (n:{entity_label})
                    SET n = entity
                """
                yield query, {"entities": entity_bulk}, len(entity_bulk)

    def visit_relationships(self):
        for relationship_class in Relationship.visit_subclasses():
            relationship_type = relationship_class.type
            relationship_label = relationship_class.label

            # Get relationship collection
            collection = self.mongo_db.get_collection(relationship_type)

            # Retrieve relationships by group
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "from_type": "$from_type",
                            "to_type": "$to_type",
                        },
                    },
                },
            ]
            groups = collection.aggregate(pipeline)

            for group in groups:
                _id = group["_id"]
                from_type, to_type = _id["from_type"], _id["to_type"]

                from_type_class = Entity.get_class(from_type)
                to_type_class = Entity.get_class(to_type)
                from_label = from_type_class.label
                to_label = to_type_class.label

                logger.debug(f"{relationship_type} {from_type} {to_type}")

                # Get relationship collection
                relationships = collection.find(
                    {
                        "from_type": from_type,
                        "to_type": to_type,
                    },
                    {"_id": False},
                )

                # Bulk insert relationships
                for relationship in bulk(relationships, 5000):
                    cypher = f"""
                        UNWIND $relationships AS relationship
                        MATCH (a:{from_label} {{qualified_name: relationship.from_qualified_name}}), (b:{to_label} {{qualified_name: relationship.to_qualified_name}})
                        CREATE (a)-[t:{relationship_label}]->(b)
                        SET t = relationship
                    """
                    yield cypher, {"relationships": relationship}, len(relationship)


def bulk(iter: Iterable, size: int):
    it = iter.__iter__()
    while True:
        batch = []
        try:
            for _ in range(size):
                batch.append(next(it))
        except StopIteration:
            if batch:
                yield batch
            break
        yield batch

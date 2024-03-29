from itertools import chain, islice
import json
from typing import Any, Iterable, TypeVar
from loguru import logger
from neomodel import db

from cskg.utils.entity import Entity
from cskg.utils.relationship import Relationship


CHUNK_SIZE = 1000


class GraphComposer:
    def __init__(self):
        self.entity_collections: list[Iterable[dict[str, Any]]] = []
        self.relationship_collections: list[Iterable[dict[str, Any]]] = []

    def add_entity_collections(self, entities: Iterable[dict[str, Any]]):
        self.entity_collections.append(entities)

    def add_relationship_collection(self, relationships: Iterable[dict[str, Any]]):
        self.relationship_collections.append(relationships)

    def visit(self):
        yield from self.visit_entities()
        yield from self.visit_relationships()

    def visit_entities(self):
        for entities in self.entity_collections:
            for entity in entities:
                cypher = self.get_entity_cypher(Entity.from_dict(entity))
                yield cypher

    def visit_relationships(self):
        for relationships in self.relationship_collections:
            for relationship in relationships:
                cypher = self.get_relationship_cypher(
                    Relationship.from_dict(relationship)
                )
                yield cypher

    def get_entity_cypher(self, entity: Entity):
        entity_type = "".join(map(lambda label: f":{label}", entity.labels))
        entity_properties = _get_dictionary_cypher(entity)

        return f"""
            CREATE ({entity_type} {{ {entity_properties} }}) 
        """

    def get_relationship_cypher(self, relationship: Relationship):
        relation_type = relationship.label

        from_ent_label = relationship.from_type.label
        from_ent_qname = relationship.from_qualified_name
        to_ent_label = relationship.to_type.label
        to_ent_qname = relationship.to_qualified_name

        relationship_properties = _get_dictionary_cypher(relationship)

        return f"""
            MATCH (a:{from_ent_label} {{qualified_name: "{from_ent_qname}"}}), (b:{to_ent_label} {{qualified_name: "{to_ent_qname}"}})
            CREATE (a)-[:{relation_type} {{ {relationship_properties} }}]->(b)
        """


T = TypeVar("T")


def _chunk(iterable: Iterable[T], size: int) -> Iterable[T]:
    """
    Splits an iterable into chunk of a specified size.

    :param iterable: An iterable like a list or a generator.
    :param batch_size: The size of each batch.
    :return: Yields batches of the iterable.
    """
    iterator = iter(iterable)
    for first in iterator:
        yield chain([first], islice(iterator, size - 1))


def _get_dictionary_cypher(dictionary: dict[str, Any]) -> str:
    dictionary = _exclude_fields_dict(dictionary, ["_id", "label", "extra_labels"])

    keypairs = []
    for key, value in dictionary.items():
        if isinstance(value, str):
            keypairs.append(f"{key}: '{value}'")
        elif value is None:
            keypairs.append(f"{key}: NULL")
        elif isinstance(value, (list, tuple, set)):
            keypairs.append(key + ": " + json.dumps(list(value)).replace("'", ""))
        elif isinstance(value, dict):
            keypairs.append(key + ": " + json.dumps(value).replace("'", ""))
        elif isinstance(value, bool):
            keypairs.append(f"{key}: {str(value).lower()}")
        else:
            keypairs.append(f"{key}: {value}")
    return ", ".join(keypairs)


def _exclude_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in dict if key not in fields}

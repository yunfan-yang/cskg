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
        self.entities: list[Iterable[dict[str, Any]]] = []
        self.relationships: list[Iterable[dict[str, Any]]] = []

    def add_entities(self, entities: Iterable[dict[str, Any]]):
        self.entities.append(entities)

    def add_relationships(self, relationships: Iterable[dict[str, Any]]):
        self.relationships.append(relationships)

    def compose_entities(self):
        for entities_iterable in self.entities:
            for chunk in _chunk(entities_iterable, CHUNK_SIZE):
                with db.transaction:
                    for entity in chunk:
                        cypher = self.compose_entity_cypher(Entity.from_json(entity))
                        logger.debug(f"cypher: {cypher}")
                        db.cypher_query(cypher)

    def compose_entity_cypher(self, entity: Entity):
        entity_type = "".join(map(lambda label: f":{label}", entity.labels))
        entity_properties = _get_dictionary_cypher(entity, entity.__final_fields__)

        return f"""
            CREATE ({entity_type} {{ {entity_properties} }}) 
        """

    def compose_relationships(self):
        for relationships_iterable in self.relationships:
            for chunk in _chunk(relationships_iterable, CHUNK_SIZE):
                with db.transaction:
                    for relationship in chunk:
                        cypher = self.compose_relationship_cypher(
                            Relationship.from_json(relationship)
                        )
                        db.cypher_query(cypher)
                        logger.debug(f"cypher: {cypher}")

    def compose_relationship_cypher(self, relationship: Relationship):
        relation_type = f":{relationship.label}"

        field_a_label = relationship.from_type.label
        field_b_label = relationship.to_type.label
        field_a_value = relationship.from_qualified_name
        field_b_value = relationship.to_qualified_name

        relationship_properties = _get_dictionary_cypher(
            relationship, relationship.__final_fields__
        )

        return f"""
            MATCH (a:{field_a_label} {{qualified_name: "{field_a_value}"}}), (b:{field_b_label} {{qualified_name: "{field_b_value}"}})
            CREATE (a)-[{relation_type} {{ {relationship_properties} }}]->(b)
        """

    def compose(self):
        self.compose_entities()
        self.compose_relationships()


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


def _get_dictionary_cypher(
    dictionary: dict[str, Any], excluded_fields: list[str] = None
) -> str:
    excluded_fields += ["_id"]
    dictionary = _exclude_fields_dict(dictionary, excluded_fields)

    keypairs = []
    for key, value in dictionary.items():
        if isinstance(value, str):
            keypairs.append(f"{key}: '{value}'")
        elif value is None:
            keypairs.append(f"{key}: NULL")
        elif isinstance(value, (list, dict)):
            return key + ": " + json.dumps(value).replace("'", "")
        else:
            keypairs.append(f"{key}: {value}")
    return ", ".join(keypairs)


def _exclude_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in dict if key not in fields}

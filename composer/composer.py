from itertools import chain, islice
from typing import Any, Iterable, TypeVar
from loguru import logger
from neomodel import db

from composer.node_composers import (
    EntityComposer,
    RelationshipComposer,
)

CHUNK_SIZE = 1000


class GraphComposer:
    def __init__(self):
        self.entities: list[tuple[Iterable[dict[str, Any]], EntityComposer]] = []
        self.relationships: list[
            tuple[Iterable[dict[str, Any]], RelationshipComposer]
        ] = []

    def add_entities(
        self, entities: Iterable[dict[str, Any]], composer: EntityComposer
    ):
        self.entities.append((entities, composer))

    def add_relationships(
        self, relationships: Iterable[dict[str, Any]], composer: RelationshipComposer
    ):
        self.relationships.append((relationships, composer))

    def compose_entities(self):
        for entities, entity_composer in self.entities:
            for chunk in _chunk(entities, CHUNK_SIZE):
                with db.transaction:
                    for entity in chunk:
                        cypher = entity_composer.get_cypher(entity)
                        db.cypher_query(cypher)
                logger.info(f"Composed {entity_composer.entity_type}")

    def compose_relationships(self):
        for relationships, relationship_composer in self.relationships:
            for chunk in _chunk(relationships, CHUNK_SIZE):
                with db.transaction:
                    for relationship in chunk:
                        cypher = relationship_composer.get_cypher(relationship)
                        db.cypher_query(cypher)
                logger.info(f"Composed {relationship_composer.relation_type}")

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

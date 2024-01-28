from typing import Any, Iterable
from composer.models import *
from loguru import logger
from neomodel import DoesNotExist, db

from composer.node_composers import (
    NodeComposer,
    EntityComposer,
    RelationshipComposer,
)

CHUNK_SIZE = 1000


class GraphComposer:
    def __init__(self):
        self.entities: list[tuple[Iterable, EntityComposer]] = {}
        self.relationships: list[tuple[Iterable, RelationshipComposer]] = {}

    def add_entities(self, entities: Iterable, composer: EntityComposer):
        self.entities.append((entities, composer))

    def add_relationships(
        self, relationships: Iterable, composer: RelationshipComposer
    ):
        self.relationships.append((relationships, composer))

    def compose_entities(self):
        for entities, entity_composer in self.entities:
            for chunk in _chunk(entities, CHUNK_SIZE):
                with db.transaction:
                    cyphers = map(entity_composer.get_cypher, chunk)
                    cypher = "\n".join(cyphers)
                    logger.debug(cypher)
                    db.cypher_query(cypher)

    def compose_relationships(self):
        for relationships, relationship_composer in self.relationships:
            for chunk in _chunk(relationships, CHUNK_SIZE):
                with db.transaction:
                    cyphers = map(relationship_composer.get_cypher, chunk)
                    cypher = "\n".join(cyphers)
                    logger.debug(cypher)
                    db.cypher_query(cypher)

    def compose(self):
        self.compose_entities()
        self.compose_relationships()


def _chunk(iterable: Iterable, size: int):
    """
    Splits an iterable into chunk of a specified size.

    :param iterable: An iterable like a list or a generator.
    :param batch_size: The size of each batch.
    :return: Yields batches of the iterable.
    """
    l = len(iterable)
    for ndx in range(0, l, size):
        yield iterable[ndx : min(ndx + size, l)]

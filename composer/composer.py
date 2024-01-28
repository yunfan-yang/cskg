from itertools import chain, islice
from typing import Iterable
from composer.models import *
from loguru import logger
from neomodel import db

from composer.node_composers import (
    EntityComposer,
    RelationshipComposer,
)

CHUNK_SIZE = 1000


class GraphComposer:
    def __init__(self):
        self.entities: list[tuple[Iterable, EntityComposer]] = []
        self.relationships: list[tuple[Iterable, RelationshipComposer]] = []

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
                    for cypher in cyphers:
                        db.cypher_query(cypher)

                logger.info(f"Composed {len(cyphers)} {entity_composer.entity_type}")

    def compose_relationships(self):
        for relationships, relationship_composer in self.relationships:
            for chunk in _chunk(relationships, CHUNK_SIZE):
                with db.transaction:
                    cyphers = map(relationship_composer.get_cypher, chunk)
                    for cypher in cyphers:
                        db.cypher_query(cypher)
                logger.info(
                    f"Composed {len(cyphers)} {relationship_composer.relation_type}"
                )

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

    # Iterable is always unsized
    # https://stackoverflow.com/questions/39381401/python-type-hinting-for-iterable-but-not-list

    iterator = iter(iterable)
    for first in iterator:
        yield chain([first], islice(iterator, size - 1))

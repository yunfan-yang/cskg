from abc import ABC, abstractmethod
from loguru import logger
from neo4j.graph import Node
from neomodel import Database as NeoDatabase

from cskg.utils.entity import Entity
from cskg.utils.mixins import VisitSubclassesMixin, CreateInstanceMixin


class AbstractDetector(ABC, VisitSubclassesMixin, CreateInstanceMixin):
    def __init__(self, neo_db: NeoDatabase):
        self.neo_db = neo_db

    @abstractmethod
    def detect(self): ...

    def response_to_ent(self, nodes: list[Node]):
        ents = []
        for node in nodes:
            ent = Entity.from_dict(dict(node))
            ents.append(ent)
        return ents

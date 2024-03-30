from abc import ABC, abstractmethod
from loguru import logger
from neo4j.graph import Node
from neomodel import Database as NeoDatabase

from cskg.utils.graph_component import GraphComponent
from cskg.utils.mixins import VisitSubclassesMixin, CreateInstanceMixin


class AbstractDetector(ABC, VisitSubclassesMixin, CreateInstanceMixin):
    def __init__(self, neo_db: NeoDatabase):
        self.neo_db = neo_db

    @abstractmethod
    def detect(self): ...

    def result_to_ent(self, nodes: list[Node]):
        components = []
        for node in nodes:
            ent = GraphComponent.from_dict(dict(node))
            components.append(ent)
        return components

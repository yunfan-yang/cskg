from abc import ABC, abstractmethod
from neomodel import Database as NeoDatabase

from cskg.mixins import VisitSubclassesMixin, CreateInstanceMixin


class AbstractDetector(ABC, VisitSubclassesMixin, CreateInstanceMixin):
    def __init__(self, neo_db: NeoDatabase):
        self.neo_db = neo_db

    @abstractmethod
    def detect(self): ...

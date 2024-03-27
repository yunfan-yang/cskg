from abc import ABC, ABCMeta

from cskg.utils.mixins import VisitSubclassesMixin


class GraphComponentMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")


class GraphComponent(dict, ABC, VisitSubclassesMixin, metaclass=GraphComponentMeta):
    type = "graph_component"
    label = "GraphComponent"

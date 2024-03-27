from abc import ABC, ABCMeta

from cskg.utils.mixins import VisitSubclassesMixin


class GraphComponentMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        if not hasattr(cls, "type"):
            raise AttributeError(f"Class {name} lacks required `type` class attribute")
        elif not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required `label` class attribute")


class GraphComponent(dict, ABC, VisitSubclassesMixin, metaclass=GraphComponentMeta):
    type = "graph_component"
    label = "GraphComponent"

    @classmethod
    def get_class(cls, type: str):
        for subclass in cls.visit_subclasses():
            if subclass.type == type:
                return subclass

        raise ValueError(f'Could not find class for type "{type}"')

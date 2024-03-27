from abc import ABC, ABCMeta

from loguru import logger

from cskg.utils.mixins import VisitSubclassesMixin, CreateInstanceMixin


class GraphComponentMeta(ABCMeta):
    def __init__(cls, name, bases, props):
        super().__init__(name, bases, props)

        if ABC in bases:
            return

        if not hasattr(cls, "type") or not getattr(cls, "type"):
            raise AttributeError(f"Class `{name}` lacks `type` class attribute")
        elif not hasattr(cls, "label") or not getattr(cls, "label"):
            raise AttributeError(f"Class `{name}` lacks `label` class attribute")


class GraphComponent(
    dict, ABC, VisitSubclassesMixin, CreateInstanceMixin, metaclass=GraphComponentMeta
):
    @classmethod
    def get_class(cls, type: str):
        for subclass in cls.visit_subclasses():
            if subclass.type == type:
                return subclass

        raise ValueError(f'Could not find class for type "{type}"')

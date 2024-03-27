from abc import ABC, ABCMeta

from cskg.utils.mixins import VisitSubclassesMixin


class GraphComponentMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")


class GraphComponent(dict, ABC, VisitSubclassesMixin, meta=GraphComponentMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(**args, **kwargs)

    def __init_subclass__(cls, *args, **kargs):
        super().__init_subclass__(**args, **kargs)

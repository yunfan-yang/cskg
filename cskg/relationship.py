from typing import Any, Type
from abc import ABC, ABCMeta

from cskg.entity import Entity


class RelationshipMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")
        super().__init__(name, bases, dct)


class Relationship(dict, ABC, metaclass=RelationshipMeta):
    __final_fields__ = ["type", "label"]
    type = "relationship"
    label = "Relationship"

    def __init__(
        self,
        from_type: Type[Entity],
        from_qualified_name: str,
        to_type: Type[Entity],
        to_qualified_name: str,
        **kwargs,
    ):
        super().__init__(
            type=self.type,
            label=self.label,
            from_type=from_type.label,
            from_qualified_name=from_qualified_name,
            to_type=to_type.label,
            to_qualified_name=to_qualified_name,
            **kwargs,
        )

    def __setitem__(self, key, value):
        if key in self.__final_fields__:
            raise ValueError("Cannot set type")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key in self.__final_fields__:
            return self.get(key)
        return super().__getitem__(key)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getitem__(__name)
        except KeyError:
            return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Cannot set {__name}")
        super().__setitem__(__name, __value)


class CallsRel(Relationship):
    type = "calls_rel"
    label = "CALLS"


class InheritsRel(Relationship):
    type = "inherits_rel"
    label = "INHERITS"


class ContainsRel(Relationship):
    type = "contains_rel"
    label = "CONTAINS"


class TakesRel(Relationship):
    type = "takes_rel"
    label = "TAKES"


class ReturnsRel(Relationship):
    type = "returns_rel"
    label = "RETURNS"


class YieldRel(Relationship):
    type = "yield_rel"
    label = "YIELDS"


class InstantiatesRel(Relationship):
    type = "instantiates_rel"
    label = "INSTANTIATES"

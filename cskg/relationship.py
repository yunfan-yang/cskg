from typing import Any, Self, Type
from abc import ABC, ABCMeta

from cskg.entity import Entity


class RelationshipMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")
        super().__init__(name, bases, dct)


class Relationship(dict, ABC, metaclass=RelationshipMeta):
    __final_fields__ = ["type", "label"]
    __required_fields__ = [
        "from_label",
        "from_qualified_name",
        "to_label",
        "to_qualified_name",
    ]

    type: str = "relationship"
    label: str = "Relationship"

    def __init__(
        self,
        from_label: Type[Entity],
        from_qualified_name: str,
        to_label: Type[Entity],
        to_qualified_name: str,
        **kwargs,
    ):
        super().__init__(
            type=self.type,
            label=self.label,
            from_label=from_label.label,
            from_qualified_name=from_qualified_name,
            to_label=to_label.label,
            to_qualified_name=to_qualified_name,
            **kwargs,
        )

    def __setitem__(self, key, value):
        if key in self.__final_fields__:
            raise ValueError(f"Not allowed to set attribute {key}")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getitem__(__name)
        except KeyError:
            return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Not allowed to set attribute {__name}")
        super().__setitem__(__name, __value)

    def __internal_set(self, key, value):
        super().__setitem__(key, value)

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Self:
        excluded_final_fields_json = {
            key: value
            for key, value in json.items()
            if (key not in cls.__final_fields__ and key not in cls.__required_fields__)
        }

        from_label_cls = Entity.get_class(json["from_label"])
        to_label_cls = Entity.get_class(json["to_label"])

        instance = cls(
            from_label=from_label_cls,
            from_qualified_name=json["from_qualified_name"],
            to_label=to_label_cls,
            to_qualified_name=json["to_qualified_name"],
            **excluded_final_fields_json,
        )
        instance.__internal_set("type", json["type"])
        instance.__internal_set("label", json["label"])
        return instance


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

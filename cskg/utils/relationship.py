from abc import ABC
from typing import Any, Self, Type

from cskg.utils.entity import Entity
from cskg.utils.graph_component import GraphComponent


class Relationship(GraphComponent, ABC):
    __final_fields__ = ["type", "label"]
    __required_fields__ = [
        "from_type",
        "from_qualified_name",
        "to_type",
        "to_qualified_name",
    ]

    type: str = "relationship"
    label: str = "Relationship"

    def __init__(
        self,
        from_type: Type[Entity],
        from_qualified_name: str,
        to_type: Type[Entity],
        to_qualified_name: str,
        **kwargs,
    ):
        self.from_type = from_type
        self.to_type = to_type

        super().__init__(
            type=self.type,
            label=self.label,
            from_type=from_type.type,
            from_qualified_name=from_qualified_name,
            to_type=to_type.type,
            to_qualified_name=to_qualified_name,
            **kwargs,
        )

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            return super().__getitem__(__name)
        except KeyError:
            raise AttributeError(f"Field {__name} not found")

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Not allowed to set attribute {__name}")

        super().__setattr__(__name, __value)

        if __name in ["from_type", "to_type"]:
            super().__setitem__(__name, __value.type)
        else:
            super().__setitem__(__name, __value)

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Self:
        excluded_final_fields_json = {
            key: value
            for key, value in json.items()
            if (key not in cls.__final_fields__ and key not in cls.__required_fields__)
        }

        from_type = Entity.get_class(json["from_type"])
        to_type = Entity.get_class(json["to_type"])
        relationship_cls = Relationship.get_class(json["type"])

        instance = relationship_cls.create_instance(
            from_type=from_type,
            from_qualified_name=json["from_qualified_name"],
            to_type=to_type,
            to_qualified_name=json["to_qualified_name"],
            **excluded_final_fields_json,
        )
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


class YieldsRel(Relationship):
    type = "yields_rel"
    label = "YIELDS"


class InstantiatesRel(Relationship):
    type = "instantiates_rel"
    label = "INSTANTIATES"

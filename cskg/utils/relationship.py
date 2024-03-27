from abc import ABC
from typing import Any, Self, Type

from loguru import logger

from cskg.utils.entity import Entity, ModuleEntity
from cskg.utils.graph_component import GraphComponent


class Relationship(GraphComponent, ABC):
    __final_fields__ = ["type", "label"]
    __required_fields__ = [
        "from_type",
        "from_qualified_name",
        "to_type",
        "to_qualified_name",
    ]

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
            from_type=from_type,
            from_qualified_name=from_qualified_name,
            to_type=to_type,
            to_qualified_name=to_qualified_name,
            **kwargs,
        )

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

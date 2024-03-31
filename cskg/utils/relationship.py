from abc import ABC
from typing import Type

from cskg.utils.entity import Entity
from cskg.utils.graph_component import GraphComponent


class Relationship(GraphComponent, ABC):
    def __init__(
        self,
        from_type: Type[Entity],
        from_qualified_name: str,
        to_type: Type[Entity],
        to_qualified_name: str,
        **kwargs,
    ):
        self.from_type: Type[Entity]
        self.from_qualified_name: str
        self.to_type: Type[Entity]
        self.to_qualified_name: str
        super().__init__(
            from_type=from_type,
            from_qualified_name=from_qualified_name,
            to_type=to_type,
            to_qualified_name=to_qualified_name,
            **kwargs,
        )

    @classmethod
    def from_dict(cls, dict):
        instance = super().from_dict(dict)

        from_type_str = instance.from_type
        to_type_str = instance.to_type

        from_type = Entity.get_class(from_type_str)
        to_type = Entity.get_class(to_type_str)

        instance.from_type = from_type
        instance.to_type = to_type
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
    param_name: str


class ReturnsRel(Relationship):
    type = "returns_rel"
    label = "RETURNS"


class YieldsRel(Relationship):
    type = "yields_rel"
    label = "YIELDS"


class InstantiatesRel(Relationship):
    type = "instantiates_rel"
    label = "INSTANTIATES"

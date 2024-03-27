from abc import ABC
from typing import override

from cskg.utils.graph_component import GraphComponent


class Relationship(GraphComponent, ABC):
    __required_fields__ = [
        "from_type",
        "from_qualified_name",
        "to_type",
        "to_qualified_name",
    ]

    # def __init__(
    #     self,
    #     from_type: Type[Entity],
    #     from_qualified_name: str,
    #     to_type: Type[Entity],
    #     to_qualified_name: str,
    #     **kwargs,
    # ):
    #     super().__init__(
    #         type=self.type,
    #         label=self.label,
    #         from_type=from_type,
    #         from_qualified_name=from_qualified_name,
    #         to_type=to_type,
    #         to_qualified_name=to_qualified_name,
    #         **kwargs,
    #     )

    @classmethod
    @override
    def from_json(cls, json):
        instance = super().from_json(json)

        from_type_str = json["from_type"]
        to_type_str = json["to_type"]

        from_type = GraphComponent.get_class(from_type_str)  # Expect entity
        to_type = GraphComponent.get_class(to_type_str)  # Expect entity

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


class ReturnsRel(Relationship):
    type = "returns_rel"
    label = "RETURNS"


class YieldsRel(Relationship):
    type = "yields_rel"
    label = "YIELDS"


class InstantiatesRel(Relationship):
    type = "instantiates_rel"
    label = "INSTANTIATES"

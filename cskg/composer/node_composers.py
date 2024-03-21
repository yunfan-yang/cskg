from abc import ABC, abstractmethod
import json
from typing import Any, Iterable, Type

from cskg.entity import Entity
from cskg.relationship import Relationship


class AbstractComposer(ABC):
    @abstractmethod
    def get_cypher(self, entity: dict[str, Any]) -> str: ...

    def get_dictionary_cypher(
        self, dictionary: dict[str, Any], excluded_fields: list[str] = None
    ) -> str:
        if not excluded_fields:
            excluded_fields = ["_id"]

        dictionary = _exclude_fields_dict(dictionary, excluded_fields)

        keypairs = []
        for key, value in dictionary.items():
            if isinstance(value, str):
                keypairs.append(f"{key}: '{value}'")
            elif value is None:
                keypairs.append(f"{key}: NULL")
            elif isinstance(value, (list, dict)):
                return key + ": " + json.dumps(value).replace("'", "")
            else:
                keypairs.append(f"{key}: {value}")
        return ", ".join(keypairs)


class EntityComposer(AbstractComposer):
    def get_cypher(self, entity: Entity):
        entity_type = map(lambda label: f":{label}", entity.labels)
        entity_properties = self.get_dictionary_cypher(entity)

        return f"""
            CREATE ({entity_type} {{ {entity_properties} }}) 
        """


def _exclude_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in dict if key not in fields}


class RelationshipComposer(AbstractComposer):
    def get_cypher(self, relationship: Relationship):
        relation_type = f":{relationship.label}"

        field_a_type = relationship.get("from_type")
        field_b_type = relationship.get("to_type")
        field_a_value = relationship.get("from_qualified_name")
        field_b_value = relationship.get("to_qualified_name")

        relationship_properties = self.get_dictionary_cypher(
            relationship,
            ["_id", "from_qualified_name", "to_qualified_name", "from_type", "to_type"],
        )

        return f"""
            MATCH (a:{field_a_type} {{qualified_name: "{field_a_value}"}}), (b:{field_b_type} {{qualified_name: "{field_b_value}"}})
            CREATE (a)-[{relation_type} {{ {relationship_properties} }}]->(b)
        """


NodeComposer = EntityComposer | RelationshipComposer


def ensure_list_of_strings(variable):
    if isinstance(variable, str):
        return [variable]
    elif isinstance(variable, Iterable):
        return variable
    else:
        raise ValueError("Variable must be a string or a list of strings")

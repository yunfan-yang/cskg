from abc import ABC, abstractmethod
import json
from typing import Any, Iterable


class AbstractNodeComposer(ABC):
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


class EntityComposer(AbstractNodeComposer):
    def __init__(self, entity_label: str | Iterable[str]):
        self.entity_type = ":".join(
            map(lambda x: x.capitalize(), ensure_list_of_strings(entity_label))
        )

    def get_cypher(self, entity: dict[str, Any]):
        entity_type = self.entity_type
        entity_properties = self.get_dictionary_cypher(entity)

        return f"""
            CREATE (:{entity_type} {{ {entity_properties} }}) 
        """


def _exclude_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in dict if key not in fields}


class RelationshipComposer(AbstractNodeComposer):
    Field = tuple[str, str]
    """
    A tuple of (name: str, type: str).
    """

    def __init__(
        self,
        relation_label: str,
        from_field: Field,
        to_field: Field,
    ):
        self.relation_type = relation_label.upper()
        self.from_field = from_field
        self.to_field = to_field

    def get_cypher(self, relationship: dict[str, Any]):
        relation_type = self.relation_type

        field_a_name, field_a_type = self.from_field
        field_b_name, field_b_type = self.to_field

        field_a_value = relationship.get(field_a_name)
        field_b_value = relationship.get(field_b_name)
        field_a_type_neo = field_a_type.capitalize()
        field_b_type_neo = field_b_type.capitalize()

        relationship_properties = self.get_dictionary_cypher(
            relationship, ["_id", field_a_name, field_b_name]
        )

        return f"""
            MATCH (a:{field_a_type_neo} {{qualified_name: "{field_a_value}"}}), (b:{field_b_type_neo} {{qualified_name: "{field_b_value}"}})
            CREATE (a)-[:{relation_type} {{ {relationship_properties} }}]->(b)
        """


NodeComposer = EntityComposer | RelationshipComposer


def ensure_list_of_strings(variable):
    if isinstance(variable, str):
        return [variable]
    elif isinstance(variable, Iterable):
        return variable
    else:
        raise ValueError("Variable must be a string or a list of strings")

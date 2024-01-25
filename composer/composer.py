from typing import Any
from composer.models import *
from loguru import logger
from neomodel import DoesNotExist, db

ENTITY_FIELDS_MAPPING = {
    "class": ["name", "qualified_name", "file_path"],
    "function": ["name", "qualified_name", "file_path"],
}

RELATIONSHIP_FIELDS_MAPPING = {
    "calls_rel": [
        ["function_qualified_name", "Function"],
        ["called_function_qualified_name", "Function"],
    ],
    "inherits_rel": [
        ["class_qualified_name", "Class"],
        ["inherited_class_qualified_name", "Class"],
    ],
    "contains_rel": [
        ["class_qualified_name", "Class"],
        ["function_qualified_name", "Function"],
    ],
}


class GraphComposer:
    def __init__(self, entities: list = None, relationships: list = None):
        self.entities = entities or []
        self.relationships = relationships or []

    def compose(self):
        GraphComposer.compose_entities(self.entities)
        GraphComposer.compose_relationships(self.relationships)

    @classmethod
    @db.transaction
    def compose_entities(self, entities: list):
        for entity in entities:
            logger.debug(entity)
            try:
                cypher = GraphComposer.get_entity_cypher(entity)
                logger.debug(cypher)
                db.cypher_query(cypher)
            except DoesNotExist as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)
                raise e

    @classmethod
    @db.transaction
    def compose_relationships(self, relationships: list):
        for relationship in relationships:
            logger.debug(relationship)
            try:
                cypher = GraphComposer.get_relationship_cypher(relationship)
                logger.debug(cypher)
                db.cypher_query(cypher)
            except Exception as e:
                logger.error(e)
                raise e

    @classmethod
    def get_entity_cypher(cls, entity: dict[str, Any]):
        node_type = entity.get("type")

        if not isinstance(node_type, str):
            logger.error(f"Unknown node type: {node_type}")
            return

        node_type_neo = node_type.capitalize()

        included_fields = ENTITY_FIELDS_MAPPING.get(node_type)

        included_fields_dict = _included_fields_dict(entity, included_fields)
        entity_properties = [
            f"{key}: '{value}'" for key, value in included_fields_dict.items()
        ]
        entity_properties_neo = ", ".join(entity_properties)

        return f"""
            CREATE (:{node_type_neo} {{ {entity_properties_neo} }}) 
        """

    @classmethod
    def get_relationship_cypher(cls, relationship: dict[str, Any]):
        node_type = relationship.get("type")

        if not isinstance(node_type, str):
            logger.error(f"Unknown relationship type: {node_type}")
            return

        node_type_neo = node_type.replace("_rel", "").upper()

        fields = RELATIONSHIP_FIELDS_MAPPING.get(node_type)

        field_a_name, field_a_type = fields[0]
        field_b_name, field_b_type = fields[1]

        field_a_value = relationship.get(field_a_name)
        field_b_value = relationship.get(field_b_name)
        field_a_type_neo = field_a_type.capitalize()
        field_b_type_neo = field_b_type.capitalize()

        return f"""
            MATCH (a:{field_a_type_neo} {{qualified_name: "{field_a_value}"}}), (b:{field_b_type_neo} {{qualified_name: "{field_b_value}"}})
            CREATE (a)-[:{node_type_neo}]->(b)
        """


def _included_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in fields if key in dict}

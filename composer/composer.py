from typing import Any
from composer.models import *
from loguru import logger
from neomodel import DoesNotExist


class GraphComposer:
    def __init__(self, entities: list = [], relationships: list = []):
        self.entities = entities
        self.relationships = relationships

    def compose(self):
        GraphComposer.compose_entities(self.entities)
        GraphComposer.compose_relationships(self.relationships)

    @classmethod
    def compose_entities(self, entities: list):
        for entity in entities:
            logger.debug(entity)
            try:
                instance = GraphComposer.instantiate(entity)
                instance.save()
            except DoesNotExist as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)
                raise e

    @classmethod
    def compose_relationships(self, relationships: list):
        for relationship in relationships:
            logger.debug(relationship)
            try:
                instance = GraphComposer.instantiate(relationship)
            except DoesNotExist as e:
                logger.error(e)
            except Exception as e:
                logger.error(e)
                raise e

    @classmethod
    def instantiate(cls, node: dict[str, Any]):
        node_type = node.get("type")
        logger.debug(node_type)

        if node_type == "class":
            included_fields = [
                "name",
                "qualified_name",
                "file_path",
            ]
            arguments = _included_fields_dict(node, included_fields)
            logger.debug(arguments)
            return Class(**arguments)

        elif node_type == "function":
            included_fields = [
                "name",
                "qualified_name",
                "file_path",
            ]
            arguments = _included_fields_dict(node, included_fields)
            return Function(**arguments)

        elif node_type == "calls_rel":
            function_qualified_name = node.get("function_qualified_name")
            called_function_qualified_name = node.get("called_function_qualified_name")
            logger.debug(
                f"Calls: {function_qualified_name} -> {called_function_qualified_name}"
            )

            f1 = Function.nodes.get(qualified_name=function_qualified_name)
            f2 = Function.nodes.get(qualified_name=called_function_qualified_name)

            rel = f1.calls.connect(f2, {})
            return rel

        elif node_type == "inherits_rel":
            class_qualified_name = node.get("class_qualified_name")
            inherited_class_qualified_name = node.get("inherited_class_qualified_name")
            logger.debug(
                f"Inherits: {class_qualified_name} -> {inherited_class_qualified_name}"
            )

            c1 = Class.nodes.get(qualified_name=class_qualified_name)
            c2 = Class.nodes.get(qualified_name=inherited_class_qualified_name)

            rel = c1.inherits.connect(c2, {})
            return rel

        elif node_type == "contains_rel":
            class_qualified_name = node.get("class_qualified_name")
            function_qualified_name = node.get("function_qualified_name")
            logger.debug(
                f"Contains: {class_qualified_name} -> {function_qualified_name}"
            )

            c1 = Class.nodes.get(qualified_name=class_qualified_name)
            f1 = Function.nodes.get(qualified_name=function_qualified_name)

            rel = c1.contains.connect(f1, {})
            return rel

        else:
            logger.warn("Unknown node type")


def _included_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in fields if key in dict}

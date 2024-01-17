from typing import Any
from composer.models import *
from loguru import logger


class GraphComposer:
    def __init__(self):
        self.classes = []
        self.functions = []
        self.calls_rel = []
        self.inherits_rel = []

    def compose(self):
        everything = []
        everything.extend(self.classes)
        everything.extend(self.functions)
        everything.extend(self.calls_rel)
        everything.extend(self.inherits_rel)

        logger.info(everything)

        for thing in everything:
            logger.debug(thing)
            try:
                instance = GraphComposer.instantiate(thing)
                logger.debug(instance)
                instance.save()
            except Exception as e:
                logger.error(e)
                pass

    @classmethod
    def instantiate(cls, node: dict[str, Any]):
        node_type = node.get("type")
        logger.info(node_type)

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
            logger.info(
                f"{function_qualified_name} calls {called_function_qualified_name}"
            )

            f1 = Function.nodes.get_or_none(qualified_name=function_qualified_name)
            f2 = Function.nodes.get_or_none(
                qualified_name=called_function_qualified_name
            )

            logger.debug(f"{f1}")
            logger.debug(f"{f2}")

            if f1 is None or f2 is None:
                raise Exception("Invalid entities")

            rel = f1.calls.connect(f2, {})
            logger.debug(f"rel: {rel}")

            return rel

        elif node_type == "inherits_rel":
            class_qualified_name = node.get("class_qualified_name")
            inherited_class_qualified_name = node.get("inherited_class_qualified_name")
            logger.info(
                f"{class_qualified_name} inherits {inherited_class_qualified_name}"
            )

            c1 = Class.nodes.get_or_none(qualified_name=class_qualified_name)
            c2 = Class.nodes.get_or_none(qualified_name=inherited_class_qualified_name)

            if c1 is None or c2 is None:
                raise Exception("Invalid entities")

            rel = c1.inherits.connect(c2, {})
            logger.debug(f"rel: {rel}")
            return rel

        else:
            raise Exception("Invalid node type")


def _included_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict.get(key) for key in fields if key in dict}

from typing import Any
from composer.models import *


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

        for thing in everything:
            try:
                instance = self.instantiate(thing)
                instance.save()
            except:
                pass

    @classmethod
    def instantiate(node: dict[str, Any]):
        node_type = node.get("type")

        if node_type == "class":
            included_fields = [
                "name",
                "qualified_name",
                "file_path",
            ]
            arguments = _included_fields_dict(node, included_fields)
            return Class(**arguments)

        elif node_type == "function":
            return Function(**node)

        elif node_type == "calls_rel":
            function_qualified_name = node.get("function_qualified_name")
            called_function_qualified_name = node.get("called_function_qualified_name")

            f1 = Function.nodes.get_or_none(function_qualified_name)
            f2 = Function.nodes.get_or_none(called_function_qualified_name)

            if f1 is None or f2 is None:
                raise Exception("Invalid entities")

            return f1.calls.connect(f2)

        elif node_type == "inherits_rel":
            class_qualified_name = node.get("class_qualified_name")
            inherited_class_qualified_name = node.get("inherited_class_qualified_name")

            c1 = Class.nodes.get_or_none(class_qualified_name)
            c2 = Class.nodes.get_or_none(inherited_class_qualified_name)

            if c1 is None or c2 is None:
                raise Exception("Invalid entities")

            return c1.inherits.connect(c2)

        else:
            raise Exception("Invalid node type")


def _included_fields_dict(dict: dict[str, Any], fields: list[str]):
    return {key: dict[key] for key in fields if key in dict}

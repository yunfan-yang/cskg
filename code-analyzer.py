import os
import astroid
import neomodel

from models import Class, Function


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def analyze(self):
        self.__traverse_files()

    def __traverse_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.__extract_file(file_path)

    def __extract_file(self, file_path):
        module_name = file_path.split("/")[-1].split(".")[0]

        with open(file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, file_path)
            entities = self.__visit_children(tree)

    def __visit_children(self, node: astroid.Module) -> list[neomodel.StructuredNode]:
        entities = []

        children = node.get_children()
        for child in children:
            es = self.__visit_node(child)
            entities.extend(es)

        return entities

    def __visit_node(self, node) -> list[neomodel.StructuredNode]:
        entities = []

        if isinstance(node, astroid.ClassDef):
            c = self.__visit_class(node)
            entities.append(c)

        elif isinstance(node, astroid.FunctionDef):
            f = self.__visit_function(node)
            entities.append(f)

        return entities

    def __visit_class(self, node: astroid.ClassDef) -> Class:
        name = node.name
        qualified_name = node.qname()
        print(f"Class: {name} ({qualified_name})")

        c = Class(name=name, qualified_name=qualified_name)
        c.save()

        # Visit children
        children_entities = self.__visit_children(node)
        for child_entity in children_entities:
            c.contains.connect(child_entity)

        return c

    def __visit_function(self, node: astroid.FunctionDef) -> Function:
        name = node.name
        qualified_name = node.qname()
        args = node.args
        print(f"Function: {name} ({qualified_name})")

        f = Function(name=name, qualified_name=qualified_name, args=args)
        f.save()
        return f


ca = CodeAnalyzer("target/requests")
ca.analyze()

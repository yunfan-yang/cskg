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
            nodes = self.__visit_children(tree)

    def __visit_children(self, node: astroid.Module) -> list[neomodel.StructuredNode]:
        nodes = []

        children = node.get_children()
        for child in children:
            es = self.__visit_node(child)
            nodes.extend(es)

        return nodes

    def __visit_node(self, node) -> list[neomodel.StructuredNode]:
        nodes = []

        if isinstance(node, astroid.ClassDef):
            c = self.__visit_class(node)
            nodes.append(c)

        elif isinstance(node, astroid.FunctionDef):
            f = self.__visit_function(node)
            nodes.append(f)

        return nodes

    def __visit_class(self, node: astroid.ClassDef) -> Class:
        name = node.name
        qualified_name = node.qname()
        print(f"Class: {name} ({qualified_name})")

        c = Class(name=name, qualified_name=qualified_name)
        c.save()

        # Visit children
        children_nodes = self.__visit_children(node)
        for child_entity in children_nodes:
            c.contains.connect(child_entity)

        return c

    def __visit_function(self, node: astroid.FunctionDef) -> Function:
        name = node.name
        qualified_name = node.qname()
        args = node.args
        print(f"Function: {name} ({qualified_name})")

        fs = Function.get_or_create(
            {"name": name, "qualified_name": qualified_name, "args": args}
        )
        f = fs[0]

        # Visit body
        body_nodes = [
            body_node_children
            for body_node in node.body
            for body_node_children in body_node.get_children()
        ]
        for body_node in body_nodes:
            if isinstance(body_node, astroid.Call):
                try:
                    inferred_nodes = body_node.func.infer()

                    for inferred_node in inferred_nodes:
                        if isinstance(
                            inferred_node, (astroid.FunctionDef, astroid.UnboundMethod)
                        ):
                            name = inferred_node.name
                            qualified_name = inferred_node.qname()
                            args = body_node.args
                            keywords = body_node.keywords

                            if not qualified_name.startswith("builtins."):
                                print(f"  Calls: {name} ({qualified_name})")

                                f_called = self.__visit_function(inferred_node)

                                f.calls.connect(
                                    f_called, {"args": args, "keywords": keywords}
                                )

                except astroid.exceptions.InferenceError:
                    print(f"Error inferring function call in {name}")

        return f


ca = CodeAnalyzer("target/requests")
ca.analyze()

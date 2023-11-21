import os
import astroid
import neomodel

from models import Class, Function


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_file_path = None

    def analyze(self):
        self.__traverse_files()

    def __traverse_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):
                    self.current_file_path = os.path.join(root, file)
                    self.__extract_file()

        self.__visit_function_calls()

    def __extract_file(self):
        module_name = self.current_file_path.split("/")[-1].split(".")[0]

        with open(self.current_file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, self.current_file_path)
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

        c = Class(
            name=name, qualified_name=qualified_name, file_path=self.current_file_path
        )
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

        f = Function(
            name=name,
            qualified_name=qualified_name,
            args=args,
            file_path=self.current_file_path,
        )

        # Visit body and write down function calls
        body_nodes = [
            body_node_child
            for body_node in node.body
            for body_node_child in body_node.get_children()
            if isinstance(body_node_child, astroid.Call)
        ]
        inferred_nodes = []
        try:
            for body_node in body_nodes:
                inferred_nodes.extend(body_node.func.inferred())
        except astroid.exceptions.InferenceError:
            pass
        inferred_nodes = [
            inferred_node
            for inferred_node in inferred_nodes
            if inferred_node is not astroid.Uninferable
        ]

        f.inferred_nodes = [inferred_node.qname() for inferred_node in inferred_nodes]

        f.save()
        return f

    def __visit_function_calls(self):
        # Get all functions
        functions = Function.nodes.all()

        # for f in functions:
        # # Visit body
        # body_nodes = [
        #     body_node_children
        #     for body_node in f.body
        #     for body_node_children in body_node.get_children()
        #     if isinstance(body_node, astroid.Call)
        # ]

        # for body_node in body_nodes:
        #     try:
        #         inferred_nodes = [
        #             inferred_node
        #             for inferred_node in body_node.func.infer()
        #             if isinstance(
        #                 inferred_node, (astroid.FunctionDef, astroid.UnboundMethod)
        #             )
        #         ]

        #         for inferred_node in inferred_nodes:
        #             name = inferred_node.name
        #             qualified_name = inferred_node.qname()
        #             args = body_node.args
        #             keywords = body_node.keywords

        #             if not qualified_name.startswith("builtins."):
        #                 print(f"  Calls: {name} ({qualified_name})")

        #                 f_called = Function.nodes.get(
        #                     qualified_name=qualified_name
        #                 )

        #                 f.calls.connect(
        #                     f_called, {"args": args, "keywords": keywords}
        #                 )

        #     except astroid.exceptions.InferenceError:
        #         print(f"Error inferring function call in {name}")


ca = CodeAnalyzer("target/requests")
ca.analyze()

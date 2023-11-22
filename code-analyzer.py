import os
import astroid
import neomodel

from models import Class, Function, CallsRelRow, postgres_session


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_file_path = None

    def analyze(self):
        self.__traverse_files()
        self.__hook_inferred_nodes()

    def __traverse_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):
                    self.current_file_path = os.path.join(root, file)
                    self.__extract_file()

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
        f.save()

        self.__visit_function_inferred_nodes(node)
        self.__visit_children(node)
        return f

    def __visit_function_inferred_nodes(self, node: astroid.FunctionDef):
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

        for inferred_node in inferred_nodes:
            function_qualified_name = node.qname()
            called_function_qualified_name = inferred_node.qname()

            crr = CallsRelRow(
                function_qualified_name=function_qualified_name,
                called_function_qualified_name=called_function_qualified_name,
            )
            postgres_session.add(crr)

        postgres_session.commit()

    def __hook_inferred_nodes(self):
        # Get all functions
        calls_rel_rows = postgres_session.query(CallsRelRow).all()

        for calls_rel_row in calls_rel_rows:
            try:
                function_qualified_name = calls_rel_row.function_qualified_name
                called_function_qualified_name = (
                    calls_rel_row.called_function_qualified_name
                )

                function_node = Function.nodes.get_or_none(
                    qualified_name=function_qualified_name
                )
                called_function_node = Function.nodes.get_or_none(
                    qualified_name=called_function_qualified_name
                )

                if function_node is None or called_function_node is None:
                    continue

                print(
                    f"Function {function_qualified_name} calls {called_function_qualified_name}"
                )
                function_node.calls.connect(called_function_node)
                calls_rel_row.is_linked = True
            except neomodel.exceptions.DoesNotExist:
                print(
                    f"Function {function_qualified_name} calls {called_function_qualified_name} but one of them does not exist"
                )
            except neomodel.exceptions.MultipleNodesReturned:
                print(
                    f"Function {function_qualified_name} calls {called_function_qualified_name} but one of them is duplicated"
                )

        postgres_session.commit()


# Clean database
postgres_session.query(CallsRelRow).delete()
postgres_session.commit()
neomodel.db.cypher_query("MATCH (n) DETACH DELETE n")

# Analyze codebase
ca = CodeAnalyzer("target/requests")
ca.analyze()

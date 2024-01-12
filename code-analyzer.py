import os
import astroid
import neo4j
import neomodel
import json
from typing import Union
from loguru import logger

from models import (
    postgres_session,
    Class,
    Function,
    CallsRelRow,
    InheritsRelRow,
    ClassRow,
    FunctionRow,
)


logger.add("logs/default.log")


CallableNode = Union[
    astroid.FunctionDef, astroid.BoundMethod, astroid.UnboundMethod, astroid.Lambda
]


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_file_path = None

    def analyze(self):
        self.__traverse_files()
        # self.__hook_inferred_nodes()
        # self.__hook_inherited_nodes()

    def __traverse_files(self):
        logger.debug("traverse files")
        for root, dirs, files in os.walk(self.folder_path):
            logger.debug(f"root {root}")
            for file in files:
                if file.endswith(".py"):
                    self.current_file_path = os.path.join(root, file)
                    logger.debug(f"current file path: {self.current_file_path}")
                    self.__extract_file()

    def __create_node(self, cls: astroid.Module, **kwargs) -> neomodel.StructuredNode:
        # Create node
        try:
            node = cls(**kwargs)
            node.save()
        except neomodel.exceptions.UniqueProperty or neo4j.exceptions.ConstraintError:
            node = cls.nodes.get_or_none(**kwargs)

        logger.debug(f"Creating {cls} with kwargs {kwargs} {node}")
        return node

    def __extract_file(self):
        module_name = self.current_file_path.split("/")[-1].split(".")[0]

        with open(self.current_file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, self.current_file_path)
            self.__visit_children(tree)

    def __visit_children(self, node: astroid.NodeNG):
        children = node.get_children()
        for child in children:
            self.__visit_node(child)

    def __visit_node(self, node):
        if isinstance(node, astroid.ClassDef):
            self.__visit_class(node)

        elif isinstance(node, astroid.FunctionDef):
            self.__visit_function(node)

    def __visit_class(self, node: astroid.ClassDef):
        name = node.name
        qualified_name = node.qname()
        logger.info(f"Class: {qualified_name}")

        # Create class
        attributes = {"file_path": self.current_file_path}
        clr = ClassRow(
            name=name,
            qualified_name=qualified_name,
            is_created=False,
            attributes=json.dumps(attributes),
        )
        postgres_session.add(clr)

        # Visit parents
        parent_classes = node.ancestors(recurs=False)
        for parent_class in parent_classes:
            ihs = InheritsRelRow(
                class_qualified_name=qualified_name,
                inherited_class_qualified_name=parent_class.qname(),
            )
            postgres_session.add(ihs)

        # Visit children
        self.__visit_children(node)

    def __visit_function(self, node: astroid.FunctionDef):
        name = node.name
        qualified_name = node.qname()
        args = node.args
        logger.debug(f"Function: {name} ({qualified_name})")

        attributes = {
            "file_path": self.current_file_path,
        }
        fnr = FunctionRow(
            name=name,
            qualified_name=qualified_name,
            is_created=False,
            attributes=json.dumps(attributes),
        )
        postgres_session.add(fnr)

        self.__visit_function_inferred_nodes(node)
        self.__visit_children(node)

    def __visit_function_inferred_nodes(self, node: astroid.FunctionDef):
        # Visit body and write down function calls
        calls = [
            body_node_child
            for body_node in node.body
            for body_node_child in body_node.get_children()
            if isinstance(body_node_child, astroid.Call)
        ]

        for call in calls:
            inferred_nodes = []
            try:
                """
                Multiple Possible Inferences:
                In Python, a name (like that of a function) can refer to multiple different objects over the course
                of a program's execution. Astroid's inference engine takes this into account and attempts to infer
                all possible objects a name could refer to at a given point in the code.
                For example, if a function name is reassigned multiple times to different callable objects,
                inferred() will return all of these possibilities.
                """

                inferred_nodes = call.func.inferred()
            except astroid.exceptions.InferenceError:
                pass

            # All arguments values passed to the inferred functions
            args_objects = call.args
            # args_values = [arg.value for arg in args_objects]
            logger.debug(
                f"Call {node.qname()} calls {inferred_nodes} with {args_objects}"
            )

            # All parameters of the inferred functions
            for inferred_node in inferred_nodes:
                logger.debug(f"Inferred node: {inferred_node}")
                if isinstance(inferred_node, CallableNode):
                    params_objects = inferred_node.args.args
                    params_names = (
                        [param.name for param in params_objects]
                        if params_objects
                        else []
                    )
                    logger.debug(f"Params: {params_names}")

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

                logger.debug(
                    f"Function {function_qualified_name} calls {called_function_qualified_name}"
                )
                function_node.calls.connect(called_function_node)
                calls_rel_row.is_linked = True
            except neomodel.exceptions.DoesNotExist:
                logger.info(
                    f"Function {function_qualified_name} calls {called_function_qualified_name} but one of them does not exist"
                )
            except neomodel.exceptions.MultipleNodesReturned:
                logger.debug(
                    f"Function {function_qualified_name} calls {called_function_qualified_name} but one of them is duplicated"
                )

        postgres_session.commit()

    def __hook_inherited_nodes(self):
        inherits_rel_rows = postgres_session.query(InheritsRelRow).all()

        for inherits_rel_row in inherits_rel_rows:
            try:
                class_qualified_name = inherits_rel_row.class_qualified_name
                inherited_class_qualified_name = (
                    inherits_rel_row.inherited_class_qualified_name
                )

                class_node = Class.nodes.get_or_none(
                    qualified_name=class_qualified_name
                )
                inherited_class_node = Class.nodes.get_or_none(
                    qualified_name=inherited_class_qualified_name
                )

                if class_node is None or inherited_class_node is None:
                    continue

                logger.debug(
                    f"Class {class_qualified_name} inherites {inherited_class_qualified_name}"
                )
                class_node.inherits.connect(inherited_class_node)
                inherits_rel_row.is_linked = True
            except neomodel.exceptions.DoesNotExist:
                logger.info(
                    f"Function {class_qualified_name} calls {inherited_class_qualified_name} but one of them does not exist"
                )
            except neomodel.exceptions.MultipleNodesReturned:
                logger.debug(
                    f"Function {class_qualified_name} calls {inherited_class_qualified_name} but one of them is duplicated"
                )
        postgres_session.commit()


# Clean database
postgres_session.query(ClassRow).delete()
postgres_session.query(FunctionRow).delete()
postgres_session.query(CallsRelRow).delete()
postgres_session.query(InheritsRelRow).delete()
postgres_session.commit()
neomodel.db.cypher_query("MATCH (n) DETACH DELETE n")
neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Function_qualified_name")
neomodel.db.cypher_query("DROP CONSTRAINT constraint_unique_Class_qualified_name")

# Analyze codebase
ca = CodeAnalyzer("targets/requests")
ca.analyze()

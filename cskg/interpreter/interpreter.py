import os
from typing import Generator
from astroid import FunctionDef, Module, ClassDef, Lambda
from astroid.manager import AstroidManager
from loguru import logger
from hashlib import md5

from cskg.utils.graph_component import GraphComponent
from cskg.interpreter.utils import remove_module_prefix
from cskg.interpreter.nodes import visit_node


class CodeInterpreter:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.folder_abs_path = os.path.abspath(folder_path)
        self.manager = AstroidManager()
        self.manager.register_transform(Module, self.format_qname)
        self.manager.register_transform(ClassDef, self.format_qname)
        self.manager.register_transform(FunctionDef, self.format_qname)
        self.manager.register_transform(Lambda, self.format_lambda_name)

    def visit(self) -> Generator[GraphComponent, None, None]:
        asts = {}

        for root, dirs, files in os.walk(self.folder_abs_path):
            for file in files:
                if str(file).endswith(".py"):  # Only handles python file
                    file_path = os.path.join(root, file)
                    asts[file_path] = self.manager.ast_from_file(file_path)
                    logger.debug(f"Ast from file: {file_path}")

        for file_path, ast in asts.items():
            yield from visit_node(ast)

    def format_qname(self, node: Module | ClassDef | FunctionDef):
        original_qname_function = node.qname
        node.qname = lambda: remove_module_prefix(
            original_qname_function(), self.folder_path
        )

        # Set file path to None if it is not internal entity
        node_root_file = node.root().file
        if node_root_file and not node_root_file.startswith(self.folder_abs_path):
            node.root().file = None

        return node

    def format_lambda_name(self, lambda_func: Lambda):
        lambda_hash = md5(lambda_func.as_string().encode()).hexdigest()[:8]
        lambda_func.name = f"lambda_{lambda_hash}"
        return lambda_func

    def get_module_prefix(self):
        return self.folder_abs_path.split("/")[-1]

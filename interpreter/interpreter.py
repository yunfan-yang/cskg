import os
import astroid
from astroid.manager import AstroidManager
from loguru import logger

from interpreter.nodes import visit_children


class CodeInterpreter:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.manager = AstroidManager()

    def interpret(self):
        yield from self.traverse_files()

    def traverse_files(self):
        asts = {}

        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):  # Only handles python file
                    current_file_path = os.path.join(root, file)

                    ast = self.manager.ast_from_file(current_file_path)
                    asts[current_file_path] = ast

        for file_path, ast in asts.items():
            yield from visit_children(ast, file_path)

    def extract_file(self, current_file_path: str = None):
        logger.debug(f"extract file {current_file_path}")
        module_name = current_file_path.split("/")[-1].split(".")[0]

        with open(current_file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, current_file_path)

            yield from visit_children(tree, current_file_path)

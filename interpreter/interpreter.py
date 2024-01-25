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

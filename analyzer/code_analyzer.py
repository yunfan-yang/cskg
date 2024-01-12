import os
import astroid
import neo4j
import neomodel
import json
from typing import Union
from loguru import logger

from analyzer.node import visit_children


logger.add("logs/default.log")


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_file_path = None

    def analyze(self):
        yield from self.__traverse_files()
        # self.__hook_inferred_nodes()
        # self.__hook_inherited_nodes()

    def __traverse_files(self):
        logger.debug("traverse files")
        for root, dirs, files in os.walk(self.folder_path):
            logger.debug(f"root {root}")
            for file in files:
                if file.endswith(".py"): # Only handles python file
                    self.current_file_path = os.path.join(root, file)
                    logger.debug(f"current file path: {self.current_file_path}")
                    yield from self.__extract_file()

    def __extract_file(self):
        module_name = self.current_file_path.split("/")[-1].split(".")[0]

        with open(self.current_file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, self.current_file_path)

            yield from visit_children(tree)

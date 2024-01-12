import os
import astroid

from analyzer.node import visit_children


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.current_file_path = None

    def analyze(self):
        yield from self.__traverse_files()

    def __traverse_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):  # Only handles python file
                    current_file_path = os.path.join(root, file)
                    yield from self.__extract_file(current_file_path)

    def __extract_file(self, current_file_path: str = None):
        module_name = current_file_path.split("/")[-1].split(".")[0]

        with open(current_file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, current_file_path)

            yield from visit_children(tree, current_file_path)

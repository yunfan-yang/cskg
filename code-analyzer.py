import ast
import os


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def traverse(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.extract_file(file_path)
                break
            break

    def extract_file(self, file_path):
        with open(file_path, "r") as file:
            code = file.read()
            tree = ast.parse(code)
            self.visit_tree(tree)

    def visit_tree(self, tree):
        entities = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                entities.append(node.name)
            # elif isinstance(node, ast.FunctionDef):
            #     entities.append(node.name)
        print(entities)


ca = CodeAnalyzer("target/transformers")
ca.traverse()

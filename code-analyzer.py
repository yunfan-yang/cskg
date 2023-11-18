import os
import astroid

from models import Class, Function


class CodeAnalyzer:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def traverse(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.extract_file(file_path)

    def extract_file(self, file_path):
        with open(file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code)
            children = tree.get_children()

            for node in children:
                if isinstance(node, astroid.ClassDef):
                    class_name = node.name
                    class_full_name = node.qname()
                    print(f"Class: {class_name} ({class_full_name})")

                    c = Class(name=class_name, full_name=class_full_name)
                    c.save()


ca = CodeAnalyzer("target/requests")
ca.traverse()

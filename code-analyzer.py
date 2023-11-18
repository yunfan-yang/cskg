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
        module_name = file_path.split("/")[-1].split(".")[0]

        with open(file_path, "r") as file:
            code = file.read()
            tree = astroid.parse(code, module_name, file_path)
            children = tree.get_children()

            for node in children:
                if isinstance(node, astroid.ClassDef):
                    class_name = node.name
                    class_qualified_name = node.qname()
                    print(f"Class: {class_name} ({class_qualified_name})")

                    c = Class(name=class_name, qualified_name=class_qualified_name)
                    c.save()

                    children = node.get_children()
                    for child in children:
                        if isinstance(child, astroid.FunctionDef):
                            function_name = child.name
                            function_qualified_name = child.qname()
                            args = child.args
                            print(f"Function: {function_name}")

                            f = Function(
                                name=function_name,
                                qualified_name=function_qualified_name,
                                args=args,
                            )
                            f.save()

                            c.contains.connect(f)
                            c.save()


ca = CodeAnalyzer("target/requests")
ca.traverse()

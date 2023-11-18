import os
import ast
from ast import NodeVisitor, Constant, Call, stmt, FunctionDef, Name

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
            #     break
            # break

    def extract_file(self, file_path):
        with open(file_path, "r") as file:
            code = file.read()
            tree = ast.parse(code)
            node_visitor = CodeAnalyzerNodeVisitor()
            node_visitor.visit(tree)


class CodeAnalyzerNodeVisitor(NodeVisitor):
    def __init__(self):
        self.current_class = None

    def visit_ClassDef(self, node):
        print(f"Class named {node.name} defined on line {node.lineno}")
        c = Class(name=node.name, full_name=node.name)
        c.save()

        self.current_class = c
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: FunctionDef):
        print(f"Function named {node.name} defined on line {node.lineno}")

        args = list(map(lambda arg: arg.arg, node.args.args))
        f = Function(name=node.name, full_name=node.name, args=args)
        f.save()

        if self.current_class:
            self.current_class.contains.connect(f)

        self.generic_visit(node)

    def visit_Call(self, node: Call):
        if isinstance(node.func, Name):
            print(
                f"  Calls function named {node.func.id} on line {node.lineno} with {node.args}"
            )

        self.generic_visit(node)


ca = CodeAnalyzer("target/requests")
ca.traverse()

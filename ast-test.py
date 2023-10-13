import ast
from ast import Constant, Call, stmt, FunctionDef
from typing import Any

code = """
a = 111

class A:
    def method1(self):
        pass

class B(A):
    def method2(self):
        pass

def function1():
    a = A()
    b = B()
    b.method2()

# Some comments
"""

tree = ast.parse(code)
print(tree)


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

    def visit_Constant(self, node: Constant) -> Any:
        print(f"Found constant {node.value} on line {node.lineno}")
        return super().visit_Constant(node)

    def visit_FunctionDef(self, node: FunctionDef):
        print(f"Function named {node.name} defined on line {node.lineno}")
        self.generic_visit(node)

    def visit_stmt(self, node: stmt) -> None:
        self.generic_visit(node)

    def visit_Call(self, node: Call):
        if isinstance(node.func, ast.Name):
            print(f"  Calls function named {node.func.id} on line {node.lineno}")
        self.generic_visit(node)


analyzer = CodeAnalyzer()
analyzer.visit(tree)

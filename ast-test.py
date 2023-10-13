import ast
from ast import Constant, Call, stmt, FunctionDef, NodeVisitor
from typing import Any

code = """
a = 111

class A:
    def method1(self):
        pass

class B(A):
    def method2(self):
        pass
        
    def method3(self, a, b):
        pass

def function1():
    a = A()
    b = B()
    b.method2()

def function4(param1, param2 = None):
    print(param1, param2)

def example(a, b=10, *args, c, d=20, **kwargs):
    pass

# Some comments
"""

tree = ast.parse(code)
print(tree)


class LongParameterAnalyzer(NodeVisitor):
    def __init__(self):
        super().__init__()

    def visit_Constant(self, node: Constant) -> Any:
        print(f"Found constant {node.value} on line {node.lineno}")
        return super().visit_Constant(node)

    def visit_FunctionDef(self, node: FunctionDef):
        print(f"Function named {node.name} defined on line {node.lineno}")
        func_params(node)
        self.generic_visit(node)

    def visit_stmt(self, node: stmt) -> None:
        self.generic_visit(node)

    def visit_Call(self, node: Call):
        if isinstance(node.func, ast.Name):
            print(f"  Calls function named {node.func.id} on line {node.lineno}")
        self.generic_visit(node)


def func_params(node: FunctionDef) -> list:
    # Print positional arguments and their default values
    for arg, default in zip(
        node.args.args[-len(node.args.defaults) :], node.args.defaults
    ):
        print(f"  Argument {arg.arg} with default value {ast.dump(default)}")
    for arg in node.args.args[
        : -len(node.args.defaults) if node.args.defaults else None
    ]:
        print(f"  Argument {arg.arg} without default value")

    # Print *args-style arguments
    if node.args.vararg:
        print(f"  *{node.args.vararg.arg} (Varargs)")

    # Print keyword-only arguments and their default values
    for kwarg, kw_default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if kw_default:
            print(
                f"  Keyword-only argument {kwarg.arg} with default value {ast.dump(kw_default)}"
            )
        else:
            print(f"  Keyword-only argument {kwarg.arg} without default value")

    # Print **kwargs-style arguments
    if node.args.kwarg:
        print(f"  **{node.args.kwarg.arg} (Keyword Varargs)")

    return node.args


class CodeAnalyzer2(NodeVisitor):
    def __init__(self):
        print("AAA")
        super().__init__()
    
    def visit_stmt(self, node: stmt) -> None:
        print("CodeAnalyzer2")
        self.generic_visit(node)

    def visit_Constant(self, node: Constant) -> Any:
        print(f"CCCC")
        return super().visit_Constant(node)


class CodeAnalyzer(LongParameterAnalyzer, CodeAnalyzer2):
    pass


analyzer = CodeAnalyzer()
analyzer.visit(tree)

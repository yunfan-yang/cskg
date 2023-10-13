from typing import Any
from ast import NodeVisitor, Constant, Call, stmt, FunctionDef


class LongParameterListAnalyzer(NodeVisitor):
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
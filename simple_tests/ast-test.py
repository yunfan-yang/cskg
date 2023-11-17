import ast
from simple_tests.parameter_list import ParameterListAnalyzer

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


class CodeAnalyzer(ParameterListAnalyzer):
    pass


analyzer = CodeAnalyzer()
analyzer.visit(tree)

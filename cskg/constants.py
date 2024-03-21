from enum import StrEnum


class Entity(StrEnum):
    MODULE = "module"
    CLASS = "class"
    VARIABLE = "variable"
    FUNCTION = "function"
    METHOD = "method"


class Relationship(StrEnum):
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    CONTAINS = "CONTAINS"
    TAKES = "TAKES"
    RETURNS = "RETURNS"
    YIELDS = "YIELDS"
    INSTANTIATES = "INSTANTIATES"
    USES = "USES"

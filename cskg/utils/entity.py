from abc import ABC

from cskg.utils.graph_component import GraphComponent
from cskg.utils.mixins import ExternalComponentMixin


class Entity(GraphComponent, ABC):
    def __init__(self, name: str, qualified_name: str, **kwargs):
        super().__init__(name=name, qualified_name=qualified_name, **kwargs)


class ModuleEntity(Entity):
    type = "module_ent"
    label = "Module"


class ClassEntity(Entity):
    type = "class_ent"
    label = "Class"


class FunctionEntity(Entity):
    type = "function_ent"
    label = "Function"


class MethodEntity(Entity):
    type = "method_ent"
    label = "Method"
    extra_labels = ("Function",)


class VariableEntity(Entity):
    type = "variable_ent"
    label = "Variable"


class ExternalModuleEntity(ModuleEntity, ExternalComponentMixin): ...


class ExternalClassEntity(ClassEntity, ExternalComponentMixin): ...


class ExternalFunctionEntity(FunctionEntity, ExternalComponentMixin): ...


class ExternalMethodEntity(MethodEntity, ExternalComponentMixin): ...


class ExternalVariableEntity(VariableEntity, ExternalComponentMixin): ...

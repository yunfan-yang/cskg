from abc import ABC

from cskg.utils.graph_component import GraphComponent

EXTERNAL_LABEL = "External"


class Entity(GraphComponent, ABC):
    __required_fields__ = ["name", "qualified_name"]


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


class ExternalModuleEntity(ModuleEntity):
    type = "external_" + ModuleEntity.type
    extra_labels = ModuleEntity.extra_labels + (EXTERNAL_LABEL,)


class ExternalClassEntity(ClassEntity):
    type = "external_" + ClassEntity.type
    extra_labels = ClassEntity.extra_labels + (EXTERNAL_LABEL,)


class ExternalFunctionEntity(FunctionEntity):
    type = "external_" + FunctionEntity.type
    extra_labels = FunctionEntity.extra_labels + (EXTERNAL_LABEL,)


class ExternalMethodEntity(MethodEntity):
    type = "external_" + MethodEntity.type
    extra_labels = MethodEntity.extra_labels + (EXTERNAL_LABEL,)


class ExternalVariableEntity(VariableEntity):
    type = "external_" + VariableEntity.type
    extra_labels = VariableEntity.extra_labels + (EXTERNAL_LABEL,)

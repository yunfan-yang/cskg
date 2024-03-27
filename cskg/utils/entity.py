from abc import ABC
from typing import Any, Self

from cskg.utils.graph_component import GraphComponent

EXTERNAL_LABEL = "External"


class Entity(GraphComponent, ABC):
    __final_fields__ = ["type", "label", "extra_labels"]
    __required_fields__ = ["name", "qualified_name", "file_path"]

    type: str = "entity"
    label: str = "Entity"
    extra_labels: tuple[str] = ()

    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        **kwargs,
    ):
        super().__init__(
            type=self.type,
            label=self.label,
            extra_labels=self.extra_labels,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            **kwargs,
        )

    @property
    def labels(self):
        return {self.label, *self.extra_labels}

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            return super().__getitem__(__name)
        except KeyError:
            raise AttributeError(f"Field {__name} not found")

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Not allowed to set attribute {__name}")
        super().__setattr__(__name, __value)
        super().__setitem__(__name, __value)

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> Self:
        excluded_final_fields_json = {
            key: value
            for key, value in json.items()
            if (key not in cls.__final_fields__ and key not in cls.__required_fields__)
        }

        entity_cls = Entity.get_class(json["type"])

        instance = entity_cls(
            name=json["name"],
            qualified_name=json["qualified_name"],
            file_path=json["file_path"],
            **excluded_final_fields_json,
        )

        return instance


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

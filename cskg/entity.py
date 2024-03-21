from typing import Any
from abc import ABC, ABCMeta


class EntityMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")
        super().__init__(name, bases, dct)


class Entity(dict, ABC, metaclass=EntityMeta):
    __final_fields__ = ["type", "label"]
    type = "entity"
    label = "Entity"

    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        **kwargs,
    ):
        if not hasattr(self, "labels"):
            self.labels = (self.label,)

        super().__init__(
            type=self.type,
            label=self.label,
            labels=self.labels,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            **kwargs,
        )

    def __setitem__(self, key, value):
        if key in self.__final_fields__:
            raise ValueError(f"Cannot set {key}")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key in self.__final_fields__:
            return self.get(key)
        return super().__getitem__(key)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getitem__(__name)
        except KeyError:
            return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Cannot set {__name}")
        super().__setitem__(__name, __value)


class ModuleEntity(Entity):
    type = "module_ent"
    label = "Module"


class ClassEntity(Entity):
    type = "class_ent"
    label = "Class"


class FunctionEntity(Entity):
    type = "function_ent"
    label = "Function"


class MethodEntity(FunctionEntity):
    type = "method_ent"
    label = "Method"
    labels = ("Method", "Function")


class VariableEntity(Entity):
    type = "variable_ent"
    label = "Variable"

from typing import Any, Self
from abc import ABC, ABCMeta


class EntityMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, "type") or not hasattr(cls, "label"):
            raise AttributeError(f"Class {name} lacks required 'label' class attribute")
        super().__init__(name, bases, dct)


class Entity(dict, ABC, metaclass=EntityMeta):
    __final_fields__ = ["type", "label", "extra_labels"]
    __required_fields__ = ["name", "qualified_name", "file_path"]

    type: str = "entity"
    label: str = "Entity"
    extra_labels: set[str] = ()

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

    @classmethod
    def get_class(cls, type: str):
        subclasses = cls.__subclasses__()
        for subclass in subclasses:
            if subclass.type == type:
                return subclass

        raise ValueError(f'Could not find class for "{type}" in {subclasses}')


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

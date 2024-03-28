from abc import ABC, ABCMeta
from typing import Any, Self

from cskg.utils.mixins import VisitSubclassesMixin, CreateInstanceMixin


class GraphComponentMeta(ABCMeta):
    def __init__(cls, name, bases, props):
        def check_meta_fields(cls, field_name, field_type):
            if not hasattr(cls, field_name):
                raise AttributeError(
                    f"Class `{cls.__name__}` lacks `{field_name}` class attribute"
                )
            if not getattr(cls, field_name):
                raise ValueError(
                    f"Class `{cls.__name__}` lacks `{field_name}` class attribute"
                )
            if not isinstance(getattr(cls, field_name), field_type):
                raise ValueError(
                    f"Class `{cls.__name__}` `{field_name}` class attribute must be of type {field_type}"
                )

        super().__init__(name, bases, props)

        if not ABC in bases:
            check_meta_fields(cls, "type", str)
            check_meta_fields(cls, "label", str)


class GraphComponent(
    dict, ABC, VisitSubclassesMixin, CreateInstanceMixin, metaclass=GraphComponentMeta
):
    __final_fields__: list[str] = ["type", "label", "extra_labels"]

    type: str = None
    label: str = None
    extra_labels: tuple[str] = ()

    def __init__(self, **kwargs):
        kwargs["type"] = self.type
        kwargs["label"] = self.label
        kwargs["extra_labels"] = self.extra_labels

        for key, value in kwargs.items():
            super().__setattr__(key, value)
            super().__setitem__(key, self.encode_dict_value(value))

    @classmethod
    def get_class(cls, type: str) -> Self:
        if cls.type == type:
            return cls

        for subclass in cls.visit_subclasses():
            if subclass.type == type:
                return subclass

        raise ValueError(f'Could not find class for type "{type}"')

    @property
    def labels(self):
        return {self.label, *self.extra_labels}

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__final_fields__:
            raise ValueError(f"Not allowed to set attribute {__name}")

        super().__setattr__(__name, __value)
        super().__setitem__(__name, self.encode_dict_value(__value))

    def encode_dict_value(self, value):
        if isinstance(value, type(GraphComponent)):
            return value.type
        return value

    @classmethod
    def from_dict(cls, dict: dict[str, Any]) -> Self:
        component_cls = cls.get_class(dict["type"])
        instance = component_cls.create_instance(**dict)
        return instance

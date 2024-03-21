class Entity(dict):
    __final_fields__ = ["type", "label"]

    def __init__(
        self,
        type: str,
        label: str | set[str],
        name: str,
        qualified_name: str,
        file_path: str,
        **kwargs,
    ):
        super().__init__(
            type=type,
            label=label,
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            **kwargs,
        )

    def __setitem__(self, key, value):
        if key in self.__final_fields__:
            raise ValueError("Cannot set type")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key in self.__final_fields__:
            return self.get(key)
        return super().__getitem__(key)

    # def __repr__(self):
    # return f"<Entity {self.get('type')} {self.get("qualified_name")}>"


class ModuleEntity(Entity):
    def __init__(self, name: str, qualified_name: str, file_path: str, **kwargs):
        super().__init__(
            type="module_ent",
            label="Module",
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            **kwargs,
        )


class ClassEntity(Entity):
    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        **kwargs,
    ):
        super().__init__(
            type="class_ent",
            label="Class",
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            **kwargs,
        )


class FunctionEntity(Entity):
    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        subtype: str,
        **kwargs,
    ):
        super().__init__(
            type="function_ent",
            label="Function",
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            subtype=subtype,
            **kwargs,
        )


class MethodEntity(FunctionEntity):
    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        class_name: str,
        class_qualified_name: str,
        subtype: str,
        **kwargs,
    ):
        super(Entity, self).__init__(
            type="method_ent",
            label=("Method", "Function"),
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            class_name=class_name,
            class_qualified_name=class_qualified_name,
            subtype=subtype,
            **kwargs,
        )


class VariableEntity(Entity):
    def __init__(
        self,
        name: str,
        qualified_name: str,
        file_path: str,
        access: str,
        **kwargs,
    ):
        super().__init__(
            type="variable_ent",
            label="Variable",
            name=name,
            qualified_name=qualified_name,
            file_path=file_path,
            access=access,
            **kwargs,
        )

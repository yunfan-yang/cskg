class VisitSubclassesMixin(object):
    @classmethod
    def visit_subclasses(cls):
        for subclass in cls.__subclasses__():
            yield subclass
            yield from subclass.visit_subclasses()

    @classmethod
    def get_subclasses(cls):
        return list(cls.visit_subclasses())


class CreateInstanceMixin(object):
    @classmethod
    def create_instance(cls, **kwargs):
        return cls(**kwargs)


class ExternalComponentMixin(object):
    EXTERNAL_LABEL = "External"

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if hasattr(cls, "type"):
            cls.type = "external_" + cls.type

        if hasattr(cls, "extra_labels"):
            cls.extra_labels = cls.extra_labels + (cls.EXTERNAL_LABEL,)

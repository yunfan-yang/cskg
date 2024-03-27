class VisitSubclassesMixin:
    @classmethod
    def visit_subclasses(cls):
        yield cls
        for subclass in cls.__subclasses__():
            yield from subclass.visit_subclasses()

    @classmethod
    def get_subclasses(cls):
        return list(cls.visit_subclasses())


class CreateInstanceMixin:
    @classmethod
    def create_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

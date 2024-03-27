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

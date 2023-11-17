from neomodel import config
from os import environ

from dotenv import load_dotenv
from neomodel import (
    config,
    StructuredNode,
    StringProperty,
    IntegerProperty,
    UniqueIdProperty,
    RelationshipTo,
)

load_dotenv()

config.DATABASE_URL = environ.get("NEO4J_URL")


class Country(StructuredNode):
    code = StringProperty(unique_index=True, required=True)


class City(StructuredNode):
    name = StringProperty(required=True)
    country = RelationshipTo(Country, "FROM_COUNTRY")


class Person(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True)
    age = IntegerProperty(index=True, default=0)

    # traverse outgoing IS_FROM relations, inflate to Country objects
    country = RelationshipTo(Country, "IS_FROM")

    # traverse outgoing LIVES_IN relations, inflate to City objects
    city = RelationshipTo(City, "LIVES_IN")


p1 = Person(name="John")
p1.save()

p2 = Person(name="Smith")
p2.save()

c1 = Country(code="IE")
c1.save()

p1.country.connect(c1)
p2.country.connect(c1)

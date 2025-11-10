from owlready2 import *

onto = get_ontology("http://semanticweb.org/example")


with onto:
    # Entities
    class Human(Thing):
        label = "Human"
        comment = "A human being"
        pass
    

    class hasSex(ObjectProperty):
        domain = [Human]
        range = [OneOf(["Male", "Female"])]

    class Profession(Thing):
        pass

    class hasProfession(Human >> Profession):
        pass
    

onto.save(file = "test.owl", format = "rdfxml")


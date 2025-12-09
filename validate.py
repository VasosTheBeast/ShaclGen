from pyshacl import validate
from rdflib import Graph
def shacl_validate(ont_graph, shapes,data_graph):
    conforms, _, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shapes,
    #ont_graph=ont_graph,
    #inference ="rdfs",
    )

    return conforms, results_text

if __name__ == "__main__":
    ont_graph = "examples/ontology.ttl"
    shapes = "shapes.ttl"
    data_graph = "examples/example.ttl"
   
    triples = """
    <http://www.cars.com#93f73f67-5658-451e-a0ba-9453cde0bf1a> <http://www.w3.org/2002/07/owl#versionInfo> "2025-12-01 15:05:43.633046"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#93f73f67-5658-451e-a0ba-9453cde0bf1a> <http://www.w3.org/2000/01/rdf-schema#label> "John"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#93f73f67-5658-451e-a0ba-9453cde0bf1a> <http://www.cars.com#hasUsername> "John"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#b5e02f3b-5cd7-4bb4-888b-309397b6c41f> <http://www.w3.org/2002/07/owl#versionInfo> "2025-12-01 15:05:43.633046"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#b5e02f3b-5cd7-4bb4-888b-309397b6c41f> <http://www.w3.org/2000/01/rdf-schema#label> "Tesla1"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#b5e02f3b-5cd7-4bb4-888b-309397b6c41f> <http://www.cars.com#hasColor> "Red"^^<http://www.w3.org/2001/XMLSchema#string> . <http://www.cars.com#b5e02f3b-5cd7-4bb4-888b-309397b6c41f> <http://www.cars.com#hasPrice> "-10000"^^<http://www.w3.org/2001/XMLSchema#integer> . <http://www.cars.com#93f73f67-5658-451e-a0ba-9453cde0bf1a> <http://www.cars.com#hasCar> <http://www.cars.com#b5e02f3b-5cd7-4bb4-888b-309397b6c41f> .
    """

    g = Graph()
    g.parse(data=triples, format="turtle")

    for a,b,c in g.triples((None, None, None)):
        print(a,b,c)
    
    ans, text= shacl_validate(ont_graph,shapes,g)

    if ans == False:
        print(f"SHACL validation failed", text)
    else:
        print("SHACL validation passed!")

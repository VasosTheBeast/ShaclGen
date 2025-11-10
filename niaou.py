from rdflib import Graph, RDF, RDFS, OWL, XSD, Namespace, BNode, Literal, URIRef

def load_graph(ttl_path):
    """
    Function that loads the ttl file to an rdflib graph
    """
    g = Graph()
    g.parse(ttl_path)#, format="turtle")
    return g


load_graph("ex.ttl")
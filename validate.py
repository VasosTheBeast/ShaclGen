from pyshacl import validate

def shacl_validate(ont_graph, shapes,data_graph):
    conforms, _, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shapes,
    ont_graph=ont_graph,
    inference ="rdfs",
    )

    return conforms, results_text

if __name__ == "__main__":
    ont_graph = "examples/ontology.ttl"
    shapes = "shapes.ttl"
    data_graph = "examples/example.ttl"

    ans, text= shacl_validate(ont_graph, shapes,data_graph)

    if ans == False:
        print(f"SHACL validation failed", text)
    else:
        print("SHACL validation passed!")

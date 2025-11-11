from rdflib import Graph, RDF, RDFS, OWL, XSD, Namespace, BNode, Literal, URIRef

SH = Namespace("http://www.w3.org/ns/shacl#")
def load_graph(ttl_path):
    """
    Function that loads the ttl file to an rdflib graph
    """
    g = Graph()
    g.parse(ttl_path)#, format="turtle")
    return g

def collect_classes(g):
    """
    Function that finds classes 
    """
    classes = set(g.subjects(RDF.type, OWL.Class)) | set(g.subjects(RDF.type, RDFS.Class))
    return classes

def collect_properties(g):
    """
    Function that finds all object and data properties
    """
    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    dt_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    return obj_props, dt_props

def find_property_domains_ranges(g, prop):
    """
    Function that finds property domains and ranges
    """
    domains = set(g.objects(prop, RDFS.domain))
    ranges = set(g.objects(prop, RDFS.range))
    return domains, ranges

def is_functional(g, prop):
    """
    Function that finds if a property is functional or not
    """
    return (prop, RDF.type, OWL.FunctionalProperty) in g or (prop, RDF.type, OWL.FunctionalProperty) in g

def find_inverse_props(g, prop):
    """
    Function that finds the inverse properties of a property if any 
    """
    invs = set(g.objects(prop, OWL.inverseOf)) | set(g.subjects(OWL.inverseOf, prop))
    return invs

def find_enumeration_values(g, node):
    """
    Function that collects the members of an owl:Class with owl:oneOf (a rdf:List).
    """
    vals = []
    for oneOf in g.objects(node, OWL.oneOf):
        # oneOf -> rdf:list (rdf:first/rdf:rest)
        current = oneOf
        while current and current != RDF.nil:
            firsts = list(g.objects(current, RDF.first))
            if firsts:
                vals.append(firsts[0])
            rests = list(g.objects(current, RDF.rest))
            current = rests[0] if rests else None
    return vals

def list_to_rdf_list(g, items):
    """
    Helper Function that makes an RDF collection list node for items and adds to graph g
    """
    if not items:
        return RDF.nil
    head = BNode()
    current = head
    for i, item in enumerate(items):
        g.add((current, RDF.first, item))
        if i == len(items) - 1:
            g.add((current, RDF.rest, RDF.nil))
        else:
            nxt = BNode()
            g.add((current, RDF.rest, nxt))
            current = nxt
    return head

def create_property_shape(shapes_g, path, info):
    """
    Function that creates a property shape (as a blank node) and attaches properties
    info dict.
    info may contain keys: 'datatype','class','minCount','maxCount','in' (list), 'hasValue'
    Returns the node representing the property shape.
    """
    # create Property Node for the property shape
    pshape = URIRef(f"{path}_PropertyShape")
    # the blank node has type of PropertyShape
    shapes_g.add((pshape, RDF.type, SH.PropertyShape))
    # add to the Property shape the path of the property
    shapes_g.add((pshape, SH.path, path))
    # if it is a dataproperty add it the the shape by using SH.datatype 
    if 'datatype' in info and info['datatype'] is not None:
        shapes_g.add((pshape, SH.datatype, info['datatype']))
    # if it is an object property add it to the shape by using SH["class"] (creates sh.class)
    if 'class' in info and info['class'] is not None:
        shapes_g.add((pshape, SH["class"], info['class']))
    # if property has minCount or maxCount add it to the shape 
    if 'minCount' in info:
        shapes_g.add((pshape, SH.minCount, Literal(info['minCount'], datatype=XSD.integer)))
    if 'maxCount' in info:
        shapes_g.add((pshape, SH.maxCount, Literal(info['maxCount'], datatype=XSD.integer)))
    # If property has minInclusicve or maxInclusive add it to the shape
    if 'minInclusive' in info:
        shapes_g.add((pshape, SH.minInclusive, Literal(info['minInclusive'], datatype=XSD.integer)))
    if 'maxInclusive' in info:
        shapes_g.add((pshape, SH.maxInclusive, Literal(info['maxInclusive'], datatype=XSD.integer)))
    if 'minLength' in info:
        shapes_g.add((pshape, SH.minLength, Literal(info['minLength'], datatype=XSD.integer)))
    if 'maxLength' in info:
        shapes_g.add((pshape, SH.maxLength, Literal(info['maxLength'], datatype=XSD.integer)))
    # If property has as range owl.oneOf, create an rdf:List of the list
    if 'in' in info and info['in']:
        # create an rdf:List for sh:in
        lst = list_to_rdf_list(shapes_g, info['in'])
        shapes_g.add((pshape, SH["in"], lst))

    return pshape

def generate_shacl_from_ontology(g):
    shapes = Graph()
    shapes.bind("sh", SH)
    shapes.bind("rdfs", RDFS)
    shapes.bind("owl", OWL)
    shapes.bind("xsd", XSD)

    # collect classes, object and data properties
    classes = collect_classes(g)
    obj_props, dt_props= collect_properties(g)
    all_props = obj_props | dt_props

    # For each class, create a NodeShape and add property shapes for properties that have this class as domain
    for cls in classes:
        # create a URI for the Node shape (e.g. Team_Shape)
        nshape = URIRef(f"{cls}_Shape")
        # the blank node is a NodeShape, which this class as the sh.targetClass
        shapes.add((nshape, RDF.type, SH.NodeShape))
        shapes.add((nshape, SH.targetClass, cls))

        # properties whose domain includes this class
        for p in all_props:
            # find the domains and ranges of the property
            domains, ranges = find_property_domains_ranges(g, p)
            # if the class is the domain of the porperty:
            if cls in domains:
                # build info for mapping
                info = {}
                print(f"Class '{cls.split("#")[-1]}' has property: '{p.split("#")[-1]}', with range: '{str(list(ranges)[0]).split("#")[-1]}'")              
                # required -> minCount 1
                required = None
                while required not in (["y", "n"]):
                    required = input("Do you want to make this property required? (y|n): ")
                if required == "y":
                    info['minCount'] = 1
                functional = None
                while functional not in (["y", "n"]):
                    functional = input("Do you want to make this property functional? (y|n): ")
                # functional -> maxCount 1
                if is_functional(g, p) or functional == 'y':
                    info['maxCount'] = 1
                # Range handling: choose first range if many
                if ranges:
                    r = next(iter(ranges))
                    # check if this range node *defines* an enumeration
                    enum_vals = find_enumeration_values(g, r)
                    # if it does then add it using sh:in
                    if enum_vals:
                        # prefer sh:in with the enumerated values
                        info['in'] = enum_vals

                    else:
                        # original handling: if r is a class -> sh:class, else treat as datatype (heuristic)
                        if (r, RDF.type, OWL.Class) in g or (r, RDF.type, RDFS.Class) in g:
                            info['class'] = r
                        # else the range is a literal
                        else:
                            # range is a datatype
                            info['datatype'] = r
                            # Range: Integer -> set bottom/upper limit (min/maxInclusive)
                            if r == XSD.integer:
                                f = None
                                while f not in ["y", "n"]:
                                    f = input("Do you want to set a bottom and an upper limit for this property? (y|n): ")
                                if f == 'y':
                                    min_limit = input("Set bottom limit (included): ")                                   
                                    max_limit = input("Set upper limit (included): ")
                                    info['minInclusive'] = int(min_limit)
                                    info['maxInclusive'] = int(max_limit)
                            # Range: String -> set min/max Length
                            elif r == XSD.string:
                                f = None
                                while f not in ["y", "n"]:
                                    f = input("Do you want to set a minumum and a maximum length of characters for this property? (y|n): ")
                                if f == 'y':
                                    min_limit = input("Set minimum length: ")                                   
                                    max_limit = input("Set maximum length: ")
                                    info['minLength'] = int(min_limit)
                                    info['maxLength'] = int(max_limit)
                                    
                            
                
                # for this property create property shape and add it to the Shapes Graph 
                pshape = create_property_shape(shapes, p, info)
                # connect the NodeShape with the Property Shape we created
                shapes.add((nshape, SH.property, pshape))

    return shapes
def main():
    input_ttl = "examples/ontology.ttl"
    output_ttl = "shapes.ttl"
    g = load_graph(input_ttl)
    print("Loaded ontology. Triples:", len(g))
    #for (s,p,o) in g.triples((None,None,None)):
    #   print(s,p,o)
    shapes = generate_shacl_from_ontology(g)
    shapes.serialize(destination=output_ttl, format="turtle")
    print("Wrote SHACL shapes to", output_ttl)

main()
from rdflib import Graph, RDF, RDFS, OWL, XSD, BNode, Literal, URIRef, SH, Namespace

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

#def find_ontology_prefix():


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
    # If property has minInclusi or maxInclusive add it to the shape
    if 'minInclusive' in info:
        shapes_g.add((pshape, SH.minInclusive, info['minInclusive']))
    if 'maxInclusive' in info:
        shapes_g.add((pshape, SH.maxInclusive, info['maxInclusive']))
    if 'minLength' in info:
        shapes_g.add((pshape, SH.minLength, info['minLength']))
    if 'maxLength' in info:
        shapes_g.add((pshape, SH.maxLength, info['maxLength']))
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
    # find ontology prefix
    if classes:
        ex_class = next(iter(classes))
        ontology_prefix = str(ex_class).rsplit("#",1)[0] + "#"
        # bind prefix
        shapes.bind("ex", Namespace(ontology_prefix))
    # collect object and data properties
    obj_props, dt_props= collect_properties(g)
    all_props = obj_props | dt_props

    # dictionary with: fullIRI -> clean property name
    properties_cleand = {}
    for pr in all_props:
        properties_cleand[pr] = pr.split("#")[-1]  
    
    properties_cleand_inverse = {v: k for k, v in properties_cleand.items()} # clean property name : fullIRI
   
    # dicitonary that holds: full_property_IRi -> info dictionary (which is used later to create the property shape)
    property_dict = {}
    # For each class, create a NodeShape and add property shapes for properties that have this class as domain
    for cls in classes:
        # create a URI for the Node shape (e.g. Team_Shape)
        nshape = URIRef(f"{cls}_Shape")
        # add rdf type sh:NodeShape
        shapes.add((nshape, RDF.type, SH.NodeShape))
        # add sh:targetClass pointing to the class
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
                # if the property is functional add maxCount = 1
                if is_functional(g, p):
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
                # store property info                     
                property_dict[p] = info
                # for this property create property shape and add it to the Shapes Graph 
                pshape = create_property_shape(shapes, p, info)
                # connect the NodeShape with the Property Shape we created
                shapes.add((nshape, SH.property, pshape))

    selected_property = None
    # Let the user input the name of the property that they want to add shacl rules to:
    while selected_property not in ["exit", "end"]:
        selected_property = input(f"Select a property you want to add contraint rules. Type 'exit' or 'end' to exit. Avaliable properties: {list(properties_cleand.values())}: ")
        if selected_property in list(properties_cleand.values()):
            full_property = properties_cleand_inverse.get(selected_property)
            # find property's domain and range
            domains, ranges = find_property_domains_ranges(g, full_property)
            print(f"Property {selected_property}. has Domain: {str(list(domains)[0]).split("#")[-1]} and range: {str(list(ranges)[0]).split("#")[-1]}")
            # ask user if they want to make the property required (minCount = 1)
            required = None
            while required not in (["y", "n"]):
                required = input("Do you want to make this property required? (y|n): ")
            if required == "y":
                property_dict[full_property]['minCount'] = 1
            # ask the user if they want to make the property functional (maxCount = 1)
            functional = None
            while functional not in (["y", "n"]):
                functional = input("Do you want to make this property functional? (y|n): ")
                if functional == 'y':
                        property_dict[full_property]['maxCount'] = 1
            # check if the property is a Dataproperty (range is not a class neither a Blank Node)
            r = next(iter(ranges))
            # integer -> set min max boundaries
            if r == XSD.integer:
                f = None
                while f not in ["y", "n"]:
                    f = input("Do you want to set a bottom and an upper limit for this property? (y|n): ")
                if f == 'y':
                    min_limit = input("Set bottom limit (included): ")                                   
                    max_limit = input("Set upper limit (included): ")
                    property_dict[full_property]['minInclusive'] = Literal(int(min_limit), datatype=XSD.integer)
                    property_dict[full_property]['maxInclusive'] = Literal(int(max_limit), datatype=XSD.integer)
            # Range: String -> set min/max string Length
            elif r == XSD.string:
                f = None
                while f not in ["y", "n"]:
                    f = input("Do you want to set a minumum and a maximum length of characters for this property? (y|n): ")
                if f == 'y':
                    min_limit = input("Set minimum length: ")                                   
                    max_limit = input("Set maximum length: ")
                    property_dict[full_property]['minLength'] = Literal(int(min_limit), datatype=XSD.integer)
                    property_dict[full_property]['maxLength'] = Literal(int(max_limit), datatype=XSD.integer)
            # Range: Date -> set min/max dates
            elif r == XSD.date:
                f = None
                while f not in ["y", "n"]:
                    f = input("Do you want to add date boundaries? (y|n):")
                if f == 'y':
                    min_date = input("Set minimum date (YYYY-MM-dd): ")
                    max_date = input("Set maximum date (YYYY-MM-dd): ")
                    property_dict[full_property]['minInclusive'] = Literal(min_date, datatype=XSD.date)
                    property_dict[full_property]['maxInclusive'] = Literal(max_date, datatype=XSD.date) 
            # finally create the property shape                
            pshape = create_property_shape(shapes, full_property, property_dict[full_property])     

    return shapes
def main():
    input_ontology = "examples/ontology.ttl"
    output_ttl = "shapes2.ttl"
    g = load_graph(input_ontology)
    print("Loaded ontology. Triples:", len(g))

    shapes = generate_shacl_from_ontology(g)
    shapes.serialize(destination=output_ttl, format="turtle")
    print("Wrote SHACL shapes to", output_ttl)

if __name__ == "__main__":
    main()

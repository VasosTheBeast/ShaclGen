# SHACL Validation in CASPAR

CASPAR allows users to automatically generate **SHACL validation shapes** from an uploaded ontology.  
This enhances data quality by validating instances against the generated SHACL constraints.

---

## 🔁 Workflow Overview

1. **User uploads a JSON file**  
   → CASPAR converts it into an OWL ontology.

2. **User selects “Generate SHACL Shapes”**  
   → A first draft of a `shapes.ttl` file is automatically created.

3. **Initial version of the SHACL file includes:**  
   - Basic **NodeShapes**  
   - Basic **PropertyShapes**

---

## 🧱 Generated NodeShapes

For each class in the ontology, CASPAR creates a `sh:NodeShape` with:

- `sh:targetClass` → the class itself  
- `sh:property` → all properties for which this class is the **domain**

---

## 🔧 Generated PropertyShapes

For each property in the ontology, CASPAR creates a corresponding `sh:PropertyShape` with:

### Datatype Properties
- `sh:path` → the property  
- `sh:datatype` → datatype from `rdfs:range`  
  (e.g., `xsd:string`, `xsd:integer`)

### Object Properties
- `sh:path` → the property  
- `sh:class` → the class defined in the `rdfs:range`

---

## 🧬 Example

### Ontology

```ttl
ex:Person a owl:Class .
ex:Job a owl:Class .

ex:hasAge a owl:DatatypeProperty ;
    rdfs:domain ex:Person ;
    rdfs:range xsd:integer .

ex:hasName a owl:DatatypeProperty ;
    rdfs:domain ex:Person ;
    rdfs:range xsd:string .

ex:hasJob a owl:ObjectProperty ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Job .
```

---

### Generated SHACL Shapes

```ttl
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://www.example.org#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:PersonShape a sh:NodeShape ;
  sh:targetClass ex:Person ;
  sh:property ex:hasAgeShape ;
  sh:property ex:hasNameShape ;
  sh:property ex:hasJobShape .

ex:JobShape a sh:NodeShape ;
  sh:targetClass ex:Job .

ex:hasAgeShape a sh:PropertyShape ;
  sh:path ex:hasAge ;
  sh:datatype xsd:integer .

ex:hasNameShape a sh:PropertyShape ;
  sh:path ex:hasName ;
  sh:datatype xsd:string .

ex:hasJobShape a sh:PropertyShape ;
  sh:path ex:hasJob ;
  sh:class ex:Job .
```

---

## ✏️ User-Defined Refinements

Users can edit PropertyShapes to add additional constraints:

### Common Constraints
- **Required** → `sh:minCount 1`
- **Functional** → `sh:maxCount 1`

### Datatype-Specific Constraints

#### Integers: Number boundaries
- `sh:minInclusive`
- `sh:maxInclusive`  
  Example: Allowed range `0–100`

#### Strings: Minimum - Maximum characters allowed
- `sh:minLength`
- `sh:maxLength`

#### Dates: Date boundaries
- `sh:minInclusive`  
- `sh:maxInclusive`

---

## Validate a data graph
- validate.py script lets you validate an example data graph using the creates shape graph.
- Optionally you can add the ontology file with inferencing if you want inference to be amde before validating your data.

## 🚀 Future Improvements

- Interactive UI for selecting constraints  
  (e.g., choose min/max bounds through the interface)
- Validation and safety checks  
  - Ensure `maxLength ≥ minLength`
  - Ensure numeric/date ranges are consistent
- Add **SPARQL-based SHACL constraints** based on natural language user prompts (LLM-powered)

---


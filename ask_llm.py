from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")


def constraint_generator(ontology_file, shacl_shapes,user_prompt):

    with open(ontology_file, 'r') as file:
        ontology_content = file.read()
    
    with open(shacl_shapes, 'r') as file:
        shacl_content = file.read()

    client = genai.Client(api_key=API_KEY)

    system_prompt = f"""
    You are an expert in Semantic Web and SHACL SPARQL constraints.

     Task:
        - Given a natural language requirement, generate a SHACL SPARQL constraint that enforces the requirement.
        - Use the ontology provided to inform your constraint generation.
        - Return only the generated SHACL SPARQL constraint - no explanations - no markdown - no commentary
    
    Example user input: Ensure home and away team of a match are different

    Example SPARQL constraint:
    ex:MatchShape
    a sh:NodeShape ;
    sh:targetClass ex:Match ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "Home and away teams must be different." ; 
        sh: prefixes ex: ;
        sh:select \"""
            SELECT $this
            WHERE {{
              $this ex:homeTeam ?team1 ;
                      ex:awayTeam ?team2 .
                FILTER(?team1 = ?team2)
            }}
        \""" ;
    ] 

    Here is the actual ontology:
    {ontology_file}

    And here are the existing SHACL shapes:
    {shacl_content}
    """
    
    config = types.GenerateContentConfig(system_instruction=system_prompt)

    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages,
        config=config
    )

    if not response or not response.candidates:
        return "Could not generate SPARQL."
    
    print(response.candidates[0].content.parts[0].text.strip())


if __name__ == "__main__":
    ontology_file = "examples/ontology.ttl"
    
    shacl_shapes = "shapes.ttl"
    user_prompt = "Every User must have an id greater than 2 in order to have a car"
    

    constraint_generator(ontology_file, shacl_shapes, user_prompt)
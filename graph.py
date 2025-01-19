from operator import add
from typing import Annotated, List

from typing_extensions import TypedDict
from langchain_neo4j import Neo4jGraph

from llm import llm

kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizzaentire10"
enhanced_graph = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name,enhanced_schema=True)

class InputState(TypedDict):
    question: str


class OverallState(TypedDict):
    question: str
    next_action: str
    cypher_statement: str
    cypher_errors: List[str]
    database_records: List[dict]
    steps: Annotated[List[str], add]


class OutputState(TypedDict):
    answer: str
    steps: List[str]
    cypher_statement: str

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

guardrails_system = """
As an intelligent assistant, your primary objective is to decide whether a given question is related to movies or not. 
If the question is related to movies, output "movie". Otherwise, output "end".
To make this decision, assess the content of the question and determine if it refers to any movie, actor, director, film industry, 
or related topics. Provide only the specified output: "movie" or "end".
"""
guardrails_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            guardrails_system,
        ),
        (
            "human",
            ("{question}"),
        ),
    ]
)


class GuardrailsOutput(BaseModel):
    decision: Literal["movie", "end"] = Field(
        description="Decision on whether the question is related to movies"
    )


guardrails_chain = guardrails_prompt | llm.with_structured_output(GuardrailsOutput)


def guardrails(state: InputState) -> OverallState:
    """
    Decides if the question is related to movies or not.
    """
    guardrails_output = guardrails_chain.invoke({"question": state.get("question")})
    database_records = None
    if guardrails_output.decision == "end":
        database_records = "This questions is not about movies or their cast. Therefore I cannot answer this question."
    return {
        "next_action": guardrails_output.decision,
        "database_records": database_records,
        "steps": ["guardrail"],
    }


from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_neo4j import Neo4jVector, Neo4jGraph
from langchain_openai import OpenAIEmbeddings

examples = [
    {
        "question": "Quali sono i piatti che includono le Chocobo Wings come ingrediente?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i:Ingrediente {nome: 'Chocobo Wings'}) RETURN p.nome",
    },
    {
        "question": "Quali sono i piatti che includono i Sashimi di Magikarp?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i:Ingrediente {nome: 'Sashimi di Magikarp'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti sono accompagnati dai misteriosi Frutti del Diavolo, che donano poteri speciali a chi li consuma?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i:Ingrediente {nome: 'Frutti del Diavolo'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti preparati con la tecnica Grigliatura a Energia Stellare DiV?",
        "query": "MATCH (p:Piatto)-[:PREPARATO_CON]->(t:Tecnica {nome: 'Grigliatura a Energia Stellare DiV'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti sono preparati utilizzando la tecnica della Sferificazione a Gravità Psionica Variabile?",
        "query": "MATCH (p:Piatto)-[:PREPARATO_CON]->(t:Tecnica {nome: 'Sferificazione a Gravità Psionica Variabile'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti eterei sono preparati usando sia la Cottura Olografica Quantum Fluttuante che la Decostruzione Interdimensionale Lovecraftiana?",
        "query": "MATCH (p:Piatto)-[:PREPARATO_CON]->(t1:Tecnica {nome: 'Cottura Olografica Quantum Fluttuante'}), (p)-[:PREPARATO_CON]->(t2:Tecnica {nome: 'Decostruzione Interdimensionale Lovecraftiana'}) RETURN p.nome",
    },
    {
        "question": "Quali sono i piatti che combinano la saggezza del Riso di Cassandra e l'intrigante tocco della Polvere di Crononite?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i1:Ingrediente {nome: 'Riso di Cassandra'}), (p)-[:CONTIENTE]->(i2:Ingrediente {nome: 'Polvere di Crononite'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti della galassia contengono Latte+?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i:Ingrediente {nome: 'Latte+'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti contengono i Ravioli al Vaporeon?",
        "query": "MATCH (p:Piatto)-[:CONTIENTE]->(i:Ingrediente {nome: 'Ravioli al Vaporeon'}) RETURN p.nome",
    },
    {
        "question": "Quali piatti sono preparati sia con la Marinatura Temporale Sincronizzata che con il Congelamento Bio-Luminiscente Sincronico?",
        "query": "MATCH (p:Piatto)-[:PREPARATO_CON]->(t1:Tecnica {nome: 'Marinatura Temporale Sincronizzata'}), (p)-[:PREPARATO_CON]->(t2:Tecnica {nome: 'Congelamento Bio-Luminiscente Sincronico'}) RETURN p.nome",
    },
]


example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples, OpenAIEmbeddings(), Neo4jVector, k=5, input_keys=["question"]
)

from langchain_core.output_parsers import StrOutputParser

text2cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Given an input question, convert it to a Cypher query. No pre-amble."
                "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
            ),
        ),
        (
            "human",
            (
                """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
Here are the graph information
  "nodes_labels": [
    "Piatto",
    "Ingrediente",
    "Tecnica",
    "Ristorante",
    "Pianeta",
    "Chef",
    "Licenza",
    "Ordine"
  ],
  "relationships": [
    ("Piatto", "CONTIENE_INGREDIENTE", "Ingrediente"),
    ("Piatto", "APPLICA_TECNICA", "Tecnica"),
    ("Piatto", "SERVITO_IN", "Ristorante"),
    ("Ristorante", "LOCALIZZATO_SU", "Pianeta"),
    ("Piatto", "PREPARATO_DA", "Chef"),
    ("Chef", "HA_LICENZA", "Licenza"),
    ("Chef", "APPARTIENE_ORDINE", "Ordine"),
    ("Pianeta", "DISTA_DA", "Pianeta")
  ],
  "node_properties": [
    "nome",
    "descrizione",
    "quantita",
    "unita_di_misura",
    "leggendario",
    "categoria",
    "principi_fondamentali",
    "livello"
  ],
  "relationship_properties": [
    "descrizione",
      "quantitaUtilizzata",
      "unitaDiMisura",
      "distanzaInAnniLuce",
      "gradoRichiesto",
      "certificazioniRichieste",
      "dataInizio",
      "dataFine",
      "condizioniParticolari"

  ]

Below are a number of examples of questions and their corresponding Cypher queries.

{fewshot_examples}

User input: {question}
Cypher query:"""
            ),
        ),
    ]
)

text2cypher_chain = text2cypher_prompt | llm | StrOutputParser()


def generate_cypher(state: OverallState) -> OverallState:
    """
    Generates a cypher statement based on the provided schema and user input
    """
    NL = "\n"
    fewshot_examples = (NL * 2).join(
        [
            f"Question: {el['question']}{NL}Cypher:{el['query']}"
            for el in example_selector.select_examples(
                {"question": state.get("question")}
            )
        ]
    )
    generated_cypher = text2cypher_chain.invoke(
        {
            "question": state.get("question"),
            "fewshot_examples": fewshot_examples,
            "schema": enhanced_graph.schema,
        }
    )
    return {"cypher_statement": generated_cypher, "steps": ["generate_cypher"]}


from typing import List, Optional

validate_cypher_system = """
You are a Cypher expert reviewing a statement written by a junior developer.
"""

validate_cypher_user = """You must check the following:
* Are there any syntax errors in the Cypher statement?
* Are there any missing or undefined variables in the Cypher statement?
* Are any node labels missing from the schema?
* Are any relationship types missing from the schema?
* Are any of the properties not included in the schema?
* Does the Cypher statement include enough information to answer the question?

Examples of good errors:
* Label (:Foo) does not exist, did you mean (:Bar)?
* Property bar does not exist for label Foo, did you mean baz?
* Relationship FOO does not exist, did you mean FOO_BAR?

Schema:
{schema}

The question is:
{question}

The Cypher statement is:
{cypher}

Make sure you don't make any mistakes!"""

validate_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            validate_cypher_system,
        ),
        (
            "human",
            (validate_cypher_user),
        ),
    ]
)


class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")
    property_value: str = Field(
        description="The value that the property is being matched against."
    )


class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )


validate_cypher_chain = validate_cypher_prompt | llm.with_structured_output(
    ValidateCypherOutput
)

from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema

# Cypher query corrector is experimental
corrector_schema = [
    Schema(el["start"], el["type"], el["end"])
    for el in enhanced_graph.structured_schema.get("relationships")
]
cypher_query_corrector = CypherQueryCorrector(corrector_schema)

from neo4j.exceptions import CypherSyntaxError


def validate_cypher(state: OverallState) -> OverallState:
    """
    Validates the Cypher statements and maps any property values to the database.
    """
    errors = []
    mapping_errors = []
    # Check for syntax errors
    try:
        enhanced_graph.query(f"EXPLAIN {state.get('cypher_statement')}")
    except CypherSyntaxError as e:
        errors.append(e.message)
    # Experimental feature for correcting relationship directions
    corrected_cypher = cypher_query_corrector(state.get("cypher_statement"))
    if not corrected_cypher:
        errors.append("The generated Cypher statement doesn't fit the graph schema")
    if not corrected_cypher == state.get("cypher_statement"):
        print("Relationship direction was corrected")
    # Use LLM to find additional potential errors and get the mapping for values
    llm_output = validate_cypher_chain.invoke(
        {
            "question": state.get("question"),
            "schema": enhanced_graph.schema,
            "cypher": state.get("cypher_statement"),
        }
    )
    if llm_output.errors:
        errors.extend(llm_output.errors)
    if llm_output.filters:
        for filter in llm_output.filters:
            # Do mapping only for string values
            if (
                not [
                    prop
                    for prop in enhanced_graph.structured_schema["node_props"][
                        filter.node_label
                    ]
                    if prop["property"] == filter.property_key
                ][0]["type"]
                == "STRING"
            ):
                continue
            mapping = enhanced_graph.query(
                f"MATCH (n:{filter.node_label}) WHERE toLower(n.`{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
                {"value": filter.property_value},
            )
            if not mapping:
                print(
                    f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
                )
                mapping_errors.append(
                    f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
                )
    if mapping_errors:
        next_action = "end"
    elif errors:
        next_action = "correct_cypher"
    else:
        next_action = "execute_cypher"

    return {
        "next_action": next_action,
        "cypher_statement": corrected_cypher,
        "cypher_errors": errors,
        "steps": ["validate_cypher"],
    }

correct_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a Cypher expert reviewing a statement written by a junior developer. "
                "You need to correct the Cypher statement based on the provided errors. No pre-amble."
                "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
            ),
        ),
        (
            "human",
            (
                """Check for invalid syntax or semantics and return a corrected Cypher statement.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not wrap the response in any backticks or anything else.
Respond with a Cypher statement only!

Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

The question is:
{question}

The Cypher statement is:
{cypher}

The errors are:
{errors}

Corrected Cypher statement: """
            ),
        ),
    ]
)

correct_cypher_chain = correct_cypher_prompt | llm | StrOutputParser()


def correct_cypher(state: OverallState) -> OverallState:
    """
    Correct the Cypher statement based on the provided errors.
    """
    corrected_cypher = correct_cypher_chain.invoke(
        {
            "question": state.get("question"),
            "errors": state.get("cypher_errors"),
            "cypher": state.get("cypher_statement"),
            "schema": enhanced_graph.schema,
        }
    )

    return {
        "next_action": "validate_cypher",
        "cypher_statement": corrected_cypher,
        "steps": ["correct_cypher"],
    }

no_results = "I couldn't find any relevant information in the database"


def execute_cypher(state: OverallState) -> OverallState:
    """
    Executes the given Cypher statement.
    """

    records = enhanced_graph.query(state.get("cypher_statement"))
    return {
        "database_records": records if records else no_results,
        "next_action": "end",
        "steps": ["execute_cypher"],
    }

generate_final_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant ready to solve user queries",
        ),
        (
            "human",
            (
                """Use the following results retrieved from a database to provide
a succinct, definitive answer to the user's question.

Respond as if you are answering the question directly.
Do not invent, nor add any additional information. Stick with the results you are given!

Results: {results}
Question: {question}"""
            ),
        ),
    ]
)

generate_final_chain = generate_final_prompt | llm | StrOutputParser()


def generate_final_answer(state: OverallState) -> OutputState:
    """
    Decides if the question is related to movies.
    """
    final_answer = generate_final_chain.invoke(
        {"question": state.get("question"), "results": state.get("database_records")}
    )
    return {"answer": final_answer, "steps": ["generate_final_answer"]}

def guardrails_condition(
    state: OverallState,
) -> Literal["generate_cypher", "generate_final_answer"]:
    if state.get("next_action") == "end":
        return "generate_final_answer"
    elif state.get("next_action") == "movie":
        return "generate_cypher"


def validate_cypher_condition(
    state: OverallState,
) -> Literal["generate_final_answer", "correct_cypher", "execute_cypher"]:
    if state.get("next_action") == "end":
        return "generate_final_answer"
    elif state.get("next_action") == "correct_cypher":
        return "correct_cypher"
    elif state.get("next_action") == "execute_cypher":
        return "execute_cypher"

from langgraph.graph import END, START, StateGraph

langgraph = StateGraph(OverallState, input=InputState, output=OutputState)
langgraph.add_node(generate_cypher)
langgraph.add_node(validate_cypher)
langgraph.add_node(correct_cypher)
langgraph.add_node(execute_cypher)
langgraph.add_node(generate_final_answer)

langgraph.add_edge(START, "generate_cypher")
langgraph.add_edge("generate_cypher", "validate_cypher")
langgraph.add_conditional_edges(
    "validate_cypher",
    validate_cypher_condition,
)
langgraph.add_edge("execute_cypher", "generate_final_answer")
langgraph.add_edge("correct_cypher", "validate_cypher")
langgraph.add_edge("generate_final_answer", END)

langgraph = langgraph.compile()

import pandas as pd
import json

# Read the CSV file without headers
df = pd.read_csv("domande.csv", header=0, names=["domanda"])

for index, row in df.iterrows():
    input_data = {"question": row["domanda"]}
    output = langgraph.invoke(input_data)
    print(output)


import json
import os
from getpass import getpass
from typing import List

from dotenv import load_dotenv
from langchain.agents import create_react_agent, create_tool_calling_agent, AgentExecutor
from langchain.chat_models import init_chat_model
from langchain_core.messages.tool import tool_call
from langchain_core.tools import tool
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import SearchType, remove_lucene_chars
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from blue_vector_db import BlueVectorDatabase
from ingestion import graph_params
from llm import llm

#from ingestion import graph_params


load_dotenv()
class Entities(BaseModel):
    """Identifying information about entities."""

    names: str = Field(
        ...,
        description=f"The entity name that appear in the text",
    )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"You have to extract one of the following entities:\n <entities>\n{graph_params["allowed_nodes"]}\n<7entities> from the user question."
            f"For example, for a question like 'Qual è il piatto più famoso di Marte?' you should extract as entity: 'Piatto'."
            f"For example, for a question like 'Quali piatti hanno carne di kraken?' you should extract as entity: 'Ingrediente'."
            f"For example, for a question like 'Quali piatti sono serviti dal ristorante 'La Tana del Lupo'?' you should extract as entity: 'Ristorante'.",
        ),
        (
            "human",
            "input: {question}",
        ),
    ]
)

entity_chain = prompt | llm.with_structured_output(Entities)

#
#
# vector_index = Neo4jVector.from_existing_graph(
#     OpenAIEmbeddings(),
#     search_type=SearchType.HYBRID,
#     node_label="Piatto",
#     text_node_properties=["text"],
#     embedding_node_property="embedding"
# )
kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizzaentire10"
graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)

graph_db.query(
    "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspelings.
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

class Query(BaseModel):
    query: str = Field(
        ...,
        description="The Cypher query to be executed",
    )

# Fulltext index query
def structured_retriever(question: str):
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    entity = entity_chain.invoke({"question": question})
    prompt_ = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a top level Neo4j developer able to write the best Cypher queries starting from a user question in natural language."),
            ("human", "Write a case insensitive Cypher query to answer the following question:\n<question>{question}</question>\ntaking into account the following entity from which start the graph search:\n<entity>{entity}</entity>."
                      "To better create the query take into account that the graph supports the following Node Labels:\n<labels>\n{labels}\n</labels> and the following relationships:\n<relationships>{relationships}\n</relationships>."
                      "Always remember to use 'id' key instead of others like 'name', 'title' etc. to identify the nodes."
                      "Always remember to use human readable names for the results of the query"),
        ]
    )
    chain_ = prompt_ | llm.with_structured_output(Query)
    query = chain_.invoke({
        "question": question,
        "entity": entity.names,
        "labels": graph_params["allowed_nodes"],
        "relationships": graph_params["allowed_relationships"],
    })
    result = graph_db.query(query.query)
    return result

def retriever(question: str):
    print(f"Search query: {question}")
    structured_data = structured_retriever(question)
    # unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
    final_data = f"""These are the results obtained from the knowledge graph to answer the user question:
{structured_data}
    """
    return final_data

template = """Answer in italian the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)


_search_query = RunnableLambda(lambda x : x["question"])


class Response(BaseModel):
    """Response to a question."""

    piatti: List[str] = Field(
        ...,
        description="The list of dishes to solve the user query",
    )

llm_structured = llm.with_structured_output(Response)
chain = (
    RunnableParallel(
        {
            "context": _search_query | retriever,
            "question": RunnablePassthrough(),
        }
    )
    | prompt
    | llm_structured
)
final_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant very good at understanding user needs and generating plans to solve user queries."
            "Your task is to analyze the user query and generate a plan to solve the user query based on the context provided."
            "The plan should actually be made of a simple list of queries to run on the knowledge graph to obtain the final result"
            "You have access to a graph with the following informations:"
            "Node Labels: {labels}"
            "Relationships: {relationships}"
            "Node properties: {properties}"
            "ANSWER WITH ONLY THE QUERIES AND DO NOT INVENT ANYTHING!"
        ),
        (
            "human",
            "{question}"
        ),

        # Placeholders fill up a **list** of messages
        ("placeholder", "{agent_scratchpad}"),
    ]
)
blueVectorDbInstance = BlueVectorDatabase()
unstructured_retriever = blueVectorDbInstance.load_vector_db(
    index_path="./faiss_index",
    embedding_model=OpenAIEmbeddings(model="text-embedding-3-large"),
    vector_db_type="FAISS")

@tool("get_info_from_knowledge_graph")
def get_info_from_knowledge_graph(question: str):
    """
    This tool retrieves information from the knowledge graph based on a user question
    and returns the result in a structured format

    Args:
        ''question'': The user question to be answered
    """
    structured_output = structured_retriever(question)

    unstructured_output = unstructured_retriever.invoke(question)

    return {
        "response_from_knowledge_graph": structured_output,
        "response_from_vector_db": unstructured_output
    }
class Plan(BaseModel):
    """A plan to solve the user query."""

    queries: List[str] = Field(
        ...,
        description="The list of Cypher queries to solve the user query",
    )
plan_chain = final_prompt | llm.with_structured_output(Plan)
answer_generator_chain = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that provide a complete and final answer to the user given a set of informations."
            "DO NOT INVENT DATA, JUST SUMMARIZE THE RESULTS FROM THE QUERIES"
        ),
        (
            "human",
            "Given the following question:"
            "<question>{question}</question>"
            "Analyze generated queries and relative results:"
            "<queries>{queries}</queries>"
            "<results>{results}</results>"
            "and finally, provide a final answer to the user."
        )
    ]
) | llm.with_structured_output(Response)
# Step 6: Input data and run the chain
import pandas as pd
import json

# Read the CSV file without headers
df = pd.read_csv("domande.csv", header=0, names=["domanda"])

# Create or overwrite the results CSV file with headers
with open("risultati3_3.csv", "w") as f:
    f.write("row_id,result\n")
# Load the dish mapping JSON file
with open("dish_mapping.json", "r") as f:
    map_json = json.load(f)

map_json_lower = {key.lower(): value for key, value in map_json.items()}

# Iterate over each row in the dataframe
for index, row in df.iterrows():
    input_data = {"question": row["domanda"], "labels": graph_params["allowed_nodes"], "relationships": graph_params["allowed_relationships"], "properties": graph_params["node_properties"]}
    plan = plan_chain.invoke(input_data)
    answers = []
    for query in plan.queries:
        try:
            query_result = graph_db.query(query)
            answers.append(query_result)
        except Exception as e:
            print(f"Error executing query: {query}")
    output = answer_generator_chain.invoke({"queries": plan.queries, "results": answers, "question": row["domanda"]})

    # Collect dish IDs
    dish_ids = []
    for dish in output.piatti:
        dish_id = str(map_json_lower.get(dish.lower(), ""))
        if dish_id is not None and dish_id != "":
            dish_ids.append(dish_id)
    # Write the result to the results CSV file
    result = ",".join(dish_ids)
    with open("risultati3_3.csv", "a") as f:
        f.write(f"{index},\"{result}\"\n")

    # print(output)

# input_data = {"question": "Quali piatti contengono carne di kraken?"}  # Example input
# output = chain.invoke(input_data)
# print(output)

#

# agent_executor = AgentExecutor(agent=agent, tools=[get_info_from_knowledge_graph])
#
#
# retrieval_chain = final_prompt | agent
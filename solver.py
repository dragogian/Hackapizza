import json
import os
from getpass import getpass
from typing import List

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_community.vectorstores.neo4j_vector import SearchType, remove_lucene_chars
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

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
kg_db_name = "hackapizzagptfixed"
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
                      "Always remember to use 'id' key instead of others like 'name', 'title' etc. to identify the nodes."),
        ]
    )
    chain_ = prompt_ | llm.with_structured_output(Query)
    query = chain_.invoke({
        "question": question,
        "entity": entity.names,
        "labels": graph_params["allowed_nodes"],
        "relationships": graph_params["allowed_relationship"],
    })
    result = graph_db.query(query.query)
    return result

def retriever(question: str):
    print(f"Search query: {question}")
    structured_data = structured_retriever(question)
    # unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
    final_data = f"""Data:
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
        description="The list of dishes",
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

# Step 6: Input data and run the chain
# import pandas as pd
#
# df = pd.read_csv("domande.csv")
#
# for index, row in df.iterrows():
#     if index == 0:
#         continue
#     input_data = {"question": row}  # Example input
#     output = chain.invoke(input_data)
#     map_json = json.load("dish_mapping.json")
#     for dish in output.piatti:
#         map_json[dish] = row
#     with open("risultati.csv", "w+") as f:
#
#
#         f.write(f"{row}, {output}\n")


    # print(output)

input_data = {"question": "Quali piatti contengono carne di kraken?"}  # Example input
output = chain.invoke(input_data)
print(output)
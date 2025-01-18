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
from sympy.physics.units import temperature

#from ingestion import graph_params

load_dotenv()
# watsonx_api_key = getpass()
# os.environ["WATSONX_APIKEY"] = watsonx_api_key

# os.environ["WATSONX_URL"] = "your service instance url"
# os.environ["WATSONX_TOKEN"] = "your token for accessing the CPD cluster"
# os.environ["WATSONX_PASSWORD"] = "your password for accessing the CPD cluster"
# os.environ["WATSONX_USERNAME"] = "your username for accessing the CPD cluster"
# os.environ["WATSONX_INSTANCE_ID"] = "your instance_id for accessing the CPD cluster"

llm = ChatOpenAI(model="gpt-4o", temperature=0)
#llm = init_chat_model("o1-mini", model_provider="openai", temperature=0)
# parameters = {
#     "temperature": 0,
# }
#
# llm = ChatWatsonx(
#     model_id="meta-llama/llama-3-3-70b-instruct",
#     url="https://us-south.ml.cloud.ibm.com",
#     project_id="e8f48b46-f7ac-4d78-a358-9c33a6e3b3d7",
#     params=parameters,
# )

# CLOUD PAK VERSION
# chat = ChatWatsonx(
#     model_id="ibm/granite-34b-code-instruct",
#     url="PASTE YOUR URL HERE",
#     username="PASTE YOUR USERNAME HERE",
#     password="PASTE YOUR PASSWORD HERE",
#     instance_id="openshift",
#     version="4.8",
#     project_id="PASTE YOUR PROJECT_ID HERE",
#     params=parameters,
# )

# DEPLOYMENT_ID VERSION
# chat = ChatWatsonx(
#     deployment_id="PASTE YOUR DEPLOYMENT_ID HERE",
#     url="https://us-south.ml.cloud.ibm.com",
#     project_id="PASTE YOUR PROJECT_ID HERE",
#     params=parameters,
# )

#Extract entities from text
# class Entities(BaseModel):
#     """Identifying information about entities."""
#
#     names: List[str] = Field(
#         ...,
#         description=f"All {graph_params["allowed_nodes"]} entities and relationships {graph_params["allowed_relationship"]} that "
#         "appear in the text",
#     )
#
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             f"You are extracting {graph_params["allowed_nodes"]} entities and relationships {graph_params["allowed_relationship"]} from the text.",
#         ),
#         (
#             "human",
#             "Use the given format to extract information from the following "
#             "input: {question}",
#         ),
#     ]
# )
#
# entity_chain = prompt | llm.with_structured_output(Entities)
#
#
#
# vector_index = Neo4jVector.from_existing_graph(
#     OpenAIEmbeddings(),
#     search_type=SearchType.HYBRID,
#     node_label="Document",
#     text_node_properties=["text"],
#     embedding_node_property="embedding"
# )
# kg_url = "neo4j://localhost:7687"
# kg_username = "neo4j"
# kg_password = "password"
# kg_db_name = "hackapizzafull"
# graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)
#
# graph_db.query(
#     "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
#
# def generate_full_text_query(input: str) -> str:
#     """
#     Generate a full-text search query for a given input string.
#
#     This function constructs a query string suitable for a full-text search.
#     It processes the input string by splitting it into words and appending a
#     similarity threshold (~2 changed characters) to each word, then combines
#     them using the AND operator. Useful for mapping entities from user questions
#     to database values, and allows for some misspelings.
#     """
#     full_text_query = ""
#     words = [el for el in remove_lucene_chars(input).split() if el]
#     for word in words[:-1]:
#         full_text_query += f" {word}~2 AND"
#     full_text_query += f" {words[-1]}~2"
#     return full_text_query.strip()
#
# # Fulltext index query
# def structured_retriever(question: str) -> str:
#     """
#     Collects the neighborhood of entities mentioned
#     in the question
#     """
#     result = ""
#     entities = entity_chain.invoke({"question": question})
#     for entity in entities.names:
#         response = graph_db.query(
#             """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
#             YIELD node,score
#             CALL {
#               MATCH (node)-[r:!MENTIONS]->(neighbor)
#               RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
#               UNION
#               MATCH (node)<-[r:!MENTIONS]-(neighbor)
#               RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
#             }
#             RETURN output LIMIT 50
#             """,
#             {"query": generate_full_text_query(entity)},
#         )
#         result += "\n".join([el['output'] for el in response])
#     return result
#
# def retriever(question: str):
#     print(f"Search query: {question}")
#     structured_data = structured_retriever(question)
#     unstructured_data = [el.page_content for el in vector_index.similarity_search(question)]
#     final_data = f"""Structured data:
# {structured_data}
# Unstructured data:
# {"#Document ". join(unstructured_data)}
#     """
#     return final_data
#
# template = """Answer the question based only on the following context:
# {context}
#
# Question: {question}
# """
# prompt = ChatPromptTemplate.from_template(template)
#
#
# def _format_chat_history(param):
#     pass
#
#
# _search_query = RunnableLambda(lambda x : x["question"])
#
# chain = (
#     RunnableParallel(
#         {
#             "context": _search_query | retriever,
#             "question": RunnablePassthrough(),
#         }
#     )
#     | prompt
#     | llm
#     | StrOutputParser()
# )
import os
from getpass import getpass
from typing import List

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()
# watsonx_api_key = getpass()
# os.environ["WATSONX_APIKEY"] = watsonx_api_key

# os.environ["WATSONX_URL"] = "your service instance url"
# os.environ["WATSONX_TOKEN"] = "your token for accessing the CPD cluster"
# os.environ["WATSONX_PASSWORD"] = "your password for accessing the CPD cluster"
# os.environ["WATSONX_USERNAME"] = "your username for accessing the CPD cluster"
# os.environ["WATSONX_INSTANCE_ID"] = "your instance_id for accessing the CPD cluster"

#llm = ChatOpenAI(model="gpt-4o")
llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0)
# parameters = {
#     "temperature": 0,
#     "max_tokens": 20000,
# }
#
# chat = ChatWatsonx(
#     model_id="ibm/granite-34b-code-instruct",
#     url="https://us-south.ml.cloud.ibm.com",
#     project_id="PASTE YOUR PROJECT_ID HERE",
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

# Extract entities from text
# class Entities(BaseModel):
#     """Identifying information about entities."""
#
#     names: List[str] = Field(
#         ...,
#         description="All the person, organization, or business entities that "
#         "appear in the text",
#     )
#
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are extracting organization and person entities from the text.",
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
# # Fulltext index query
# def structured_retriever(question: str) -> str:
#     """
#     Collects the neighborhood of entities mentioned
#     in the question
#     """
#     result = ""
#     entities = entity_chain.invoke({"question": question})
#     for entity in entities.names:
#         response = graph.query(
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
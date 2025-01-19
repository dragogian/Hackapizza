import os

from langchain_openai import OpenAIEmbeddings

from blue_vector_db import BlueVectorDatabase
from ingestion import load_file_documents_by_format

blue_vector_instance = BlueVectorDatabase()
docs = []
for file in os.listdir("Resources"):
    load_file_documents_by_format(file, docs, ref_path="Resources/", is_vector=True)
blue_vector_instance.create_vector_db(
    index_path="./faiss_index",
    embedding_model=OpenAIEmbeddings(model="text-embedding-3-large"),
    urls=docs  # documenti da indicizzare
)
import os

from dotenv import load_dotenv

from ingestion import load_file_documents_by_format, create_knowledge_graph_schema, create_knowledge_graph

load_dotenv()

if __name__ == "__main__":
    docs = []
    for file in os.listdir("resources"):
        load_file_documents_by_format(file, docs)

    schema = create_knowledge_graph_schema(docs)
    create_knowledge_graph(schema)

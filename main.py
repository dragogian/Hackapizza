import os

from dotenv import load_dotenv

from ingestion import load_file_documents_by_format, create_knowledge_graph_schema, create_knowledge_graph

load_dotenv()

if __name__ == "__main__":
    docs = []
    for file in os.listdir("resources"):
        print(f"Loading file: {file}")
        load_file_documents_by_format(file, docs)
    print(f"Creating knowledge graph schema with loaded documents...")
    schema = create_knowledge_graph_schema(docs)
    print(f"Creating knowledge graph with schema: \n {schema} \n")
    create_knowledge_graph(schema)

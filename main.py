import os
import pickle

from dotenv import load_dotenv

from ingestion import load_file_documents_by_format, create_knowledge_graph_schema, create_knowledge_graph

load_dotenv()

if __name__ == "__main__":
    docs = []
    if not os.path.exists("docs_v2.pickle"):
        for file in os.listdir("resources"):
            print(f"Loading file: {file}")
            load_file_documents_by_format(file, docs)
            with open("docs_v3.pickle", "wb") as f:
                pickle.dump(docs, f)
    else:
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs_v2.pickle", "rb"))
    print(f"Creating knowledge graph schema with loaded documents...")
    schema = create_knowledge_graph_schema(docs)
    with open("schema.pickle", "wb") as f:
        pickle.dump(schema, f)
    print(f"Creating knowledge graph with schema: \n {schema} \n")
    create_knowledge_graph(schema)

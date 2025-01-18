import asyncio
import os
import pickle

from dotenv import load_dotenv

from ingestion import load_file_documents_by_format, create_knowledge_graph_schema, create_knowledge_graph

load_dotenv()

async def main():
    docs = []
    if not os.path.exists("docs.pickle"):
        for file in os.listdir("resources"):
            print(f"Loading file: {file}")
            load_file_documents_by_format(file, docs)
        with open("docs.pickle", "wb") as f:
            pickle.dump(docs, f)
    else:
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs.pickle", "rb"))
    print(f"Creating knowledge graph schema with loaded documents...")
    if not os.path.exists("schema1.pickle"):
        schema = await create_knowledge_graph_schema(docs)
        with open("schema1.pickle", "wb") as f:
            pickle.dump(schema, f)
        print(f"Creating knowledge graph with schema: \n {schema} \n")
    else:
        print(f"Loading schema from pickle file...")
        schema = pickle.load(open("schema1.pickle", "rb"))
    create_knowledge_graph(schema)

if __name__ == "__main__":
    asyncio.run(main())
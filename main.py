import ast
import asyncio
import json
import os
import pickle
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from langchain_openai import OpenAIEmbeddings

from blue_vector_db import BlueVectorDatabase
from ingestion import load_file_documents_by_format, create_knowledge_graph_schema, create_knowledge_graph, \
    enrich_graph_from_docs, add_docs, ExtractionInfo, EnrichmentInfo

load_dotenv()

# async def main():
#     docs = []
#     if not os.path.exists("docs2.pickle"):
#         for file in os.listdir("resources"):
#             print(f"Loading file: {file}")
#             load_file_documents_by_format(file, docs)
#         with open("docs2.pickle", "wb") as f:
#             pickle.dump(docs, f)
#     else:
#         print(f"Loading documents from pickle file...")
#         docs = pickle.load(open("docs2.pickle", "rb"))
#     print(f"Creating knowledge graph schema with loaded documents...")
#     if not os.path.exists("schema3.pickle"):
#         schema = await create_knowledge_graph_schema(docs)
#         with open("schema3.pickle", "wb") as f:
#             pickle.dump(schema, f)
#         print(f"Creating knowledge graph with schema: \n {schema} \n")
#     else:
#         print(f"Loading schema from pickle file...")
#         schema = pickle.load(open("schema3.pickle", "rb"))
#     create_knowledge_graph(schema)

async def main():
    docs: List[Document] = []
    if os.path.exists("docs_final_12.pickle"):
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs_final_12.pickle", "rb"))
        if not os.path.exists("schema_final121.pickle"):
            print(f"Creating knowledge schema...")
            for doc in docs:
                try:
                    info = None
                    # Validate JSON format before parsing
                    if is_valid_json(doc.page_content):
                        try:
                            info = ExtractionInfo.model_validate_json(doc.page_content)
                        except Exception:
                            pass
                        try:
                            info = EnrichmentInfo.model_validate_json(doc.page_content)
                        except Exception:
                            pass

                        if info is not None:
                            json_content = json.loads(info.model_dump_json())
                            cleaned_content = clean_json(json_content)
                            doc.page_content = json.dumps(cleaned_content)
                    else:
                        print("Invalid JSON detected, skipping processing.")
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    print(f"Error processing document: {e}")
                    doc.page_content = doc.page_content.replace("\n", " ")
            schema = await create_knowledge_graph_schema(docs)
            with open("schema_final121.pickle", "wb") as f:
                pickle.dump(schema, f)
            print(f"Creating knowledge graph with schema: \n {schema} \n")
        else:
            print(f"Loading schema from pickle file...")
            schema = pickle.load(open("schema_final121.pickle", "rb"))
        create_knowledge_graph(schema)
    if not os.path.exists("docs_final_12.pickle"):
        # Process new files in the "Menu" directory
        for file in os.listdir("Menu"):
            print(f"Loading file: {file}")
            load_file_documents_by_format(file, docs)
        with open("docs_final_12.pickle", "wb") as f:
            pickle.dump(docs, f)
    else:
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs_final_12.pickle", "rb"))

    # Process additional directories
    for folder, name in [("Codice Galattico", "Codice Galattico/"),
                         ("Blogpost", "Blogpost/"),
                         ("Misc", "Misc/")]:
        for file in os.listdir(folder):
            print(f"Loading file: {file}")
            docs.extend(load_file_documents_by_format(file, docs, name))
            print(f"Enriching graph with additional info from {file}...")

    with open("docs_final_12.pickle", "wb") as f:
        pickle.dump(docs, f)

    if not os.path.exists("schema_final1211.pickle"):
        print(f"Creating knowledge schema...")
        for doc in docs:
            try:
                # Ensure valid JSON in the documents
                if not is_valid_json(doc.page_content):
                    raise ValueError("Invalid JSON detected.")
                json_content = json.loads(doc.page_content)
                cleaned_content = clean_json(json_content)
                doc.page_content = json.dumps(cleaned_content)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error: {e}. Document skipped or repaired.")
                doc.page_content = doc.page_content.replace("\n", " ")
            except TypeError as e:
                print(f"Type error: {e}")
                doc.page_content = str(doc.page_content).replace("\n", " ")
        schema = await create_knowledge_graph_schema(docs)
        with open("schema_final1211.pickle", "wb") as f:
            pickle.dump(schema, f)
        print(f"Creating knowledge graph with schema: \n {schema} \n")
    else:
        print(f"Loading schema from pickle file...")
        schema = pickle.load(open("schema_final1211.pickle", "rb"))
    blue_vector_instance = BlueVectorDatabase()
    blue_vector_instance.create_vector_db(
        index_path="./faiss_index",
        embedding_model="text-embedding-3-large",
        urls=docs  # documenti da indicizzare
    )
    #create_knowledge_graph(schema)


def is_valid_json(content):
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        return False


def clean_json(json_obj):
    """Recursively remove null/None values from a JSON object."""
    if isinstance(json_obj, dict):
        return {k: clean_json(v) for k, v in json_obj.items() if v is not None and v != "null"}
    elif isinstance(json_obj, list):
        return [clean_json(item) for item in json_obj if item is not None and item != "null"]
    else:
        return json_obj

if __name__ == "__main__":
    asyncio.run(main())
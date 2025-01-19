import asyncio
import json
import os
import pickle
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph

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
    if os.path.exists("docs_final_1.pickle"):
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs_final_1.pickle", "rb"))
        if not os.path.exists("schema_final1.pickle"):
            print(f"Creating knowledge schema...")
            for doc in docs:
                try:
                    # Try to parse page_content as JSON
                    info = None
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
                        # Clean the JSON from null/None values
                        cleaned_content = clean_json(json_content)
                        # Convert back to a JSON string
                        doc.page_content = json.dumps(cleaned_content)
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    # Handle malformed JSON gracefully
                    print(f"Error processing document: {e}")
                    # Replace newlines with spaces for non-JSON content
                    doc.page_content = doc.page_content.replace("\n", " ")
            schema = await create_knowledge_graph_schema(docs)
            with open("schema_final1.pickle", "wb") as f:
                pickle.dump(schema, f)
            print(f"Creating knowledge graph with schema: \n {schema} \n")
        else:
            print(f"Loading schema from pickle file...")
            schema = pickle.load(open("schema_final1.pickle", "rb"))
        create_knowledge_graph(schema)
    if not os.path.exists("docs_final.pickle"):
        #START FROM MENUS
        for file in os.listdir("Menu"):
            print(f"Loading file: {file}")
            load_file_documents_by_format(file, docs)
        with open("docs_final.pickle", "wb") as f:
            pickle.dump(docs, f)
    else:
        print(f"Loading documents from pickle file...")
        docs = pickle.load(open("docs_final.pickle", "rb"))

    #ADDITIONAL INFO
    for file in os.listdir("Codice Galattico"):
        print(f"Loading file: {file}")
        docs.extend(load_file_documents_by_format(file, docs, "Codice Galattico/"))
        print(f"Enriching graph with additional info from {file}...")
    for file in os.listdir("Blogpost"):
        print(f"Loading file: {file}")
        docs.extend(load_file_documents_by_format(file, docs, "Blogpost/"))
        print(f"Enriching graph with additional info from {file}...")
    for file in os.listdir("Misc"):
        print(f"Loading file: {file}")
        docs.extend(load_file_documents_by_format(file, docs, "Misc/"))
        print(f"Enriching graph with additional info from {file}...")

    with open("docs_final_1.pickle", "wb") as f:
        pickle.dump(docs, f)

    if not os.path.exists("schema_final1.pickle"):
        print(f"Creating knowledge schema...")
        for doc in docs:
            try:
                # Try to parse page_content as JSON
                info = None
                try:
                    info = ExtractionInfo.model_validate_json(doc.page_content)
                except Exception:
                    pass
                try:
                    info = EnrichmentInfo.model_validate_json(doc.page_content)
                except Exception:
                    pass
                if info is not None:
                    # If it's an ExtractionInfo or EnrichmentInfo object, add it to the graph
                    json_content = json.loads(info.model_dump_json())
                    # Clean the JSON from null/None values
                    cleaned_content = clean_json(json_content)
                    # Convert back to a JSON string
                    doc.page_content = json.dumps(cleaned_content)
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, just replace newlines with spaces
                continue
        schema = await create_knowledge_graph_schema(docs)
        with open("schema_final1.pickle", "wb") as f:
            pickle.dump(schema, f)
        print(f"Creating knowledge graph with schema: \n {schema} \n")
    else:
        print(f"Loading schema from pickle file...")
        schema = pickle.load(open("schema_final1.pickle", "rb"))
    create_knowledge_graph(schema)


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
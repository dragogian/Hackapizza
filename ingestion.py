import os.path
import shutil
from typing import Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, JSONLoader, TextLoader, UnstructuredHTMLLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ClientError

from llm import llm
from pdf_cleaner import clean_pdf

kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizzafinal"

load_dotenv()
graph_params = {
  "allowed_nodes": [
    "Piatto",
    "Ingrediente",
    "Tecnica",
    "Ristorante",
    "Pianeta",
    "Chef",
    "Licenza",
    "Ordine"
  ],
"allowed_relationships" : [
    ("Piatto", "CONTIENE_INGREDIENTE", "Ingrediente"),
    ("Piatto", "APPLICA_TECNICA", "Tecnica"),
    ("Piatto", "SERVITO_IN", "Ristorante"),
    ("Ristorante", "LOCALIZZATO_SU", "Pianeta"),
    ("Piatto", "PREPARATO_DA", "Chef"),
    ("Chef", "HA_LICENZA", "Licenza"),
    ("Chef", "APPARTIENE_ORDINE", "Ordine"),
    ("Ordine", "ORDINE_AUTORIZZA", "Piatto"),
],
"node_properties": [
    "coordinate",
    "descrizione",
    "livelloLicenza",
    "tipoLicenza",
    "specializzazioneChef",
    "categoriaPianeta",
    "capienzaRistorante",
    "flagLeggendario"
  ],
  "relationship_properties": [
    "quantitaUtilizzata",
    "unitaDiMisura",
    "distanzaInAnniLuce",
    "gradoRichiesto",
    "certificazioniRichieste",
    "dataInizio",
    "dataFine",
    "condizioniParticolari"
  ]
}

def load_file_documents_by_format(file: str, docs: list[Document]) -> list:
    file = "resources/" + file
    if file.endswith(".txt") or file.endswith(".md"):
        loader = TextLoader(file)
        docs.extend(loader.load_and_split())
    elif file.endswith(".csv"):
        loader = CSVLoader(file)
        docs.extend(loader.load_and_split())
    elif file.endswith(".pdf"):
        basename = os.path.basename(file).split(".")[0]
        cleaned_pdf = "resources_cleaned/" + basename + "_cleaned.pdf"
        if basename.startswith("Datapizza") or basename.startswith("Codice Galattico"):
            clean_pdf(file, cleaned_pdf)
        else:
            shutil.copy(file, cleaned_pdf)
        loader = PyPDFLoader(cleaned_pdf)
        docs.extend(loader.load_and_split())
    elif file.endswith(".html"):
        loader = UnstructuredHTMLLoader(file)
        docs.extend(loader.load_and_split())
    else:
        print(f"Unsupported file format: {file}")
        return docs
    return docs

async def create_knowledge_graph_schema(docs: list[Document]) -> list[GraphDocument]:
    graph_transformer = LLMGraphTransformer(llm=llm,
                                            allowed_nodes=graph_params["allowed_nodes"],
                                            allowed_relationships=graph_params["allowed_relationships"],
                                            node_properties=graph_params["node_properties"],
                                            relationship_properties=graph_params["relationship_properties"],
                                            prompt=""
                                            )
    return await graph_transformer.aconvert_to_graph_documents(docs)

def create_knowledge_graph(docs: list[GraphDocument]) -> None:
    try:
        graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)
    except ClientError as e:
        print("Database not found, creating a new one...")
        # Inizializza la connessione al database Neo4j
        base_graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password)
        base_graph_db.query(f"CREATE DATABASE {kg_db_name}")
        graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)
    graph_db.add_graph_documents(docs)
    return
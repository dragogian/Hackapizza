import os.path
import re
import shutil
from typing import Optional, List, Union

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, JSONLoader, TextLoader, UnstructuredHTMLLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from neo4j.exceptions import ClientError
from pydantic import Field, BaseModel

from llm import llm
from model import Piatto, Tecnica, Ristorante, Pianeta, Chef, LicenzeRichieste, Ordine
from pdf_cleaner import clean_pdf

kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizzaentire5"

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
  "allowed_relationships": [
    ("Piatto", "CONTIENE_INGREDIENTE", "Ingrediente"),
    ("Piatto", "APPLICA_TECNICA", "Tecnica"),
    ("Piatto", "SERVITO_IN", "Ristorante"),
    ("Ristorante", "LOCALIZZATO_SU", "Pianeta"),
    ("Piatto", "PREPARATO_DA", "Chef"),
    ("Chef", "HA_LICENZA", "Licenza"),
    ("Chef", "APPARTIENE_ORDINE", "Ordine"),
    ("Pianeta", "DISTA_DA", "Pianeta")
  ],
  "node_properties": [
    "nome",
    "descrizione",
    "quantita",
    "unita_di_misura",
    "leggendario",
    "categoria",
    "principi_fondamentali",
    "livello"
  ],
  "relationship_properties": [
    "descrizione",
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

# graph_params = {
#   "allowed_nodes": [
#     "PIATTO",
#     "INGREDIENTE",
#     "TECNICA",
#     "RISTORANTE",
#     "PIANETA",
#     "CHEF",
#     "LICENZA",
#     "ORDINE"
#   ],
#   "allowed_relationship": [
#     ("PIATTO", "CONTIENTE_INGREDIENTE", "INGREDIENTE"),
#     ("PIATTO", "USA_TECNICA", "TECNICA"),
#     ("PIATTO", "SERVITO_IN", "RISTORANTE"),
#     ("RISTORANTE", "SI_TROVA_SU", "PIANETA"),
#     ("TECNICA", "RICHIEDE_LICENZA", "LICENZA"),
#     ("CHEF", "HA_LICENZA", "LICENZA"),
#     ("CHEF", "APPARTIENE_A_ORDINE", "ORDINE"),
#     ("CHEF", "MEMBRO_DI_ORDINE", "ORDINE")
#   ],
#   "node_properties": [
#     "nome",
#     "descrizione",
#     "eLeggendario",
#     "gradoCHEFRichiesto",
#     "quantitaMassimaConsentita",
#     "esotico",
#     "multiDimensionale",
#     "richiedeGestioneSpeciale",
#     "categoria",
#     "licenzaRichiesta",
#     "fonteEnergia",
#     "eMultiReale",
#     "livelloLICENZACHEF",
#     "distanzaDaRiferimento",
#     "coordinateGalattiche",
#     "regioneGalattica",
#     "coordinate",
#     "livelloDimensionale",
#     "licenzeCHEF",
#     "appartenenzaORDINE",
#     "specializzazioni",
#     "tipoLICENZA",
#     "gradoLICENZA",
#     "licenzaTemporale",
#     "licenzaPsionica",
#     "requisitiIngresso"
#   ],
#   "relationship_properties": [
#     "quantita",
#     "unitaDiMisura",
#     "ingredienteFondamentale",
#     "conformeCodiceGalattico",
#     "chefConLICENZAAdeguata",
#     "attrezzaturaSpeciale",
#     "livelloEsecuzione",
#     "disponibilitaStagionale",
#     "menuSpeciale",
#     "inServizioDal",
#     "distanzaDalCentro",
#     "accessibilita",
#     "allineamentoDimensionale",
#     "gradoMinimo",
#     "tipoLICENZASpecifico",
#     "motivazione",
#     "gradoPosseduto",
#     "dataConseguimento",
#     "validaFinoAl",
#     "livelloDiAppartenenza",
#     "dataAdesione"
#   ]
# }


class ExtractionInfo(BaseModel):
    piatti: Optional[List[Piatto]] = Field(description="Informazioni sui piatti contenuti nel documento")
    pianeta: Optional[Pianeta] = Field(description="Info sul pianeta")
    licenze: Optional[List[LicenzeRichieste]] = Field(description="Info sulle licenze richieste per operare all'interno del documento")

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system", "You are a top-tier algorithm able to extract information from a document about the following entities: {entities}. Be clear and concise when filling the informations!"
                      "DO NOT FORGET TO INCLUDE ANY ENTITY THAT APPEARS IN THE DOCUMENT. BE SURE TO READ AND PARSE ALL THE DOC AND EXTRACT ALL THE INFO",
        ),
        (
            "human", "Given the following document:\n<document>\n{document}\n</document>\nSummarize and extract the needed information."
                     "For example, for a document like 'The pizza is a dish made of dough topped with tomato sauce and cheese and baked in an oven.' you should extract the entities 'piatto' (pizza), a list of 'ingrediente' (tomato sauce, cheese) and 'tecnica' (baked).",
        ),
    ]
)
#
# prompt_o1 = ChatPromptTemplate.from_messages(
#     [
#         (
#             "human", "You are a top-tier algorithm able to extract information from a document about the following entities: {entities}. Be clear and concise when filling the informations!"
#                      "DO NOT FORGET TO INCLUDE ANY ENTITY THAT APPEARS IN THE DOCUMENT. BE SURE TO READ AND PARSE ALL THE DOC AND EXTRACT ALL THE INFO"
#                      "Given the following document:\n<document>\n{document}\n</document>\nSummarize and extract the needed information."
#                      "For example, for a document like 'The pizza is a dish made of dough topped with tomato sauce and cheese and baked in an oven.' you should extract the entities 'piatto' (pizza), a list of 'ingrediente' (tomato sauce, cheese) and 'tecnica' (baked).",
#         ),
#     ]
# )



extraction_chain = prompt | llm.with_structured_output(ExtractionInfo)

class EnrichmentInfo(BaseModel):
    pianeti: Optional[Pianeta] = Field(description="Info sul pianeta")
    licenze: Optional[List[LicenzeRichieste]] = Field(description="Info sulle licenze richieste per operare all'interno del documento")
    ristoranti: Optional[List[Ristorante]] = Field(description="Info sui ristoranti contenuti nel documento")
    tecniche: Optional[List[Tecnica]] = Field(description="Info sulle tecniche contenute nel documento")
    ordini: Optional[List[Ordine]] = Field(description="Info sugli ordini contenuti nel documento")


enrichment_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system", "You are a top-tier algorithm able to extract information from a document about the following entities: {entities}. Be clear and concise when filling the informations!"
                      "DO NOT FORGET TO INCLUDE ANY ENTITY THAT APPEARS IN THE DOCUMENT. BE SURE TO READ AND PARSE ALL THE DOC AND EXTRACT ALL THE INFO",
        ),
        (
            "human", "Given the following document:\n<document>\n{document}\n</document>\nSummarize and extract the needed information. For example, for a document like 'The restaurant is on Pandora which is 456 lightyears away from Asgard' you should extract the entities 'pianeti' (Asgard, Pandora). For example, for a document like 'The technique 'Sferificazione' you need license 'Psionica' level 0' you should extract the entities 'tecniche' (Sferificazione) and 'licenze' (Psionica).",
        ),
    ]
)


enrichment_chain = enrichment_prompt | llm.with_structured_output(EnrichmentInfo)

def load_file_documents_by_format(file: str, docs: list[Document], ref_path: Optional[str] = None) -> list:
    file = ref_path + file if ref_path is not None else  "Menu/" + file
    if file.endswith(".txt") or file.endswith(".md"):
        loader = TextLoader(file)
        info = loader.load()
        combined_content = "".join(doc.page_content for doc in info)
        info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
        docs.append(Document(page_content=str(info_doc), source=file))
    elif file.endswith(".csv"):
        loader = CSVLoader(file)
        info = loader.load()
        combined_content = "".join(doc.page_content for doc in info)
        info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
        docs.append(Document(page_content=str(info_doc), source=file))
    elif file.endswith(".pdf"):
        basename = os.path.basename(file).split(".")[0]
        cleaned_pdf = "resources_cleaned/" + basename + "_cleaned.pdf"
        if basename.startswith("Datapizza") or basename.startswith("Codice Galattico"):
            clean_pdf(file, cleaned_pdf)
        else:
            print(file)
            shutil.copy(file, cleaned_pdf)
        loader = PyPDFLoader(cleaned_pdf)
        info = loader.load()
        if basename.startswith("Manuale di Cucina"):
            loader = PyPDFLoader(cleaned_pdf)
            info = loader.load()
            for i in range(0, len(info), 1):
                combined_content = "".join(doc.page_content for doc in info[i:i + 5])
                if combined_content:  # Ensure there is content to process
                    info_doc = enrichment_chain.invoke(
                        {"document": combined_content, "entities": graph_params["allowed_nodes"]})
                    docs.append(Document(page_content=str(info_doc), source=file))
        else:
            combined_content = "".join(doc.page_content for doc in info)
            info_doc = extraction_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
            docs.append(Document(page_content=str(info_doc), source=file))
    elif file.endswith(".html"):
        loader = UnstructuredHTMLLoader(file)
        info = loader.load()
        combined_content = "".join(doc.page_content for doc in info)
        info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
        docs.append(Document(page_content=str(info_doc), source=file))
    else:
        print(f"Unsupported file format: {file}")
        return docs
    return docs

async def create_knowledge_graph_schema(docs: list[Document]) -> list[GraphDocument]:
    graph_transformer = LLMGraphTransformer(llm=llm,
                                            allowed_nodes=graph_params["allowed_nodes"],
                                            allowed_relationships=graph_params["allowed_relationships"],
                                            node_properties=graph_params["node_properties"],
                                            relationship_properties=graph_params["relationship_properties"]
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

class Query(BaseModel):
    query: List[str] = Field(
        ...,
        description="The list of Cypher queries to be executed on the knowledge graph",
    )
prompt_enrich = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a top-tier data scientist able to generate the best Cypher queries to translate documents in knowledge graph info from a document about the following entities: {entities} to update an existing knowledge graph",
        ),
        (
            "human",
            "Given the following document:\n<document>\n{document}\n</document>\n"
            "and the following list of graph settings:"
            "<node_labels>{node_labels}</node_labels>"
            "<relationships>{relationships}</relationships>"
            "Generate the needed Cypher query to enrich the proper nodes or relationships in the knowledge graph."
            "Be careful, you should update the graph with the new information extracted from the document and if nodes or relationships are missing, you should create them."
            "Feel free to define the node and relationship to insert properties as needed."
            "DO NOT DELETE ANY EXISTING DATA!",
        ),
    ]
)


enrich_chain = prompt_enrich | llm.with_structured_output(Query)

def enrich_graph_from_docs(doc: Document):
    queries = enrich_chain.invoke({"document": doc, "entities": graph_params["allowed_nodes"], "node_labels": graph_params["allowed_nodes"], "relationships": graph_params["allowed_relationships"]})
    graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)
    print(f"Running query: {queries.query}")
    for query in queries.query:
        escaped_query = escape_quotes_in_neo4j_query(query)
        graph_db.query(escaped_query)


# def load_for_enrich(file: str, docs: list[Document]) -> list:
#     file = "resources/" + file
#     if file.endswith(".txt") or file.endswith(".md"):
#         loader = TextLoader(file)
#         info = loader.load()
#         combined_content = "".join(doc.page_content for doc in info)
#         info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
#         docs.append(Document(page_content=str(info_doc), source=file))
#     elif file.endswith(".csv"):
#         loader = CSVLoader(file)
#         info = loader.load()
#         combined_content = "".join(doc.page_content for doc in info)
#         info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
#         docs.append(Document(page_content=str(info_doc), source=file))
#     elif file.endswith(".pdf"):
#         basename = os.path.basename(file).split(".")[0]
#         cleaned_pdf = "resources_cleaned/" + basename + "_cleaned.pdf"
#         if basename.startswith("Datapizza") or basename.startswith("Codice Galattico"):
#             clean_pdf(file, cleaned_pdf)
#         else:
#             print(file)
#             shutil.copy(file, cleaned_pdf)
#         if basename.startswith("Manuale di Cucina"):
#             loader = PyPDFLoader(cleaned_pdf)
#             info = loader.load()
#             for doc in info:
#                 info_doc = enrichment_chain.invoke(
#                     {"document": doc, "entities": graph_params["allowed_nodes"]})
#                 docs.append(Document(page_content=str(info_doc), source=file))
#         else:
#             loader = PyPDFLoader(cleaned_pdf)
#             info = loader.load()
#             combined_content = "".join(doc.page_content for doc in info)
#             info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
#             docs.append(Document(page_content=str(info_doc), source=file))
#     elif file.endswith(".html"):
#         loader = UnstructuredHTMLLoader(file)
#         info = loader.load()
#         combined_content = "".join(doc.page_content for doc in info)
#         info_doc = enrichment_chain.invoke({"document": combined_content, "entities": graph_params["allowed_nodes"]})
#         docs.append(Document(page_content=str(info_doc), source=file))
#     else:
#         print(f"Unsupported file format: {file}")
#         return docs
#     return docs
#

# Function to escape quotes in the descrizione field if it exists
def escape_quotes_in_neo4j_query(query):
    # Match descrizione field with its content
    pattern = r"descrizione:'(.*?)'"

    # Function to escape single quotes within descrizione
    def escape_quotes(match):
        content = match.group(1)  # Extract the content inside descrizione
        escaped_content = content.replace("'", " ")  # Escape single quotes
        return f"descrizione:'{escaped_content}'"

    # Check if the pattern exists and apply transformation only if found
    if re.search(pattern, query):
        escaped_query = re.sub(pattern, escape_quotes, query)
        return escaped_query
    else:
        # If descrizione is not found, return the query unchanged
        return query


def add_docs(schema: list[GraphDocument]) -> None:
    graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)

    # Function to merge a single node
    def merge_node(node):
        query = f"""
        MERGE (n:{node['label']} {{id: $id}})
        SET n += $properties
        """
        graph_db.query(query, {"id": node["id"], "properties": node.get("properties", {})})

    # Function to merge a single relationship
    def merge_relationship(rel):
        query = f"""
        MATCH (a {{id: $start_id}})
        MATCH (b {{id: $end_id}})
        MERGE (a)-[r:{rel['type']}]->(b)
        SET r += $properties
        """
        graph_db.query(query, {
            "start_id": rel["start_id"],
            "end_id": rel["end_id"],
            "properties": rel.get("properties", {})
        })

    # Process the GraphDocument list
    for doc in schema:
        # Merge all nodes
        for node in doc.nodes:
            merge_node(node)
        # Merge all relationships
        for rel in doc.relationships:
            merge_relationship(rel)

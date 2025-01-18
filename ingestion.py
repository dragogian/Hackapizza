import os.path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, JSONLoader, TextLoader, UnstructuredHTMLLoader
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j.exceptions import ClientError

from llm import llm
from pdf_cleaner import clean_pdf

kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizza_full"

load_dotenv()
graph_params = {
  "allowed_nodes": [
    "PIATTO",
    "INGREDIENTE",
    "TECNICA",
    "RISTORANTE",
    "PIANETA",
    "CHEF",
    "LICENZA",
    "ORDINE"
  ],
  "allowed_relationship": [
    ("PIATTO", "CONTIENTE_INGREDIENTE", "INGREDIENTE"),
    ("PIATTO", "USA_TECNICA", "TECNICA"),
    ("PIATTO", "SERVITO_IN", "RISTORANTE"),
    ("RISTORANTE", "SI_TROVA_SU", "PIANETA"),
    ("TECNICA", "RICHIEDE_LICENZA", "LICENZA"),
    ("CHEF", "HA_LICENZA", "LICENZA"),
    ("CHEF", "APPARTIENE_A_ORDINE", "ORDINE"),
    ("CHEF", "MEMBRO_DI_ORDINE", "ORDINE")
  ],
  "node_properties": [
    "nome",
    "descrizione",
    "eLeggendario",
    "gradoChefRichiesto",
    "quantitaMassimaConsentita",
    "esotico",
    "multiDimensionale",
    "richiedeGestioneSpeciale",
    "categoria",
    "licenzaRichiesta",
    "fonteEnergia",
    "eMultiReale",
    "livelloLicenzaChef",
    "distanzaDaRiferimento",
    "coordinateGalattiche",
    "regioneGalattica",
    "coordinate",
    "livelloDimensionale",
    "licenzeChef",
    "appartenenzaOrdine",
    "specializzazioni",
    "tipoLicenza",
    "gradoLicenza",
    "licenzaTemporale",
    "licenzaPsionica",
    "requisitiIngresso"
  ],
  "relationship_properties": [
    "quantita",
    "unitaDiMisura",
    "ingredienteFondamentale",
    "conformeCodiceGalattico",
    "chefConLicenzaAdeguata",
    "attrezzaturaSpeciale",
    "livelloEsecuzione",
    "disponibilitaStagionale",
    "menuSpeciale",
    "inServizioDal",
    "distanzaDalCentro",
    "accessibilita",
    "allineamentoDimensionale",
    "gradoMinimo",
    "tipoLicenzaSpecifico",
    "motivazione",
    "gradoPosseduto",
    "dataConseguimento",
    "validaFinoAl",
    "livelloDiAppartenenza",
    "dataAdesione"
  ]
}


def load_file_documents_by_format(file: str, docs: list[Document]) -> list:
    file = "resources/" + file
    if file.endswith(".txt") or file.endswith(".md"):
        loader = TextLoader(file)
        docs.extend(loader.load_and_split())
    # elif file.endswith(".json"):
    #     loader = JSONLoader(file, ".", text_content=False)
    #     docs.extend(loader.load_and_split())
    elif file.endswith(".csv"):
        loader = CSVLoader(file)
        docs.extend(loader.load())
    elif file.endswith(".pdf"):
        basename = os.path.basename(file).split(".")[0]
        cleaned_pdf = "resources_cleaned/" + basename
        #clean_pdf(file, "resources_cleaned/" + basename + "_cleaned.pdf")
        loader = PyPDFLoader(cleaned_pdf, extract_images=True)
        docs.extend(loader.load_and_split())
    elif file.endswith(".html"):
        loader = UnstructuredHTMLLoader(file)
        docs.extend(loader.load_and_split())
    else:
        print(f"Unsupported file format: {file}")
        return docs
    return docs

async def create_knowledge_graph_schema(docs: list[Document]) -> list[GraphDocument]:
    graph_transformer = LLMGraphTransformer(llm=llm, allowed_nodes=graph_params["allowed_nodes"], allowed_relationships=graph_params["allowed_relationship"], node_properties=graph_params["node_properties"], relationship_properties=graph_params["relationship_properties"])
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
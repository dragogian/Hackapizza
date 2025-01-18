from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, JSONLoader, TextLoader, UnstructuredHTMLLoader
from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer

from llm import llm

kg_url = "neo4j://localhost:7687"
kg_username = "neo4j"
kg_password = "password"
kg_db_name = "hackapizza"

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
      "idPiatto",
      "nome",
      "descrizione",
      "eLeggendario",
      "gradoChefRichiesto",
      "idRistoranteOrigine",
      "idPianetaOrigine",
      "idIngrediente",
      "nome",
      "descrizione",
      "quantitaMassimaConsentita",
      "esotico",
      "multiDimensionale",
      "richiedeGestioneSpeciale",
      "idTecnica",
      "nome",
      "descrizione",
      "categoria",
      "licenzaRichiesta",
      "fonteEnergia",
      "eMultiReale",
      "idRistorante",
      "nome",
      "descrizione",
      "livelloLicenzaChef",
      "idPianetaLocalizzazione",
      "distanzaDaRiferimento",
      "coordinateGalattiche",
      "idPianeta",
      "nome",
      "descrizione",
      "regioneGalattica",
      "coordinate",
      "livelloDimensionale",
      "idChef",
      "nome",
      "licenzeChef",
      "appartenenzaOrdine",
      "specializzazioni",
      "idLicenza",
      "tipoLicenza",
      "gradoLicenza",
      "licenzaTemporale",
      "licenzaPsionica",
      "descrizione",
      "idOrdine",
      "nome",
      "descrizione",
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
      "idChefCreatore",
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
      "dataAdesione",
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
        docs.extend(loader.load_and_split())
    elif file.endswith(".pdf"):
        loader = PyPDFLoader(file, extract_images=True)
        docs.extend(loader.load_and_split())
    elif file.endswith(".html"):
        loader = UnstructuredHTMLLoader(file)
        docs.extend(loader.load_and_split())
    else:
        print(f"Unsupported file format: {file}")
        return docs
    return docs

def create_knowledge_graph_schema(docs: list[Document]) -> list[GraphDocument]:
    graph_transformer = LLMGraphTransformer(llm=llm, allowed_nodes=graph_params["allowed_nodes"], allowed_relationships=graph_params["allowed_relationship"], node_properties=True, relationship_properties=True)
    return graph_transformer.convert_to_graph_documents(docs)

def create_knowledge_graph(docs: list[GraphDocument]) -> None:
    graph_db = Neo4jGraph(url=kg_url, username=kg_username, password=kg_password, database=kg_db_name)
    graph_db.add_graph_documents(docs)
    return
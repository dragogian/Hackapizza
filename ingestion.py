from langchain_community.document_loaders import PyPDFLoader, CSVLoader, JSONLoader, TextLoader
from langchain_core.documents import Document


def load_file_documents_by_format(file: str, docs: list[Document]) -> list:
    if file.endswith(".txt") or file.endswith(".md"):
        loader = TextLoader(file)
        docs.extend(loader.load_and_split())
    elif file.endswith(".json"):
        loader = JSONLoader(file, ".")
        docs.extend(loader.load_and_split())
    elif file.endswith(".csv"):
        loader = CSVLoader(file)
        docs.extend(loader.load_and_split())
    elif file.endswith(".pdf"):
        loader = PyPDFLoader(file, extract_images=True)
        docs.extend(loader.load_and_split())
    else:
        raise ValueError("File format not supported")
    return docs
from typing import List, Any

import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS, Chroma


def remove_element_from_index(
        vectorstore: FAISS,
        target_metadata: dict
):
    id_to_remove = []
    docstore_dict = vectorstore.docstore.__dict__.get('_dict', {})
    for _id, doc in docstore_dict.items():
        to_remove = True
        for k, v in target_metadata.items():
            if doc.metadata[k] != v:
                to_remove = False
                break
        if to_remove:
            id_to_remove.append(_id)
    docstore_id_to_index = {
        v: k for k, v in vectorstore.index_to_docstore_id.items()
    }
    n_removed = len(id_to_remove)
    n_total = vectorstore.index.ntotal
    for _id in id_to_remove:
        # remove the document from the docstore
        del docstore_dict[
            _id
        ]
        # remove the embedding from the index
        ind = docstore_id_to_index[_id]
        vectorstore.index.remove_ids(
            np.array([ind], dtype=np.int64)
        )
        # remove the index to docstore id mapping
        del vectorstore.index_to_docstore_id[
            ind
        ]
    # reorder the mapping
    vectorstore.index_to_docstore_id = {
        i: _id
        for i, _id in enumerate(vectorstore.index_to_docstore_id.values())
    }
    return n_removed, n_total


class BlueVectorDatabase:
    """
        This class manages the creation and loading of vector databases using various embedding models
        and different types of vector databases, such as FAISS and Chroma.
    """

    def __init__(self):
        """
            Initializes the VectorDatabase class.
            The 'pages' attribute is used to store the documents loaded from URLs or provided directly.
        """
        self.pages = []

    def create_vector_db(self,
                         urls: List[str],
                         embedding_model,
                         index_path: str = "default",
                         vector_db_type: str = "FAISS",
                         extract_images: bool = False):
        """
            Creates a new vector database based on the provided documents or URLs.

            Parameters:
            - urls (List[str]): A list of URLs to PDF documents. If provided, documents will be loaded and processed.
            - index_path (str): The path where the vector index will be saved.
            - embedding_model (Any): The embedding model to use for creating the vector index.
            - vector_db_type (str): The type of vector database to create. Options include "FAISS" and "Chroma".
            - extract_images (bool): Whether to extract images from the documents. Default is False.

            Returns:
            - retriever: A retriever object for querying the created vector database.
        """

        print(f"Creating new {vector_db_type} vector store...")

        for url in urls:
            loaders = PyPDFLoader(url, extract_images=extract_images)
            slides = loaders.load_and_split()
            self.pages.extend(slides)

        # Use match-case to select the vector DB type
        match vector_db_type:
            case "FAISS":
                return self._create_faiss_vector_db(embedding_model, index_path)
            case "Chroma":
                return self._create_chroma_vector_db(embedding_model, index_path)
            case _:
                raise ValueError(f"Unsupported vector DB type: {vector_db_type}")

    def update_vector_db(self,
                         urls: List[str],
                         embedding_model,
                         files_to_delete: List[str],
                         index_path: str = "default",
                         vector_db_type: str = "FAISS",
                         extract_images: bool = False):
        """
            Creates a new vector database based on the provided documents or URLs.

            Parameters:
            - urls (List[str]): A list of URLs to PDF documents. If provided, documents will be loaded and processed.
            - index_path (str): The path where the vector index will be saved.
            - embedding_model (Any): The embedding model to use for creating the vector index.
            - vector_db_type (str): The type of vector database to create. Options include "FAISS" and "Chroma".
            - extract_images (bool): Whether to extract images from the documents. Default is False.

            Returns:
            - retriever: A retriever object for querying the created vector database.
        """

        print(f"Creating new {vector_db_type} vector store...")

        for url in urls:
            loaders = PyPDFLoader(url, extract_images=extract_images)
            slides = loaders.load_and_split()
            self.pages.extend(slides)

        # Use match-case to select the vector DB type
        match vector_db_type:
            case "FAISS":
                return self._update_faiss_vector_db(embedding_model, index_path, files_to_delete)
            case "Chroma":
                return self._update_chroma_vector_db(embedding_model, index_path, files_to_delete)
            case _:
                raise ValueError(f"Unsupported vector DB type: {vector_db_type}")

    def load_vector_db(self,
                       index_path: str,
                       embedding_model,
                       vector_db_type: str):

        """
            Loads an existing vector database from a local path.

            Parameters:
            - index_path (str): The path to the saved vector index.
            - embedding_model (Any): The embedding model to use for creating the vector index.
            - vector_db_type (str): The type of vector database to load. Options include "FAISS" and "Chroma".

            Returns:
            - vector: The loaded vector database object.
        """

        match vector_db_type:
            case "FAISS":
                return self._load_faiss_vector_db(embedding_model=embedding_model, index_path=index_path).as_retriever()
            case "Chroma":
                return self._load_chroma_vector_db(embedding_model=embedding_model,
                                                   index_path=index_path).as_retriever()
            case _:
                raise ValueError(f"Tipo di vector DB non supportato: {vector_db_type}")

    def _create_faiss_vector_db(self, embedding_model: Any, index_path: str):
        print("Creating FAISS vector database...")
        vector = FAISS.from_documents(self.pages, embedding_model)
        vector.save_local(index_path)

    def _update_faiss_vector_db(self, embedding_model: Any, index_path: str, files_to_delete: List[str]):
        print("Creating FAISS vector database...")
        index = FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)
        for file in files_to_delete:
            remove_element_from_index(index, {"source": file})
        index.add_documents(self.pages)
        index.save_local(index_path)

    def _create_chroma_vector_db(self, embedding_model: Any, index_path: str):
        print("Creating Chroma vector database...")
        Chroma.from_documents(
            documents=self.pages,
            collection_name="rag-chroma",
            embedding=embedding_model,
            persist_directory=str(index_path),
        )

    def _update_chroma_vector_db(self, embedding_model: Any, index_path: str, files_to_delete: List[str]):
        print("Creating Chroma vector database...")
        vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=embedding_model,
            persist_directory=str(index_path),  # Where to save data locally, remove if not necessary
        )
        ids_to_del = []
        for file in files_to_delete:
            ids_to_del = vector_store.get(where = {'source': file})['ids']
        vector_store.delete(ids_to_del)
        vector_store.add_documents(self.pages)

    def _load_faiss_vector_db(self, embedding_model: Any, index_path: str):
        print("Loading FAISS index...")
        return FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)

    def _load_chroma_vector_db(self, embedding_model: Any, index_path: str):
        print("Loading Chroma index...")
        return Chroma(
            collection_name="rag-chroma",
            persist_directory=index_path,
            embedding_function=embedding_model
        )
# Usage example:
# urls = ["url1", "url2"]
# index_path = "path_to_save_index"
# vector_db = VectorDatabase()
# retriever = vector_db.create_vector_db(urls, index_path, embedding_model, vector_db_type="FAISS")

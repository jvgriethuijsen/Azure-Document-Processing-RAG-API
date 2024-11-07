import logging
import os
from langchain.document_loaders import UnstructuredWordDocumentLoader, CSVLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from azure.cosmos import CosmosClient
import uuid
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

class DocumentProcessor:
    def __init__(self):
        self.db_url = os.getenv("DB_URL")
        self.db_key = os.getenv("DB_PRIMARY_KEY")
        self.db_name = os.getenv("DB_NAME")
        self.db_container = os.getenv("DB_CONTAINER")
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def get_files_from_folder(self, folder_path):
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                if os.path.isfile(os.path.join(folder_path, f))]
        return files

    def load_documents(self, files):
        pdf_docs, word_docs, csv_docs = [], [], []
        
        for file in files:
            file_extension = file.lower().split('.')[-1]
            
            try:
                if file_extension == 'pdf':
                    pdf_loader = PyPDFLoader(file)
                    pdf_docs.extend(pdf_loader.load())
                elif file_extension == 'docx':
                    word_loader = UnstructuredWordDocumentLoader(file)
                    word_docs.extend(word_loader.load())
                elif file_extension == 'csv':
                    csv_loader = CSVLoader(file_path=file)
                    csv_docs.extend(csv_loader.load())
            except Exception as e:
                logging.error(f"Error processing {file}: {str(e)}")
                
        return pdf_docs, word_docs, csv_docs

    def split_documents(self, pdf_docs, word_docs, csv_docs):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
        chunks = []
        
        if pdf_docs:
            chunks.extend(text_splitter.split_documents(pdf_docs))
        if word_docs:
            chunks.extend(text_splitter.split_documents(word_docs))
        if csv_docs:
            chunks.extend(text_splitter.split_documents(csv_docs))
            
        return chunks

    def create_cosmos_documents(self, chunks):
        cosmos_documents = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.page_content
            embedding = self.embedder.encode(chunk_text, convert_to_tensor=False).astype(np.float32).tolist()
                        
            cosmos_doc = {
                "id": str(uuid.uuid4()),
                "text": chunk_text,
                "embedding": embedding,
                "metadata": {
                    "source": chunk.metadata.get("source", "unknown"),
                    "page": chunk.metadata.get("page", i + 1)
                }
            }
            cosmos_documents.append(cosmos_doc)
        return cosmos_documents

    def ingest_to_cosmos(self, cosmos_documents):
        cosmos_client = CosmosClient(self.db_url, self.db_key)
        database = cosmos_client.get_database_client(self.db_name)
        container = database.get_container_client(self.db_container)

        for doc in cosmos_documents:
            container.create_item(body=doc)
            

    def query_documents(self, query_text, top_k=5):
        query_embedding = self.embedder.encode(query_text, convert_to_tensor=False).astype(np.float32).tolist()
        search_service_name = os.getenv("COG_SEARCH_NAME")
        index_name = os.getenv("COG_SEARCH_INDEX")
        api_key = os.getenv("COG_SEARCH_API_KEY")
        top_k = os.getenv("COG_SEARCH_TOP_K")

        # Construct the search URL
        # https://learn.microsoft.com/en-us/azure/search/search-get-started-vector?tabs=azure-cli
        # https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-create-index?tabs=config-2024-07-01%2Crest-2024-07-01%2Cpush%2Cportal-check-index
        url = f"https://{search_service_name}.search.windows.net/indexes/{index_name}/docs/search?api-version=2024-07-01"
        headers = {
            'Content-Type': 'application/json',
            'api-key': api_key
        }

        # Construct the request body for vector similarity search
        body = {
            "count": True,
            "search": query_text,
            "select": "text",
            "top": top_k,
            "vectorQueries": [
                {
                    "vector": query_embedding,
                    "k": top_k,
                    "fields": "embedding",
                    "kind": "vector",
                    "exhaustive": True
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 200:
                logging.error(f"Search API error: Status {response.status_code}, Response: {response.text}")
            response.raise_for_status()
            return response.json()["value"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Error in query_documents: {str(e)}, Response: {e.response.text if e.response else 'No response'}")
            raise
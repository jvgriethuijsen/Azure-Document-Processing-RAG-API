import logging
import os
from langchain.document_loaders import UnstructuredPDFLoader, UnstructuredWordDocumentLoader, CSVLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import pipeline
from azure.cosmos import CosmosClient
import uuid
import numpy as np
import requests
import json

class DocumentProcessor:
    def __init__(self, db_url, db_key, db_name, db_container):
        self.db_url = db_url
        self.db_key = db_key
        self.db_name = db_name
        self.db_container = db_container
        self.embedder = pipeline('feature-extraction', model='sentence-transformers/all-MiniLM-L6-v2')

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
            embedding = self.embedder(chunk_text, padding=True, truncation=True, max_length=512)[0]
            
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
        """
        Perform semantic search on stored documents.
        
        Args:
            query_text (str): The search query
            top_k (int): Number of results to return
            
        Returns:
            list: Top k matching documents with their scores
        """
        # Generate embedding for the query
        query_embedding = self.embedder(query_text, padding=True, truncation=True, max_length=512)[0]
        
        # Connect to Cosmos DB
        cosmos_client = CosmosClient(self.db_url, self.db_key)
        database = cosmos_client.get_database_client(self.db_name)
        container = database.get_container_client(self.db_container)
        

        # Azure Cognitive Search details
        search_service_name = os.getenv("COG_SEARCH_NAME")
        index_name = os.getenv("COG_SEARCH_INDEX")
        api_key = os.getenv("COG_SEARCH_API_KEY")

        # Query parameters
        top_k = 5

        # Construct the search URL
        url = f"https://{search_service_name}.search.windows.net/indexes/{index_name}/docs"
        headers = {
            'Content-Type': 'application/json',
            'api-key': api_key
        }
        params = {
            'api-version': '2024-07-01',
            'search': query_text,
            '$top': top_k
        }

        # Perform the search request
        response = requests.get(url, headers=headers, params=params)
        results = response.json()

        # Process and display results
        #for result in results['value']:
            #print(f"Document: {result['text']}")
            #print(f"Metadata: {result['metadata']}")
            #print(f"Score: {result['@search.score']}")

        return results["value"]

        """
        # Retrieve all documents
        query = "SELECT * FROM c"
        documents = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Calculate cosine similarity
        def cosine_similarity(vec1, vec2):
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        # Compute similarity scores
        results = []
        for doc in documents:
            doc_embedding = np.array(doc['embedding'])
            similarity_score = cosine_similarity(query_embedding, doc_embedding)
            results.append((doc, similarity_score))
        
        # Sort results by similarity score in descending order
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        return results[:top_k]
        """
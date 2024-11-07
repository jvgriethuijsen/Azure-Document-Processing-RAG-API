# Document Processing & RAG API

A serverless Azure Function that both provides document processing and RAG (Retrieval-Augmented Generation) capabilities through two main endpoints:

- `/api/ingest_documents`: Processes and indexes documents from the `ingest` folder
- `/api/query_documents`: Semantic similarity search across processed documents

## Features

- 📄 Multi-format document support (PDF, Word, CSV)
- 🔍 Vector-based semantic search using Azure Cognitive Search
- 💾 Document storage in Azure Cosmos DB
- 🔄 Automatic text chunking and embedding generation

## Quick Start

1. Place documents in the `ingest` folder
2. Call `/api/ingest_documents` to process and index them
3. Query your documents using `/api/query_documents?query=your search query`

# Installation
## Setup Azure (via azure portal)
- Create new azure function
- Setup a cosmosDB instance
- Setup a cognitive search service, with an index and an indexer
    - Fields: text and field embeddings (384) -> Collection.Single

# Setup vscode
- VScode -> install azure plugin -> Then execute: Azure functions: New project

pip install -r requirements.txt
(Perhaps some ingestion libs are still missing)

## Setup a .env file with:
DB_URL = "https://###.documents.azure.com:443/"
DB_PRIMARY_KEY = 
DB_NAME = 
DB_CONTAINER = 

COG_SEARCH_NAME = 
COG_SEARCH_API_KEY = 
COG_SEARCH_INDEX = 
COG_SEARCH_TOP_K = 3


## Use Cases
- Enterprise document search
- Knowledge base creation
- Content discovery systems
- Legal document analysis
- Research assistance

## Need Custom Development?
This API is maintained by Joey van Griethuijsen, specializing in:
- Backend & fullstack development
- Custom AI/ML solutions
- Enterprise search systems

📧 Contact: [info@joeyvg.nl]  
🌐 Website: [https://joeyvg.nl/en]

## License
MIT License
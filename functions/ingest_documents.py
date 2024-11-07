import azure.functions as func
import logging
import os
from services.document_processor import DocumentProcessor
import numpy as np

def ingest_documents(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Document ingestion function processed a request.')
    
    try:
        processor = DocumentProcessor(
            os.getenv("DB_URL"),
            os.getenv("DB_PRIMARY_KEY"),
            os.getenv("DB_NAME"),
            os.getenv("DB_CONTAINER")
        )

        # Get files from ingest folder
        ingest_folder = 'ingest'
        files = processor.get_files_from_folder(ingest_folder)
        
        if not files:
            return func.HttpResponse(
                "No files found in the ingest folder.",
                status_code=404
            )

        # Load and process documents
        pdf_docs, word_docs, csv_docs = processor.load_documents(files)
        chunks = processor.split_documents(pdf_docs, word_docs, csv_docs)
            
        # Clear the container before ingesting new documents
        #processor.clear_container()
        
        cosmos_documents = processor.create_cosmos_documents(chunks)
        
        boep = False
        # Convert embeddings to single-precision
        for chunk in cosmos_documents:
            if 'embedding' in chunk:
                # Print type before conversion
                if not boep:
                    print(f"Before conversion - First element type: {type(chunk['embedding'][0])}")
                    #print(f"Before conversion - Embedding structure: {chunk['embedding'][:2]}")  # Show first 2 elements
                                
                # Force float32 precision for each element
                chunk['embedding'] = [float(x) for x in chunk['embedding'][0]]  # Note the [0] to get inner list
                                
                # Print type after conversion
                if not boep:
                    print(f"After conversion - First element type: {type(chunk['embedding'][0])}")
                    #print(f"After conversion - Embedding structure: {chunk['embedding'][:2]}")  # Show first 2 elements
                    boep = True

        #return func.HttpResponse(f"TEMP DISABLED", status_code=200)
        processor.ingest_to_cosmos(cosmos_documents)

        return func.HttpResponse(
            f"Successfully processed and ingested {len(cosmos_documents)} document chunks.",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred during document processing: {str(e)}",
            status_code=500
        )
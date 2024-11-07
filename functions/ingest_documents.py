import azure.functions as func
import logging
import os
from services.document_processor import DocumentProcessor

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
        cosmos_documents = processor.create_cosmos_documents(chunks)
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
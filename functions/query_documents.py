import azure.functions as func
import logging
import os
import json
from services.document_processor import DocumentProcessor

def query_documents(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Document query function processed a request.')
    
    try:
        # Get query from URL parameters first
        query_text = req.params.get('query')
        
        # If not in URL params, try to get from JSON body
        if not query_text:
            try:
                req_body = req.get_json()
                query_text = req_body.get('query')
            except ValueError:
                pass

        # Check if we have a query
        if not query_text:
            return func.HttpResponse(
                "Please provide a 'query' parameter either in the URL or request body.",
                status_code=400
            )

        # Get top_k from params or body, default to 5
        try:
            top_k = int(req.params.get('top_k', 5))
        except (TypeError, ValueError):
            try:
                req_body = req.get_json()
                top_k = int(req_body.get('top_k', 5))
            except (ValueError, TypeError):
                top_k = 5

        # Create processor instance
        processor = DocumentProcessor(
            os.getenv("DB_URL"),
            os.getenv("DB_PRIMARY_KEY"),
            os.getenv("DB_NAME"),
            os.getenv("DB_CONTAINER")
        )

        # Use the processor's query_documents method
        results = processor.query_documents(query_text, top_k)
        
        # Format results
        formatted_results = [{
            'text': result['text'],
            'metadata': result['metadata'],
            'similarity_score': result['@search.score']
        } for result in results]

        return func.HttpResponse(
            json.dumps({
                'query': query_text,
                'results': formatted_results
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in query_documents: {str(e)}")
        return func.HttpResponse(
            f"An error occurred during document querying: {str(e)}",
            status_code=500
        )
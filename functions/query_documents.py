import azure.functions as func
import logging
import os
import json
from services.document_processor import DocumentProcessor

def query_documents(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Document query function processed a request.')
    
    try:
        query_text = req.params.get('query')
        
        if not query_text:
            try:
                req_body = req.get_json()
                query_text = req_body.get('query')
            except ValueError:
                pass

        if not query_text:
            return func.HttpResponse(
                "Please provide a 'query' parameter either in the URL or request body.",
                status_code=400
            )

        top_k = os.getenv("COG_SEARCH_TOP_K")
        processor = DocumentProcessor()
        results = processor.query_documents(query_text, top_k)
        
        formatted_results = [{
            'text': result['text'],
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
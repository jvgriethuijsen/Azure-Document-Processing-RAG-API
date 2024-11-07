import azure.functions as func
from dotenv import load_dotenv
from functions.query_documents import query_documents
from functions.ingest_documents import ingest_documents
load_dotenv()

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# http://localhost:7071/api/query_documents?query=needle
@app.route(route="query_documents")
def query_documents_route(req: func.HttpRequest) -> func.HttpResponse:
    return query_documents(req)

# http://localhost:7071/api/ingest_documents
@app.route(route="ingest_documents")
def ingest_documents_route(req: func.HttpRequest) -> func.HttpResponse:
    return ingest_documents(req)
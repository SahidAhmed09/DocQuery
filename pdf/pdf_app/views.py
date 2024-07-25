import os
import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
import fitz  # PyMuPDF
import faiss
from langchain_community.vectorstores import FAISS
import logging
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the embedding dimension
EMBED_DIMENSION = 384

# Initialize FAISS index
index = faiss.IndexFlatL2(EMBED_DIMENSION)

# Simple document store
class SimpleDocstore:
    def __init__(self):
        self.docs = {}
        self.counter = 0

    def add_document(self, doc):
        doc_id = self.counter
        self.docs[doc_id] = doc
        self.counter += 1
        return doc_id

    def get_document(self, doc_id):
        return self.docs.get(doc_id, None)

docstore = SimpleDocstore()

# Simple IndexToDocstoreID
class IndexToDocstoreID:
    def __init__(self):
        self.mapping = {}

    def add(self, index_id, docstore_id):
        self.mapping[index_id] = docstore_id

    def get(self, index_id):
        return self.mapping.get(index_id, None)

index_to_docstore_id = IndexToDocstoreID()

vector_store = FAISS(embedding_function=None, index=index, docstore=docstore, index_to_docstore_id=index_to_docstore_id)

# Initialize the embedding model
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Improved embedding function using the SentenceTransformer model
def embed_text(text):
    embedding = embedding_model.encode(text, convert_to_numpy=True)
    logging.debug(f"Embedding for text '{text[:50]}...': {embedding}")
    return embedding

@api_view(['POST'])
def upload_file(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    file_name = default_storage.save(file.name, file)
    
    # Load and process the PDF file using PyMuPDF
    file_path = os.path.join(default_storage.location, file_name)
    pdf_document = fitz.open(file_path)
    documents = []
    
    for page in pdf_document:
        text = page.get_text()
        documents.append({"text": text})
    
    doc_ids = []
    for doc in documents:
        embedding = embed_text(doc['text'])
        doc_id = docstore.add_document(doc)
        index_to_docstore_id.add(doc_id, doc_id)
        index.add(np.array([embedding]))  # Convert to NumPy array
        doc_ids.append(doc_id)

    logging.info(f"Uploaded file '{file_name}' with document IDs: {doc_ids}")
    return Response({'message': 'File uploaded successfully', 'file_name': file_name}, status=status.HTTP_200_OK)

@api_view(['POST'])
def query_file(request):
    query = request.data.get('query')
    if not query:
        return Response({'error': 'No query provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    query_embedding = embed_text(query)
    logging.debug(f"Query embedding: {query_embedding}")
    
    D, I = index.search(np.array([query_embedding]), k=1)
    
    if I[0][0] != -1:
        doc_id = index_to_docstore_id.get(I[0][0])
        document = docstore.get_document(doc_id)
        response_text = document['text']
    else:
        response_text = "No relevant information found."

    logging.info(f"Query result for '{query}': {response_text[:200]}...")
    return Response({'response': response_text}, status=status.HTTP_200_OK)

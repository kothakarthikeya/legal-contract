import os
import PyPDF2
import uuid
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone and Embedding Model
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "contracts-v2")

def parse_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error parsing PDF: {e}")

def parse_docx(file_path: str) -> str:
    """Placeholder for DOCX parsing"""
    return f"[Content from DOCX: {os.path.basename(file_path)}]"

def parse_pptx(file_path: str) -> str:
    """Placeholder for PPTX parsing"""
    return f"[Content from PPTX: {os.path.basename(file_path)}]"

def parse_image(file_path: str) -> str:
    """Placeholder for Image OCR"""
    return f"[OCR Content from Image: {os.path.basename(file_path)}]"

def parse_document(file_path: str) -> str:
    """Parse document based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_path)
    elif ext in [".ppt", ".pptx"]:
        return parse_pptx(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        return parse_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    if not words:
        return []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks

def get_embedding(text: str) -> List[float]:
    """Generate text embedding using SentenceTransformer"""
    try:
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise ValueError(f"Failed to generate embedding: {e}")

def ensure_index_exists(index_name: str, dimension: int = 384):
    """Ensure Pinecone index exists"""
    try:
        existing_indexes = pc.list_indexes()
        index_names = [i.name for i in existing_indexes]
        
        if index_name not in index_names:
            print(f"Creating index {index_name}...")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"Index {index_name} created.")
        else:
            print(f"Index {index_name} already exists.")
    except Exception as e:
        print(f"Warning checking/creating index: {e}")

def ingest_document(file_path: str, doc_id: str = None) -> Dict[str, Any]:
    """
    Parse document, chunk text, generate embeddings, and upsert to Pinecone
    """
    if not doc_id:
        doc_id = f"contract_{uuid.uuid4().hex[:8]}"
    
    # Parse document
    print(f"Parsing {file_path}...")
    text = parse_document(file_path)
    
    if not text:
        raise ValueError("No text extracted from document.")
        
    # Chunk text
    chunks = chunk_text(text)
    print(f"Generated {len(chunks)} chunks.")
    
    # Embed and upsert to Pinecone
    ensure_index_exists(INDEX_NAME)
    index = pc.Index(INDEX_NAME)
    
    vectors = []
    for i, chunk in enumerate(chunks):
        vector_id = f"{doc_id}_chunk_{i}"
        embedding = get_embedding(chunk)
        if embedding:
            metadata = {
                "text": chunk,
                "doc_id": doc_id,
                "chunk_id": i,
                "source": os.path.basename(file_path)
            }
            vectors.append((vector_id, embedding, metadata))
    
    # Batch upsert
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//batch_size + 1}")
        
    return {
        "doc_id": doc_id,
        "chunks": len(chunks),
        "pinecone_ready": True
    }

import os
import re
from pypdf import PdfReader
import chromadb
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
import google.generativeai as genai

class GeminiEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function for Chroma DB using Google Generative AI API."""
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
    def __call__(self, input: Documents) -> Embeddings:
        # If input is empty
        if not input:
            return []
        
        # Call API - embed each document individually to handle batch/single response
        embeddings = []
        for text in input:
            response = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            # Single-item response returns {'embedding': [...]}
            embeddings.append(response['embedding'])
        return embeddings

def extract_text_from_pdf(filepath):
    """Extract page-by-page text from PDF with page numbers."""
    reader = PdfReader(filepath)
    pages_data = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages_data.append({
                "content": text.strip(),
                "metadata": {
                    "source": os.path.basename(filepath),
                    "location": f"Page {i + 1}"
                }
            })
    return pages_data

def extract_text_from_markdown_or_txt(filepath):
    """Extract text from markdown or text files, attempting to detect sections/headers."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split content by H1/H2 headers to create meaningful sections
    sections = []
    current_section = "General"
    
    # Simple regex split by header lines
    lines = content.split("\n")
    current_chunk = []
    
    for line in lines:
        if line.startswith("# ") or line.startswith("## ") or (line.isupper() and len(line) < 50 and len(line) > 3):
            # Save previous section if not empty
            if current_chunk:
                sections.append({
                    "content": "\n".join(current_chunk).strip(),
                    "metadata": {
                        "source": os.path.basename(filepath),
                        "location": current_section
                    }
                })
                current_chunk = []
            current_section = line.replace("#", "").strip()
        else:
            current_chunk.append(line)
            
    # Add trailing chunk
    if current_chunk:
        sections.append({
            "content": "\n".join(current_chunk).strip(),
            "metadata": {
                "source": os.path.basename(filepath),
                "location": current_section
            }
        })
        
    return sections

def chunk_text(text, chunk_size=500, overlap=50):
    """Break text into overlapping chunks of rough character sizes."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def process_documents(directory):
    """Scan and process files in directory to create final chunk list."""
    all_chunks = []
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return all_chunks
        
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
            
        print(f"Processing: {filename}")
        
        file_chunks = []
        if filename.endswith(".pdf"):
            pages = extract_text_from_pdf(filepath)
            for page in pages:
                # Chunk each page
                chunks = chunk_text(page["content"])
                for chunk in chunks:
                    if chunk.strip():
                        file_chunks.append({
                            "content": chunk,
                            "metadata": {
                                "source": page["metadata"]["source"],
                                "location": page["metadata"]["location"]
                            }
                        })
        elif filename.endswith((".md", ".txt")):
            sections = extract_text_from_markdown_or_txt(filepath)
            for sec in sections:
                chunks = chunk_text(sec["content"])
                for chunk in chunks:
                    if chunk.strip():
                        file_chunks.append({
                            "content": chunk,
                            "metadata": {
                                "source": sec["metadata"]["source"],
                                "location": sec["metadata"]["location"]
                            }
                        })
        
        print(f"  Generated {len(file_chunks)} chunks for {filename}")
        all_chunks.extend(file_chunks)
        
    return all_chunks

def ingest_to_chroma(api_key, data_dir="docs/data", persist_dir="chroma_db"):
    """Main function to ingest KB data to Chroma DB."""
    # Process files
    chunks = process_documents(data_dir)
    if not chunks:
        print("No document chunks found to ingest.")
        return 0
        
    # Connect to Chroma
    client = chromadb.PersistentClient(path=persist_dir)
    
    # Define embedding function
    embedding_fn = GeminiEmbeddingFunction(api_key)
    
    # Get or create collection
    # Note: If it already exists, delete it first to ensure clean state
    try:
        client.delete_collection("support_kb")
        print("Cleared existing collection.")
    except Exception:
        pass
        
    collection = client.create_collection(
        name="support_kb",
        embedding_function=embedding_fn
    )
    
    # Batch load into Chroma
    documents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    
    print(f"Loading {len(ids)} chunks into Chroma DB...")
    
    # Chroma handles batching automatically or we can load directly
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print("Document ingestion complete.")
    return len(ids)

if __name__ == "__main__":
    # Test script standalone
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set. Standalone ingestion skipped.")
    else:
        ingest_to_chroma(api_key)

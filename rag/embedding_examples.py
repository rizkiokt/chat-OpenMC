import os
import google.generativeai as genai
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

def read_python_file(file_path):
    """Read a Python file and return its content."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def chunk_python_code(code, chunk_size=500):
    """Chunk Python code while keeping function and class definitions intact."""
    chunks = []
    current_chunk = ""
    
    lines = code.split("\n")
    for line in lines:
        if len(current_chunk) + len(line) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def create_embeddings_and_store(docs_source_dir, collection_name="document_embeddings"):
    """Create embeddings for Python files and store them in an existing ChromaDB collection."""
    # Initialize ChromaDB client and collection
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)

    # Traverse directories to find all Python files up to depth 1
    py_files = []
    for root, dirs, files in os.walk(docs_source_dir):
        depth = len(Path(root).relative_to(docs_source_dir).parts)
        if depth > 2:  
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    # Process each file
    for file_path in py_files:
        print(f"Processing file: {file_path}")

        # Read Python file
        code = read_python_file(file_path)
        
        # Chunk Python code
        chunks = chunk_python_code(code)

        # Generate embeddings and store in ChromaDB
        for i, chunk in enumerate(chunks):
            print(f"Creating embedding for chunk {i} of {file_path}")

            try:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=chunk
                )
                embedding = result['embedding']

                title = " ".join(word.capitalize() for word in os.path.splitext(file_path[len(docs_source_dir):].lstrip("/"))[0].replace("/", " ").replace("_", " ").split())

                # Generate a unique ID for the chunk
                chunk_id = f"{file_path}-{i}"

                # # Check if the ID exists in the collection
                # existing_records = collection.get(ids=[chunk_id])

                # # If the record exists, delete it before inserting
                # if existing_records and existing_records["ids"]:
                #     print(f"Overwriting existing embedding for {chunk_id}")
                #     collection.delete(ids=[chunk_id])

                # Add the new embedding
                collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    metadatas=[{
                        "file_path": file_path,
                        "section": "Python OpenMC examples",
                        "document": title,
                        "chunk": chunk
                    }]
                )

            except Exception as e:
                print(f"Error generating embedding for chunk {i}: {e}")

    print("Embeddings and metadata have been stored in ChromaDB.")

if __name__ == "__main__":
    # Set up the Google Gemini API key
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Directory containing the Python files
    docs_source_dir = "/home/rizki/openmc/examples/"

    # Execute the embedding creation process
    create_embeddings_and_store(docs_source_dir, "openmc_embeddings")

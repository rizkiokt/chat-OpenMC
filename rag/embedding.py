import os
import google.generativeai as genai
from docutils.core import publish_doctree
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

def preprocess_rst_content(rst_content):
    """Replace incorrect math labels and fix formatting before parsing."""
    # Fix math directive labels
    rst_content = rst_content.replace(":label:", ":name:")
    return rst_content

def parse_rst(file_path):
    with open(file_path, "r") as file:
        rst_content = file.read()

    # Preprocess the content
    rst_content = preprocess_rst_content(rst_content)

    try:
        doctree = publish_doctree(rst_content)
        return doctree
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None

def extract_text_with_metadata(doctree, file_path):
    metadata = {
        "file_path": file_path,
        "document": None,
        "sections": [],  # To store sections and their content
    }
    
    # Traverse the doctree and capture relevant data
    current_section = None
    
    for node in doctree.traverse():
        if node.tagname == "document":
            metadata["document"] = node[0].astext()
        elif node.tagname == "section":
            # When we encounter a section, save the previous one if exists
            if current_section:
                metadata["sections"].append(current_section)
            
            # Start a new section
            section_title = node[0].astext() if node.children else "Untitled Section"
            current_section = {
                "title": section_title,
                "content": []
            }
        elif current_section is not None:
            # Capture non-text tag names in the section content
            if node.tagname != "paragraph":
                current_section["content"].append({
                    "tagname": node.tagname,
                    "content": node.astext()
                })
    
    # Add the last section to metadata if any
    if current_section:
        metadata["sections"].append(current_section)
    
    return metadata

def chunk_text_with_metadata(metadata, chunk_size=500):
    chunks = []
    current_chunk = ""
    
    for section in metadata["sections"]:
        section_content = section["content"]
        for item in section_content:
            # Add the content to the current chunk
            new_chunk = item['content']
            if len(current_chunk) + len(new_chunk) > chunk_size:
                # If adding the new content exceeds the chunk size, start a new chunk
                chunks.append({
                    "metadata": {
                        "file_path": metadata["file_path"],
                        "section": section["title"],
                        "document": metadata["document"]
                    }, 
                    "chunk": current_chunk
                })
                current_chunk = new_chunk
            else:
                current_chunk += " " + new_chunk
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            "metadata": {
                "file_path": metadata["file_path"],
                "section": section["title"],
                "document": metadata["document"]
            },
            "chunk": current_chunk
        })
    
    return chunks

def create_embeddings_and_store(docs_source_dir, collection_name="document_embeddings"):
    """Create embeddings for RST files and store them in ChromaDB."""
    # Initialize ChromaDB client and collection
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)

    # Traverse directories to find all RST files up to depth 1
    rst_files = []
    for root, dirs, files in os.walk(docs_source_dir):
        depth = len(Path(root).relative_to(docs_source_dir).parts)
        if depth > 2:  # Adjusted depth to 1 for better performance
            continue
        for file in files:
            if file.endswith(".rst"):
                rst_files.append(os.path.join(root, file))

    # Process each file
    for file_path in rst_files:
        print(f"Processing file: {file_path}")

        # Parse RST and extract metadata
        doctree = parse_rst(file_path)
        if not doctree:
            continue  # Skip if parsing fails

        metadata = extract_text_with_metadata(doctree, file_path)

        # Chunk text with metadata
        chunks = chunk_text_with_metadata(metadata)

        # Generate embeddings and store in ChromaDB
        for i, chunk in enumerate(chunks):
            print(f"Creating embedding for chunk {i} of {chunk['metadata']['file_path']}")

            try:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=chunk["chunk"]
                )
                embedding = result['embedding']

                # **Include the actual chunk content in metadata**
                simplified_metadata = {
                    "file_path": chunk["metadata"]["file_path"],
                    "section": chunk["metadata"]["section"],
                    "document": chunk["metadata"]["document"],
                    "chunk": chunk["chunk"]  # Add the actual text content
                }

                # Store embedding in ChromaDB
                collection.add(
                    ids=[f"{file_path}-{i}"],
                    embeddings=[embedding],
                    metadatas=[simplified_metadata]  # Store chunk content inside metadata
                )
            except Exception as e:
                print(f"Error generating embedding for chunk {i}: {e}")

    print("Embeddings and metadata have been stored in ChromaDB.")


if __name__ == "__main__":
    # Set up the Google Gemini API key
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Directory containing the documentation
    docs_source_dir = "/home/rizki/openmc/docs/source/"

    # Execute the embedding creation process
    create_embeddings_and_store(docs_source_dir, "openmc_embeddings")
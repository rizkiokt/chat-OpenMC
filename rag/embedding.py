import os
import google.generativeai as genai
from docutils.core import publish_doctree
from pathlib import Path
import json

# Set up the Google Gemini API key
my_key = input("Insert Google Gemini API key")
genai.configure(api_key=my_key)

# Directory containing the documentation
docs_source_dir = "/home/rizki/openmc/docs/source/usersguide/"

# Function to parse RST and extract text with metadata
def parse_rst(file_path):
    with open(file_path, "r") as file:
        rst_content = file.read()
    doctree = publish_doctree(rst_content)
    return doctree

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

# Function to chunk text with metadata
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
                    "metadata": {**metadata, "section": section["title"]}, 
                    "chunk": current_chunk
                })
                current_chunk = new_chunk
            else:
                current_chunk += " " + new_chunk
    
    # Add the last chunk
    if current_chunk:
        chunks.append({
            "metadata": {**metadata, "section": section["title"]},
            "chunk": current_chunk
        })
    
    return chunks

# Function to create embeddings and store metadata in JSON
def create_embeddings_and_store(docs_source_dir, output_file="embeddings_output.json"):
    embeddings_data = []  # List to hold all metadata and embeddings
    
    # Traverse directories to find all RST files up to depth 1
    rst_files = []
    for root, dirs, files in os.walk(docs_source_dir):
        depth = len(Path(root).relative_to(docs_source_dir).parts)
        if depth > 1:
            continue
        for file in files:
            if file.endswith(".rst"):
                rst_files.append(os.path.join(root, file))
    
    # Process each file
    for file_path in rst_files:
        print(f"Processing file: {file_path}")
        
        # Parse RST and extract metadata
        doctree = parse_rst(file_path)
        metadata = extract_text_with_metadata(doctree, file_path)
        
        # Chunk text with metadata
        chunks = chunk_text_with_metadata(metadata)
        
        # Generate embeddings and store the metadata with embeddings
        for chunk in chunks:
            print(f"Creating embedding for chunk of {chunk['metadata']['file_path']}")
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=chunk["chunk"]
            )
            
            # Here we store the embeddings with metadata
            embedding = result['embedding']
            chunk["metadata"]["embedding"] = embedding
            
            # Add the chunk with metadata and embedding to the list
            embeddings_data.append(chunk)
    
    # Store all embeddings data to a JSON file
    with open(output_file, "w") as f:
        json.dump(embeddings_data, f, indent=4)

    print(f"Embeddings and metadata have been saved to {output_file}")

# Execute the embedding creation process
create_embeddings_and_store(docs_source_dir, output_file="openmc_docs_embeddings.json")

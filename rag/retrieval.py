import google.generativeai as genai
import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import os

# Function to compute similarity score (cosine similarity)
def compute_similarity(embedding1, embedding2):
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))


# Function to retrieve relevant passages based on query
def get_relevant_docs(query, collection, top_k=5):
    # Generate embedding for the query
    query_embedding_result = genai.embed_content(
        model="models/text-embedding-004",
        content=query
    )
    query_embedding = query_embedding_result["embedding"]

    # Fetch all embeddings from ChromaDB collection
    results = collection.get(include=["metadatas", "embeddings"])
    
    # Compute similarity scores
    similarities = []
    for i, chunk_embedding in enumerate(results["embeddings"]):
        similarity = compute_similarity(query_embedding, chunk_embedding)
        similarities.append({
            "section": results["metadatas"][i]["section"],
            "file_path": results["metadatas"][i]["file_path"],
            "document": results["metadatas"][i]["document"],
            "chunk": results["metadatas"][i]["chunk"],
            "similarity": similarity
        })

    # Sort by similarity and return the top_k chunks with metadata
    similarities = sorted(similarities, key=lambda x: x["similarity"], reverse=True)
    return similarities[:top_k]

# Example usage
if __name__ == "__main__":
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Initialize ChromaDB client and collection
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_collection(name="openmc_embeddings", embedding_function=embedding_fn)

    # Insert your query
    query = "Write me pincell input example in .py"

    # Retrieve the top 5 most relevant sections
    top_results = get_relevant_docs(query, collection, top_k=5)

    # Print the results
    for i, result in enumerate(top_results, 1):
        print(f"\nResult {i}:")
        print(f"File Path: {result['file_path']}")
        print(f"Section: {result['section']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Content: {result['chunk']}")
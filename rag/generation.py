import google.generativeai as genai
import json
import numpy as np
from rag.retrieval import get_relevant_docs
import os
import chromadb
from chromadb.utils import embedding_functions

# Function to create a RAG prompt with conversational history
def make_rag_prompt(query, relevant_passages, chat_history):
    # Format passages with document source and section for more context
    passages_with_context = []
    for passage in relevant_passages:
        context = (
            f"Document: {passage['document']}\n"
            f"Section: {passage['section']}\n"
            f"Content: {passage['chunk']}\n"
        )
        passages_with_context.append(context)

    # Combine the passages into a single block
    relevant_passage_text = "\n\n".join(passages_with_context)

    # Format the chat history
    formatted_history = ""
    for message in chat_history[-5:]:  # Limit to last 5 exchanges to keep prompt concise
        role = "User" if message["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {message['content']}\n"

    # Create the RAG prompt with context
    prompt = (
        f"You are an OpenMC expert assistant that answers questions using text from the OpenMC Documentation below.\n"
        f"You are also an expert in nuclear engineering, especially reactor designs.\n"
        f"Use your creativity when the user asks to write input files/codes, but always refer to the user's guide and utilize examples. Prioritize to write using OpenMC Python API, unless asked other formats. \n"
        f"Use reasonable engineering assumptions for parameters needed to write a complete input file. \n"
        f"Maintain a professional, conversational, and helpful tone. Also, mention the source based on the documentation metadata.\n\n"
        f"Previous Conversation:\n{formatted_history}\n\n"
        f"Current Question: '{query}'\n"
        f"Relevant OpenMC Documentation:\n{relevant_passage_text}\n\n"
        f"ANSWER:"
    )
    
    return prompt


# Function to generate a response using Google Gemini
def generate_response(user_prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    answer = model.generate_content(user_prompt)
    return answer.text

# Main function to generate an answer with conversational history
def generate_answer(query, collection, chat_history):
    # Retrieve relevant passages
    relevant_passages = get_relevant_docs(query, collection)

    # Create a contextual prompt using chat history
    prompt = make_rag_prompt(query, relevant_passages, chat_history)

    # Generate the answer using the prompt
    answer = generate_response(prompt)
    return answer


# Example usage
if __name__ == "__main__":

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Insert your query
    #query = input("Enter your query: ")
    query = f"Provide an example of OpenMC input files using Python API."

    # Initialize ChromaDB client and collection
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_collection(name="openmc_embeddings", embedding_function=embedding_fn)

    # Generate the answer
    try:
        answer = generate_answer(query, collection)
        print("\nGenerated Answer:")
        print(answer)
    except Exception as e:
        print(f"Error: {e}")

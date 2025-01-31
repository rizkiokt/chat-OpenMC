import google.generativeai as genai
import json
import numpy as np
from rag.retrieval import get_relevant_docs
import os
import time
import chromadb
from chromadb.utils import embedding_functions
import streamlit as st

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
        f"You are an OpenMC expert assistant specializing in nuclear engineering, particularly reactor designs. "
        f"Your goal is to assist users by generating Python code for OpenMC input files based on documentation. "
        f"Your responses should use the OpenMC Python API whenever possible, unless specified otherwise. "
        f"Always refer to the OpenMC documentation and use relevant examples when applicable. "
        f"Provide full Python code whenever possible. "
        f"Do not leave code incomplete; make reasonable assumptions where necessary, but clarify these assumptions with the user if they are important. "
        f"You don't need to define the cross section library as it is set up in the system already. "
        f"Ensure that the generated Python code is organized, readable, and precise for the user's purpose. "
        f"Always maintain a professional and helpful tone and be sure to mention the source of the documentation used. "
        f"\n\nPrevious Conversation:\n{formatted_history}\n\n"
        f"Current Question: '{query}'\n\n"
        f"Relevant OpenMC Documentation:\n{relevant_passage_text}\n\n"
        f"ANSWER (Break down the task if necessary and ensure the solution is clear and well-commented):"
    )
    
    return prompt


# Function to generate a response using Google Gemini
def generate_response(model,user_prompt):
    #model = genai.GenerativeModel('gemini-1.5-flash')
    answer = model.generate_content(user_prompt)
    return answer.text



# Main function to generate an answer with conversational history
def generate_answer(model, query, collection, chat_history):
    # Start overall timer
    start_time = time.time()
    
    with st.status("Generating answer...", expanded=True) as status:
        
        # Start timer for retrieving relevant docs
        start_retrieving_time = time.time()
        st.write("Retrieving relevant OpenMC documentation...")
        relevant_passages = get_relevant_docs(query, collection)
        end_retrieving_time = time.time()
        retrieving_time = end_retrieving_time - start_retrieving_time
        
        for passage in relevant_passages:
            st.write(f'<p style="padding-left: 20px;">Document: {passage["document"]}, Section: {passage["section"]}</p>', unsafe_allow_html=True)

        # Start timer for creating contextual prompt
        start_prompt_time = time.time()
        st.write("Creating contextual prompt...")
        prompt = make_rag_prompt(query, relevant_passages, chat_history)
        end_prompt_time = time.time()
        prompt_creation_time = end_prompt_time - start_prompt_time
        
        # Start timer for generating response
        start_response_time = time.time()
        st.write("Generating response...")
        # st.write(f"Using model", model.model_name)
        answer = generate_response(model, prompt)
        end_response_time = time.time()
        response_generation_time = end_response_time - start_response_time
        
        # Total time taken for all steps
        end_time = time.time()
        total_time = end_time - start_time
        
        # Updating status after generation is complete with timing information
        status.update(
            label=(
                f"Answer generated! "
                f"Retrieving docs: {retrieving_time:.2f}s, "
                f"Processing prompt: {prompt_creation_time:.2f}s, "
                f"Response generation: {response_generation_time:.2f}s, "
                f"Total: {total_time:.2f}s"
            ),
            state="complete",
            expanded=False
        )
    
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

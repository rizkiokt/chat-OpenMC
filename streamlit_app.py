import streamlit as st
import google.generativeai as genai
import json
import time
import os
import shutil
import chromadb
from chromadb.utils import embedding_functions

from rag.generation import generate_answer
from gui.chat_history import get_saved_chats, load_chat_history, generate_chat_topic, save_chat_history, CHAT_HISTORY_DIR



st.set_page_config(page_title="Chat-OpenMC", page_icon="💡")

# Streamlit UI
st.title("💡 OpenMC Chatbot")
st.write("This chatbot interfaces with OpenMC nuclear simulation codes to provide assistance and insights. ")
st.write("To use this app, you need to provide a Gemini API key.")



# Initialize the session state for parameters if not already done
if 'topic' not in st.session_state:
    st.session_state.topic = None 


gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🔑")
    st.stop()

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_collection(name="openmc_embeddings", embedding_function=embedding_fn)

# Sidebar for selecting chat history
new_chat = st.sidebar.button("New Chat")
st.sidebar.header(f"Chat History:")
topics = get_saved_chats()
for topic in topics:
    if st.sidebar.button(f"🔹 {topic}", use_container_width=True):
        st.session_state.topic = topic
        st.rerun()

if new_chat or not st.session_state.topic:
    st.session_state.messages = []
    st.session_state.topic = None
else:
    st.session_state.messages = load_chat_history(st.session_state.topic)

tab_chat, tab_run = st.tabs(["Chat", "OpenMC Run"])


# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        tab_chat.markdown(message["content"])

if prompt := tab_chat.chat_input("Ask about OpenMC simulations..."):
    if not st.session_state.topic:
        selected_topic = generate_chat_topic(prompt)
        st.session_state.messages = []
        st.session_state.topic = selected_topic
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        tab_chat.markdown(prompt)

    response = generate_answer(prompt, collection, st.session_state.messages)

    with st.chat_message("assistant"):
        response_text = ""
        message_placeholder = tab_chat.empty()
        for char in response:
            response_text += char
            message_placeholder.markdown(response_text + "▌")
            time.sleep(0.001)
        message_placeholder.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response})
    save_chat_history(selected_topic, st.session_state.messages)
    #st.rerun()

clear_all = st.sidebar.button("Clear All Chat History")
if clear_all:
    shutil.rmtree(CHAT_HISTORY_DIR)

st.sidebar.markdown("<p style='font-size: 14px; text-align: center;'> Developed by: Rizki Oktavian</p>", unsafe_allow_html=True)

st.sidebar.markdown("<p style='font-size: 14px; text-align: center;'>© 2025 Blue Wave AI Labs<br>All rights reserved</p>", unsafe_allow_html=True)

import streamlit as st
import google.generativeai as genai
import json
import time
import os
import sys
import shutil
import subprocess
import chromadb
from chromadb.utils import embedding_functions
from code_editor import code_editor

from rag.generation import generate_answer
from gui.chat_history import get_saved_chats, load_chat_history, generate_chat_topic, save_chat_history, CHAT_HISTORY_DIR
from gui.code_run import save_python_script, run_python_script

st.set_page_config(page_title="Chat-OpenMC", page_icon="💡",layout="wide")





# Initialize the session state for parameters if not already done
if 'topic' not in st.session_state:
    st.session_state.topic = None 
if 'loaded' not in st.session_state:
    st.session_state.loaded = False 



os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Streamlit UI
st.title("💡 OpenMC Chatbot")
st.write("This chatbot interfaces with OpenMC nuclear simulation codes to provide assistance and insights. ")
st.write("To use this app, you need to provide a Gemini API key.")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🔑")
    st.stop()

left, right = st.columns(2)

left.subheader("Chat")
right.subheader("Code Editor")



genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_collection(name="openmc_embeddings", embedding_function=embedding_fn)

# Sidebar for selecting chat history
new_chat = st.sidebar.button("New Chat")
st.sidebar.header(f"Chat Histories:")
topics = get_saved_chats()
for topic in topics:
    if st.sidebar.button(f"{topic}", use_container_width=True):
        st.session_state.loaded = False
        st.session_state.topic = topic
        st.rerun()

if new_chat or not st.session_state.topic:
    st.session_state.messages = []
    st.session_state.topic = None
else:
    st.session_state.messages = load_chat_history(st.session_state.topic)

with left.container(height=600, border=True):
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about OpenMC simulations..."):

        if not st.session_state.topic:
            selected_topic = generate_chat_topic(prompt)
            st.session_state.messages = []
            st.session_state.topic = selected_topic
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = generate_answer(model,prompt, collection, st.session_state.messages)


        with st.chat_message("assistant"):
            response_text = ""
            message_placeholder = st.empty()
            for char in response:
                response_text += char
                message_placeholder.markdown(response_text + "▌")
                time.sleep(0.001)
            message_placeholder.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_history(st.session_state.topic, st.session_state.messages)

        st.rerun()


# code editor config variables
height = [19, 22]
language="python"
theme="default"
shortcuts="vscode"
focus=False
wrap=True
editor_btns = [
  {
    "name": "Copy",
    "feather": "Copy",
    "hasText": True,
    "alwaysOn": True,
    "commands": [
      "copyAll",
      [
        "infoMessage",
        {
          "text": "Copied to clipboard!",
          "timeout": 2500,
          "classToggle": "show"
        }
      ]
    ],
    "style": {
      "top": "-0.25rem",
      "right": "0.4rem"
    }
  },
  {
    "name": "Save",
    "feather": "Save",
    "primary": True,
    "hasText": True,
    "alwaysOn": True,
    "showWithIcon": True,
    "commands": [
      "submit"
    ],
    "style": {
      "bottom": "0.44rem",
      "right": "0.4rem"
    }
  }
]
code_file_path = save_python_script(st.session_state.messages, st.session_state.topic)
with right:
    if code_file_path:
        with open(code_file_path) as python_file:
            python_code = python_file.read()
        
        response_dict = code_editor(
            python_code, height=height, lang=language, theme=theme, 
            shortcuts=shortcuts, focus=focus, buttons=editor_btns
        )

        # If response is submitted, update the file with new code
        if response_dict.get('id') and (response_dict.get('type') == "submit"):
            # Overwrite code_file_path with the submitted code
            with open(code_file_path, "w") as python_file:
                python_file.write(response_dict["text"])
            st.write(f"file saved to",code_file_path)

if code_file_path:
    run_python_script(code_file_path)


clear_all = st.sidebar.button("Clear All Chat History")
if clear_all:
    shutil.rmtree(CHAT_HISTORY_DIR)
    st.rerun()

st.sidebar.markdown("<p style='font-size: 14px; text-align: center;'> Developed by: Rizki Oktavian</p>", unsafe_allow_html=True)

st.sidebar.markdown("<p style='font-size: 14px; text-align: center;'>© 2025 Blue Wave AI Labs<br>All rights reserved</p>", unsafe_allow_html=True)

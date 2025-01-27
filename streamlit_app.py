import streamlit as st
import google.generativeai as genai
import json
import time

# Show title and description.
st.title("💡 OpenMC Chatbot")
st.write(
    "This chatbot interfaces with OpenMC nuclear simulation codes to provide assistance and insights. "
    "To use this app, you need to provide a Gemini API key, which you can get [here](https://aistudio.google.com/app/apikey). "
    "You can also learn how to use OpenMC by visiting [OpenMC's documentation](https://docs.openmc.org/en/latest/)."
    )

# Ask user for their Gemini API key via `st.text_input`.
gemini_api_key = st.text_input("Gemini API Key", type="password")
if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🔑")
else:
    
    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Load chat history from a file
    def load_chat_history():
        try:
            with open("chat_history.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    # Save chat history to a file
    def save_chat_history(messages):
        with open("chat_history.json", "w") as file:
            json.dump(messages, file)

    # Sidebar options for storing and retrieving chat history
    with st.sidebar:
        if st.button("Save Chat History"):
            save_chat_history(st.session_state.messages)
            st.sidebar.success("Chat history saved!")
        if st.button("Load Chat History"):
            st.session_state.messages = load_chat_history()
            st.sidebar.success("Chat history loaded!")

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("Ask about OpenMC simulations..."):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the Gemini API.
        response = model.generate_content(f"Provide assistance with OpenMC nuclear simulations: {prompt}")
        
        # Typing animation effect
        with st.chat_message("assistant"):
            response_text = ""
            message_placeholder = st.empty()
            for char in response.text:
                response_text += char
                message_placeholder.markdown(response_text + "▌")
                time.sleep(0.001)
            message_placeholder.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response.text})

        # Save chat history
        save_chat_history(st.session_state.messages)

    # Option to clear chat history
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        save_chat_history([])
        st.rerun()

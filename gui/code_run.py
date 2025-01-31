import os
import sys
import subprocess
import streamlit as st
from gui.chat_history import CHAT_HISTORY_DIR


def extract_python_code(response_text):
    if "```python" in response_text:
        start = response_text.find("```python") + 9
        end = response_text.find("```", start)
        if end != -1:
            return response_text[start:end].strip()
    return None


def handle_python_script(messages, topic):
    """
    Processes the last message to extract Python code, save it to a file, and provide an option to run it.
    
    Args:
        messages (list): List of chat messages.
        topic (str): The topic name used for directory organization.
        extract_python_code (function): Function to extract Python code from a message.
    """
    if not messages:
        return
    
    last_response = messages[-1]["content"]
    code_content = extract_python_code(last_response)
    
    if not code_content:
        return
    
    python_filename = "response.py"
    topic_dir = os.path.join(CHAT_HISTORY_DIR, topic)
    os.makedirs(topic_dir, exist_ok=True)  # Ensure the directory exists
    code_file_path = os.path.join(topic_dir, python_filename)
    
    # Save the extracted Python code
    with open(code_file_path, "w") as f:
        f.write(code_content)
    
    

    # Streamlit UI buttons
    if st.button("Run Script"):
        try:
            with st.expander("Run Output", expanded=True):
                output_area = st.empty()  # Placeholder for live updates
                
                process = subprocess.Popen(
                    [sys.executable, python_filename],  
                    cwd=topic_dir,  # Set working directory
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1  # Line-buffered output
                )

                # Read output line by line and update Streamlit UI
                output_text = ""
                for line in iter(process.stdout.readline, ''):
                    output_text += line
                    output_area.code(output_text, language="text")

                process.stdout.close()
                process.wait()
        except Exception as e:
            st.error(f"Error running script: {e}")
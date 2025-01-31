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


def save_python_script(messages, topic):
    """
    Extracts Python code from the last message and saves it to a file.
    
    Args:
        messages (list): List of chat messages.
        topic (str): The topic name used for directory organization.
        extract_python_code (function): Function to extract Python code from a message.
    
    Returns:
        str: Path to the saved Python file, or None if no code was extracted.
    """
    if not messages:
        return None
    
    last_response = messages[-1]["content"]
    code_content = extract_python_code(last_response)
    
    if not code_content:
        return None
    
    python_filename = "response.py"
    topic_dir = os.path.join("CHAT_HISTORY_DIR", topic)
    os.makedirs(topic_dir, exist_ok=True)  # Ensure the directory exists
    code_file_path = os.path.join(topic_dir, python_filename)
    
    # Save the extracted Python code
    with open(code_file_path, "w") as f:
        f.write(code_content)
    
    return code_file_path

def run_python_script(script_path):
    """
    Runs a Python script and displays output in Streamlit.
    
    Args:
        script_path (str): Path to the Python script file.
    """
    if not script_path or not os.path.exists(script_path):
        st.error("Script file not found.")
        return
    
    if st.button("Run Script"):
        try:
            with st.expander("Script Output", expanded=True):
                output_area = st.empty()  # Placeholder for live updates
                
                process = subprocess.Popen(
                    [sys.executable, os.path.basename(script_path)],  
                    cwd=os.path.dirname(script_path),  # Set working directory
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
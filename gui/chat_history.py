import os
import json
import google.generativeai as genai


CHAT_HISTORY_DIR = "./chat_history"

def generate_chat_topic(prompt):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt + "\nDon't answer, just rewrite this prompt in 4 words or less:")
    return response.text.strip().replace(" ", "_").lower()

def get_chat_history_path(topic):
    topic_dir = os.path.join(CHAT_HISTORY_DIR, topic)
    os.makedirs(topic_dir, exist_ok=True)
    return os.path.join(topic_dir, f"{topic}.json")

def load_chat_history(topic):
    path = get_chat_history_path(topic)
    if os.path.exists(path):
        with open(path, "r") as file:
            return json.load(file)
    return []

def save_chat_history(topic, messages):
    with open(get_chat_history_path(topic), "w") as file:
        json.dump(messages, file)

def get_saved_chats():
    return [d for d in os.listdir(CHAT_HISTORY_DIR) if os.path.isdir(os.path.join(CHAT_HISTORY_DIR, d))]

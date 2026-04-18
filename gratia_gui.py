import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import sys
import os
from datetime import datetime
import anthropic
from openai import OpenAI
import speech_recognition as sr
import pyttsx3
import re
import sounddevice as sd
import numpy as np
import wave
import io
import json
import hashlib
from pathlib import Path
import threading

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize TTS engine
tts_engine = pyttsx3.init('sapi5')
tts_engine.setProperty('rate', 140)
tts_engine.setProperty('volume', 1.0)
voices = tts_engine.getProperty('voices')
if len(voices) > 1:
    for voice in voices:
        if 'female' in voice.name.lower():
            tts_engine.setProperty('voice', voice.id)
            break
    else:
        tts_engine.setProperty('voice', voices[1].id)

# Initialize recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 2500
recognizer.dynamic_energy_threshold = True

# Theme system
THEMES = {
    "space": {
        "name": "🚀 Space",
        "emoji": "🌌",
        "prefix": "🛸",
        "assistant": "✨",
        "success": "⭐",
        "error": "💫",
        "listening": "🛰️",
        "speaking": "📡",
        "bg": "#0a0e27",
        "fg": "#e0e0ff",
        "button": "#1a3a52"
    },
    "ocean": {
        "name": "🌊 Ocean",
        "emoji": "🌊",
        "prefix": "🐚",
        "assistant": "🐬",
        "success": "🌴",
        "error": "⚓",
        "listening": "🎣",
        "speaking": "🐚",
        "bg": "#001a33",
        "fg": "#b3e5fc",
        "button": "#00695c"
    },
    "default": {
        "name": "Default",
        "emoji": "✨",
        "prefix": "→",
        "assistant": "✓",
        "success": "✓",
        "error": "✗",
        "listening": "🎤",
        "speaking": "🔊",
        "bg": "#f0f0f0",
        "fg": "#333333",
        "button": "#4CAF50"
    }
}

SYSTEM_PROMPT = """
You are Gratia, a helpful AI assistant. Answer clearly and politely.
Keep responses short unless the user asks for more detail.
"""

PROVIDER = "anthropic"

# Data storage paths
DATA_DIR = Path.home() / ".gratia"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
CURRENT_USER_FILE = DATA_DIR / "current_user.txt"
SETTINGS_FILE = DATA_DIR / "settings.json"
TASKS_FILE = DATA_DIR / "tasks.json"
MESSAGES_FILE = DATA_DIR / "messages.json"
KNOWLEDGE_BASE_FILE = DATA_DIR / "knowledge_base.json"
LEARNING_PATTERNS_FILE = DATA_DIR / "learning_patterns.json"
MEMORY_FILE = DATA_DIR / "memory.json"
CONVERSATION_LOG_FILE = DATA_DIR / "conversation_log.json"

def load_json(filepath, default=None):
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default or {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# Global state
current_user = None
if CURRENT_USER_FILE.exists():
    with open(CURRENT_USER_FILE, 'r') as f:
        current_user = f.read().strip()

users = load_json(USERS_FILE, {})
settings = load_json(SETTINGS_FILE, {})
tasks = load_json(TASKS_FILE, {})
messages_data = load_json(MESSAGES_FILE, {})
knowledge_base = load_json(KNOWLEDGE_BASE_FILE, {})
learning_patterns = load_json(LEARNING_PATTERNS_FILE, {})
memory = load_json(MEMORY_FILE, {})
conversation_log = load_json(CONVERSATION_LOG_FILE, {})
messages = []

def get_current_theme():
    if not current_user:
        return THEMES["default"]
    theme_name = settings.get(current_user, {}).get("theme", "default")
    return THEMES.get(theme_name, THEMES["default"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    global users
    if username in users:
        return False, "User already exists."
    users[username] = {
        "password": hash_password(password),
        "created": datetime.now().isoformat()
    }
    save_json(USERS_FILE, users)
    return True, f"User {username} registered successfully."

def login_user(username, password):
    global current_user
    if username not in users:
        return False, "User not found."
    if users[username]["password"] != hash_password(password):
        return False, "Incorrect password."
    current_user = username
    with open(CURRENT_USER_FILE, 'w') as f:
        f.write(username)
    return True, f"Welcome back, {username}!"

def logout_user():
    global current_user
    current_user = None
    if CURRENT_USER_FILE.exists():
        CURRENT_USER_FILE.unlink()
    return True, "Logged out successfully."

def speak(text):
    try:
        if not text or text.strip() == "":
            return
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"Audio error: {e}")

def learn_from_input(user_input, response):
    if not current_user:
        return
    if current_user not in knowledge_base:
        knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
    if current_user not in learning_patterns:
        learning_patterns[current_user] = {"questions": [], "topics": [], "patterns": []}
    words = user_input.lower().split()
    for word in words:
        if len(word) > 4 and word not in ["about", "what", "that", "with", "from"]:
            if word not in learning_patterns[current_user]["topics"]:
                learning_patterns[current_user]["topics"].append(word)
    learning_patterns[current_user]["questions"].append({
        "input": user_input,
        "timestamp": datetime.now().isoformat(),
        "response_length": len(response)
    })
    save_json(KNOWLEDGE_BASE_FILE, knowledge_base)
    save_json(LEARNING_PATTERNS_FILE, learning_patterns)

def auto_learn_from_conversation(user_input, response):
    learn_from_input(user_input, response)
    if "prefer" in user_input.lower() or "like" in user_input.lower():
        if current_user not in knowledge_base:
            knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
    save_json(KNOWLEDGE_BASE_FILE, knowledge_base)

def get_learned_context():
    if not current_user:
        return ""
    kb = knowledge_base.get(current_user, {})
    context = ""
    facts = kb.get("facts", [])
    if facts:
        context += "Known facts: " + "; ".join([f["text"] for f in facts[-5:]]) + ". "
    interests = kb.get("interests", [])
    if interests:
        context += f"Interests: {', '.join(interests)}. "
    return context

def trim_history(max_messages=20):
    global messages
    if len(messages) > max_messages:
        messages = messages[-max_messages:]

def ask_anthropic():
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT + "\n\n📚 LEARNED CONTEXT:\n" + get_learned_context(),
        messages=messages,
    )
    return response.content[0].text

def ask_openai():
    learned_context = get_learned_context()
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n📚 LEARNED CONTEXT:\n" + learned_context}] + messages
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

def ask_ai(user_input):
    global messages
    if not user_input:
        return "Please enter a message."
    user_input = re.sub(r'^[Gg]ratia,?\s*', '', user_input).strip()
    
    # Auth commands
    if user_input.lower().startswith("login "):
        parts = user_input[6:].split(" ", 1)
        if len(parts) >= 2:
            username, password = parts[0], parts[1]
            success, message = login_user(username, password)
            return message
        return "Format: login username password"
    
    if user_input.lower().startswith("register "):
        parts = user_input[9:].split(" ", 1)
        if len(parts) >= 2:
            username, password = parts[0], parts[1]
            success, message = register_user(username, password)
            return message
        return "Format: register username password"
    
    if user_input.lower() == "logout":
        success, message = logout_user()
        return message
    
    if user_input.lower() == "whoami":
        if current_user:
            return f"You are logged in as: {current_user}"
        return "You are not logged in."
    
    if user_input.lower() == "help":
        return """Gratia Commands:
🔐 User: login username password | register username password | logout | whoami
⚙️ Settings: set key value | get key
🎨 Themes: theme space | theme ocean | theme default | themes
🕐 Other: time | exit"""
    
    if user_input.lower() == "themes":
        result = "Available themes:\n"
        for name, theme in THEMES.items():
            result += f"  • {theme['name']} (use: theme {name})\n"
        return result
    
    if user_input.lower().startswith("theme "):
        theme_name = user_input[6:].strip().lower()
        if theme_name not in THEMES:
            available = ", ".join(THEMES.keys())
            return f"Unknown theme. Available themes: {available}"
        if not current_user:
            return "Please login first."
        if current_user not in settings:
            settings[current_user] = {}
        settings[current_user]["theme"] = theme_name
        save_json(SETTINGS_FILE, settings)
        return f"Theme changed to {THEMES[theme_name]['name']}!"
    
    lower_input = user_input.lower().rstrip('?')
    if lower_input in ["time", "what time is it", "current time"]:
        return f"The current time is: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # AI query
    messages.append({"role": "user", "content": user_input})
    if PROVIDER == "anthropic":
        reply = ask_anthropic()
    else:
        reply = ask_openai()
    messages.append({"role": "assistant", "content": reply})
    trim_history()
    auto_learn_from_conversation(user_input, reply)
    if current_user not in conversation_log:
        conversation_log[current_user] = []
    conversation_log[current_user].append({
        "input": user_input,
        "output": reply,
        "timestamp": datetime.now().isoformat()
    })
    save_json(CONVERSATION_LOG_FILE, conversation_log)
    return reply


class GratiaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gratia - AI Assistant")
        self.root.geometry("900x700")
        self.voice_mode = False
        
        self.apply_theme()
        self.create_widgets()
        
    def apply_theme(self):
        theme = get_current_theme()
        self.root.configure(bg=theme['bg'])
        self.current_theme = theme
        
    def create_widgets(self):
        theme = self.current_theme
        
        # Header
        header = tk.Frame(self.root, bg=theme['button'], height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        
        title = tk.Label(header, text=f"{theme['emoji']} Gratia - AI Assistant", 
                        font=("Arial", 18, "bold"), bg=theme['button'], fg=theme['fg'])
        title.pack(pady=10)
        
        # Auth Frame
        auth_frame = tk.Frame(self.root, bg=theme['bg'])
        auth_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(auth_frame, text="Username:", bg=theme['bg'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        self.username_var = tk.StringVar()
        tk.Entry(auth_frame, textvariable=self.username_var, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Label(auth_frame, text="Password:", bg=theme['bg'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        self.password_var = tk.StringVar()
        tk.Entry(auth_frame, textvariable=self.password_var, width=15, show="*").pack(side=tk.LEFT, padx=5)
        
        tk.Button(auth_frame, text="Login", command=self.login, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        tk.Button(auth_frame, text="Register", command=self.register, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        tk.Button(auth_frame, text="Logout", command=self.logout, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        
        # User Status
        self.status_label = tk.Label(self.root, text=self.get_status(), bg=theme['bg'], fg=theme['fg'], font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        # Output area
        tk.Label(self.root, text="Chat History:", bg=theme['bg'], fg=theme['fg']).pack(anchor=tk.W, padx=10)
        self.output_text = scrolledtext.ScrolledText(self.root, height=15, width=100, 
                                                     bg="#1a1a1a", fg=theme['fg'], font=("Arial", 10))
        self.output_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = tk.Frame(self.root, bg=theme['bg'])
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(input_frame, text="Message:", bg=theme['bg'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        self.input_text = tk.Entry(input_frame, font=("Arial", 11), width=70)
        self.input_text.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
        self.input_text.bind("<Return>", lambda e: self.send_message())
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg=theme['bg'])
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="Send", command=self.send_message, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Voice: OFF", command=self.toggle_voice, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        
        # Theme selector
        tk.Label(button_frame, text="Theme:", bg=theme['bg'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        self.theme_var = tk.StringVar(value="default")
        theme_dropdown = ttk.Combobox(button_frame, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=12)
        theme_dropdown.pack(side=tk.LEFT, padx=5)
        theme_dropdown.bind("<<ComboboxSelected>>", lambda e: self.change_theme())
        
        tk.Button(button_frame, text="Clear", command=self.clear_output, bg=theme['button'], fg=theme['fg']).pack(side=tk.LEFT, padx=5)
        
        self.voice_button = tk.Button(button_frame, text="🔊 Voice: OFF", command=self.toggle_voice, bg=theme['button'], fg=theme['fg'])
        self.voice_button.pack(side=tk.LEFT, padx=5)
        
    def get_status(self):
        if current_user:
            return f"{self.current_theme['success']} Logged in as: {current_user}"
        return f"{self.current_theme['error']} Not logged in"
    
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        success, message = login_user(username, password)
        self.add_message("System", message)
        self.status_label.config(text=self.get_status())
        if success:
            self.apply_theme()
            self.refresh_widgets()
    
    def register(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        success, message = register_user(username, password)
        self.add_message("System", message)
    
    def logout(self):
        global current_user
        logout_user()
        self.add_message("System", "Logged out successfully")
        self.status_label.config(text=self.get_status())
        self.apply_theme()
        self.refresh_widgets()
    
    def toggle_voice(self):
        self.voice_mode = not self.voice_mode
        status = "ON" if self.voice_mode else "OFF"
        self.voice_button.config(text=f"🔊 Voice: {status}")
        self.add_message("System", f"Voice mode {status}")
    
    def change_theme(self):
        theme_name = self.theme_var.get()
        response = ask_ai(f"theme {theme_name}")
        self.add_message("Gratia", response)
        self.apply_theme()
        self.refresh_widgets()
    
    def refresh_widgets(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
    
    def send_message(self):
        user_input = self.input_text.get().strip()
        if not user_input:
            return
        
        self.add_message("You", user_input)
        self.input_text.delete(0, tk.END)
        
        # Run AI response in separate thread to avoid freezing
        thread = threading.Thread(target=self.process_message, args=(user_input,))
        thread.daemon = True
        thread.start()
    
    def process_message(self, user_input):
        try:
            response = ask_ai(user_input)
            self.root.after(0, self.add_message, "Gratia", response)
            if self.voice_mode:
                self.root.after(0, lambda: speak(response))
        except Exception as e:
            self.root.after(0, self.add_message, "Error", str(e))
    
    def add_message(self, sender, message):
        self.output_text.config(state=tk.NORMAL)
        theme = self.current_theme
        emoji = theme['assistant'] if sender == "Gratia" else theme['prefix']
        self.output_text.insert(tk.END, f"{emoji} {sender}: {message}\n\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = GratiaGUI(root)
    root.mainloop()

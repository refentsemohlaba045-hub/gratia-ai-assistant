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

# Make sure the relevant API key(s) are set in your environment
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize TTS engine with improved audio settings
tts_engine = pyttsx3.init('sapi5')  # Use Windows SAPI5 for better quality
tts_engine.setProperty('rate', 140)  # Speed of speech (slower for clarity)
tts_engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)

# Get available voices and set to female if available
voices = tts_engine.getProperty('voices')
if len(voices) > 1:
    for voice in voices:
        if 'female' in voice.name.lower():
            tts_engine.setProperty('voice', voice.id)
            break
    else:
        tts_engine.setProperty('voice', voices[1].id)  # Use second voice as fallback

# Initialize speech recognizer with improved sensitivity
recognizer = sr.Recognizer()
recognizer.energy_threshold = 2500  # Lower threshold for better voice detection
recognizer.dynamic_energy_threshold = True  # Adapt to ambient noise

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
    }
}

def get_current_theme():
    """Get the current theme for the user."""
    if not current_user:
        return THEMES["default"]
    theme_name = settings.get(current_user, {}).get("theme", "default")
    return THEMES.get(theme_name, THEMES["default"])

SYSTEM_PROMPT = """
You are Gratia, a helpful AI assistant. Answer clearly and politely.
Keep responses short unless the user asks for more detail.
"""

messages = []

PROVIDER = "anthropic"  # Switch to "openai" to use GPT instead

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

# Load or initialize data
def load_json(filepath, default=None):
    """Load JSON file, return default if not exists."""
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default or {}

def save_json(filepath, data):
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# User management
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


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def speak(text):
    """Convert text to speech with improved error handling and audio output."""
    try:
        if not text or text.strip() == "":
            return
        
        theme = get_current_theme()
        print(f"{theme['speaking']} Speaking...")
        tts_engine.say(text)
        tts_engine.runAndWait()  # This will block until speech is finished
        print(f"{theme['success']} Done speaking")
    except Exception as e:
        theme = get_current_theme()
        print(f"{theme['error']} Audio output error: {e}")


# User Management Functions
def hash_password(password):
    """Hash password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """Register a new user."""
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
    """Login a user."""
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
    """Logout current user."""
    global current_user
    current_user = None
    if CURRENT_USER_FILE.exists():
        CURRENT_USER_FILE.unlink()
    return True, "Logged out successfully."

# Settings Management
def set_setting(key, value):
    """Set a user setting."""
    if not current_user:
        return False, "Please login first."
    if current_user not in settings:
        settings[current_user] = {}
    settings[current_user][key] = value
    save_json(SETTINGS_FILE, settings)
    return True, f"Setting '{key}' set to '{value}'."

def get_setting(key, default=None):
    """Get a user setting."""
    if not current_user:
        return default
    return settings.get(current_user, {}).get(key, default)

# Task Management
def add_task(task_name):
    """Add a task for the user."""
    if not current_user:
        return False, "Please login first."
    if current_user not in tasks:
        tasks[current_user] = []
    tasks[current_user].append({
        "name": task_name,
        "completed": False,
        "created": datetime.now().isoformat()
    })
    save_json(TASKS_FILE, tasks)
    return True, f"Task '{task_name}' added."

def list_tasks():
    """List all tasks for the user."""
    if not current_user:
        return "Please login first."
    user_tasks = tasks.get(current_user, [])
    if not user_tasks:
        return "No tasks yet."
    result = "Your tasks:\n"
    for i, task in enumerate(user_tasks, 1):
        status = "✓" if task["completed"] else "○"
        result += f"  {i}. {status} {task['name']}\n"
    return result

def complete_task(task_number):
    """Mark a task as complete."""
    if not current_user:
        return False, "Please login first."
    user_tasks = tasks.get(current_user, [])
    if task_number < 1 or task_number > len(user_tasks):
        return False, "Invalid task number."
    user_tasks[task_number - 1]["completed"] = True
    save_json(TASKS_FILE, tasks)
    return True, f"Task '{user_tasks[task_number - 1]['name']}' completed!"

# Message Management
def save_message(recipient, subject, body):
    """Save a message for the user."""
    if not current_user:
        return False, "Please login first."
    if current_user not in messages_data:
        messages_data[current_user] = []
    messages_data[current_user].append({
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now().isoformat()
    })
    save_json(MESSAGES_FILE, messages_data)
    return True, f"Message saved for {recipient}."

def list_messages():
    """List all messages for the user."""
    if not current_user:
        return "Please login first."
    user_messages = messages_data.get(current_user, [])
    if not user_messages:
        return "No messages yet."
    result = "Your messages:\n"
    for i, msg in enumerate(user_messages, 1):
        result += f"  {i}. To: {msg['recipient']}\n     Subject: {msg['subject']}\n"
    return result

def show_message(msg_number):
    """Show a specific message."""
    if not current_user:
        return "Please login first."
    user_messages = messages_data.get(current_user, [])
    if msg_number < 1 or msg_number > len(user_messages):
        return "Invalid message number."
    msg = user_messages[msg_number - 1]
    return f"To: {msg['recipient']}\nSubject: {msg['subject']}\n\n{msg['body']}"


# ===== SECOND BRAIN: Learning System =====
def learn_from_input(user_input, response):
    """Analyze input and response to extract learning."""
    if not current_user:
        return
    
    if current_user not in knowledge_base:
        knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
    
    if current_user not in learning_patterns:
        learning_patterns[current_user] = {"questions": [], "topics": [], "patterns": []}
    
    # Extract keywords and topics
    words = user_input.lower().split()
    for word in words:
        if len(word) > 4 and word not in ["about", "what", "that", "with", "from"]:
            if word not in learning_patterns[current_user]["topics"]:
                learning_patterns[current_user]["topics"].append(word)
    
    # Store conversation patterns
    learning_patterns[current_user]["questions"].append({
        "input": user_input,
        "timestamp": datetime.now().isoformat(),
        "response_length": len(response)
    })
    
    # Save learning data
    save_json(KNOWLEDGE_BASE_FILE, knowledge_base)
    save_json(LEARNING_PATTERNS_FILE, learning_patterns)

def add_fact(fact_text, category="general"):
    """Add a fact to the knowledge base."""
    if not current_user:
        return False
    
    if current_user not in knowledge_base:
        knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
    
    knowledge_base[current_user]["facts"].append({
        "text": fact_text,
        "category": category,
        "timestamp": datetime.now().isoformat()
    })
    
    save_json(KNOWLEDGE_BASE_FILE, knowledge_base)
    return True

def get_learned_context():
    """Get context from learned information to enhance responses."""
    if not current_user:
        return ""
    
    kb = knowledge_base.get(current_user, {})
    context = ""
    
    # Add facts
    facts = kb.get("facts", [])
    if facts:
        context += "Known facts: " + "; ".join([f["text"] for f in facts[-5:]]) + ". "
    
    # Add interests
    interests = kb.get("interests", [])
    if interests:
        context += f"Interests: {', '.join(interests)}. "
    
    # Add preferences
    prefs = kb.get("preferences", {})
    if prefs:
        context += "Preferences: " + "; ".join([f"{k}={v}" for k, v in list(prefs.items())[:3]]) + ". "
    
    return context

def record_memory(memory_type, content):
    """Record important memories about the user."""
    if not current_user:
        return
    
    if current_user not in memory:
        memory[current_user] = {"important_moments": [], "preferences": [], "habits": []}
    
    memory[current_user][memory_type].append({
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    save_json(MEMORY_FILE, memory)

def get_user_insights():
    """Analyze user patterns and return insights."""
    if not current_user:
        return ""
    
    patterns = learning_patterns.get(current_user, {})
    insights = ""
    
    # Analyze question patterns
    questions = patterns.get("questions", [])
    if len(questions) > 3:
        avg_response_length = sum(q["response_length"] for q in questions) / len(questions)
        insights += f"Average response complexity: {int(avg_response_length)} chars. "
    
    # Analyze topics
    topics = patterns.get("topics", [])
    if topics:
        top_topics = topics[-5:]
        insights += f"Recent interests: {', '.join(top_topics)}. "
    
    return insights

def auto_learn_from_conversation(user_input, response):
    """Automatically extract and learn from conversations."""
    learn_from_input(user_input, response)
    
    # Extract preferences from certain keywords
    if "prefer" in user_input.lower() or "like" in user_input.lower():
        if current_user not in knowledge_base:
            knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
        # Extract what they prefer
        add_fact(f"Preference: {user_input}", "preference")
    
    # Track interests
    if "interested in" in user_input.lower() or "love" in user_input.lower():
        topics = learning_patterns.get(current_user, {}).get("topics", [])
        if current_user not in knowledge_base:
            knowledge_base[current_user] = {"facts": [], "preferences": {}, "interests": []}
        for topic in topics[-3:]:
            if topic not in knowledge_base[current_user]["interests"]:
                knowledge_base[current_user]["interests"].append(topic)
    
    save_json(KNOWLEDGE_BASE_FILE, knowledge_base)




def listen():
    """Listen for voice input and convert to text with improved detection."""
    try:
        theme = get_current_theme()
        print(f"{theme['listening']} Listening... (speak now)")
        duration = 10  # Record for up to 10 seconds
        sample_rate = 16000  # 16 kHz sample rate
        
        # Record audio from microphone
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
        
        # Wait for recording with timeout
        sd.wait()
        
        # Check if audio was captured (lowered threshold for better sensitivity)
        max_level = np.max(np.abs(audio_data))
        if max_level < 300:  # Very quiet
            print(f"{theme['error']} No voice detected. Please speak louder or try again.")
            return ""
        
        # Convert numpy array to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_buffer.seek(0)
        
        # Use speech recognition to convert audio to text
        try:
            audio = sr.AudioFile(wav_buffer)
            with audio as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data_sr = recognizer.record(source)
            
            # Try Google Speech Recognition
            text = recognizer.recognize_google(audio_data_sr)
            print(f"{theme['success']} You said: {text}")
            return text
        except sr.UnknownValueError:
            print(f"{theme['error']} Could not understand. Please speak clearly and try again.")
            return ""
        except sr.RequestError as e:
            print(f"{theme['error']} Speech recognition error: {e}")
            return ""
    except Exception as e:
        theme = get_current_theme()
        print(f"{theme['error']} Microphone error: {e}")
        print("Falling back to text input.")
        return input("You: ").strip()


def trim_history(max_messages=20):
    """Keep conversation from getting too long."""
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

    # Guard against empty input
    if not user_input:
        return "Please enter a message."

    # Strip the name if addressed
    user_input = re.sub(r'^[Gg]ratia,?\s*', '', user_input).strip()

    # User authentication commands
    if user_input.lower().startswith("login "):
        parts = user_input[6:].split(" ")
        if len(parts) >= 2:
            username, password = parts[0], " ".join(parts[1:])
            success, message = login_user(username, password)
            return message
        return "Format: login username password"
    
    if user_input.lower().startswith("register "):
        parts = user_input[9:].split(" ")
        if len(parts) >= 2:
            username, password = parts[0], " ".join(parts[1:])
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
    
    # Settings commands
    if user_input.lower().startswith("set "):
        parts = user_input[4:].split(" ", 1)
        if len(parts) == 2:
            success, message = set_setting(parts[0], parts[1])
            return message
        return "Format: set key value"
    
    if user_input.lower().startswith("get "):
        key = user_input[4:].strip()
        value = get_setting(key)
        if value is None:
            return f"Setting '{key}' not found."
        return f"{key}: {value}"
    
    # Task commands
    if user_input.lower().startswith("add task "):
        task_name = user_input[9:].strip()
        success, message = add_task(task_name)
        return message
    
    if user_input.lower() == "list tasks" or user_input.lower() == "tasks":
        return list_tasks()
    
    if user_input.lower().startswith("complete task "):
        try:
            task_num = int(user_input[14:].strip())
            success, message = complete_task(task_num)
            return message
        except ValueError:
            return "Please provide a valid task number."
    
    # Message commands
    if user_input.lower().startswith("message "):
        parts = user_input[8:].split(" ", 1)
        if len(parts) >= 2:
            recipient = parts[0]
            # Ask for subject and message body
            return f"Message system: To send a message, use format: message recipient|subject|body"
        return "Format: message recipient|subject|body"
    
    if user_input.lower().startswith("save message "):
        parts = user_input[13:].split("|")
        if len(parts) >= 3:
            recipient = parts[0].strip()
            subject = parts[1].strip()
            body = parts[2].strip()
            success, message = save_message(recipient, subject, body)
            return message
        return "Format: save message recipient|subject|body"
    
    if user_input.lower() == "list messages" or user_input.lower() == "messages":
        return list_messages()
    
    if user_input.lower().startswith("show message "):
        try:
            msg_num = int(user_input[13:].strip())
            return show_message(msg_num)
        except ValueError:
            return "Please provide a valid message number."
    
    # Learning Brain commands
    if user_input.lower() == "memory":
        if not current_user:
            return "Please login first."
        user_memory = memory.get(current_user, {})
        if not user_memory:
            return "No memories recorded yet."
        result = "📚 Your Memories:\n"
        if user_memory.get("important_moments"):
            result += "Important Moments:\n"
            for moment in user_memory["important_moments"][-3:]:
                result += f"  • {moment['content']}\n"
        if user_memory.get("preferences"):
            result += "Preferences:\n"
            for pref in user_memory["preferences"][-3:]:
                result += f"  • {pref['content']}\n"
        return result
    
    if user_input.lower() == "insights":
        if not current_user:
            return "Please login first."
        insights = get_user_insights()
        learned = get_learned_context()
        return f"🧠 Brain Analysis:\n{insights}\n{learned}"
    
    if user_input.lower().startswith("learn "):
        fact = user_input[6:].strip()
        add_fact(fact, "user_taught")
        record_memory("important_moments", f"Taught: {fact}")
        return f"✓ Learned: {fact}"
    
    if user_input.lower().startswith("remember "):
        item = user_input[9:].strip()
        record_memory("important_moments", item)
        return f"✓ Remembered: {item}"
    
    if user_input.lower() == "what do you know about me":
        if not current_user:
            return "Please login first."
        kb = knowledge_base.get(current_user, {})
        facts = kb.get("facts", [])
        interests = kb.get("interests", [])
        result = "🧠 About You:\n"
        if facts:
            result += f"Facts: {len(facts)} things learned\n"
        if interests:
            result += f"Interests: {', '.join(interests)}\n"
        mem = memory.get(current_user, {})
        if mem.get("important_moments"):
            result += f"Memories: {len(mem['important_moments'])} moments recorded"
        return result
    
    # Theme commands
    if user_input.lower().startswith("theme "):
        theme_name = user_input[6:].strip().lower()
        if theme_name not in THEMES:
            available = ", ".join(THEMES.keys())
            return f"Unknown theme. Available themes: {available}"
        success, message = set_setting("theme", theme_name)
        return f"Theme changed to {THEMES[theme_name]['name']}!"
    
    if user_input.lower() == "themes":
        result = "Available themes:\n"
        for name, theme in THEMES.items():
            result += f"  • {theme['name']} (use: theme {name})\n"
        return result
    
    if user_input.lower() == "help":
        return """
Gratia Commands:
🔐 User: login username password | register username password | logout | whoami
⚙️ Settings: set key value | get key
📋 Tasks: add task name | tasks | complete task number
💬 Messages: save message recipient|subject|body | messages | show message number
🧠 Learning Brain: memory | insights | learn fact text | interests
🎨 Themes: theme space | theme ocean | theme default | themes
🕐 Other: time | voice | exit
        """

    # Simple built-in command
    lower_input = user_input.lower().rstrip('?')
    if lower_input in ["time", "what time is it", "current time"]:
        return f"The current time is: {get_time()}"

    # Append user message first
    messages.append({"role": "user", "content": user_input})

    # Get reply from the selected provider
    if PROVIDER == "anthropic":
        reply = ask_anthropic()
    elif PROVIDER == "openai":
        reply = ask_openai()
    else:
        raise ValueError(f"Unknown provider: '{PROVIDER}'. Choose 'anthropic' or 'openai'.")

    # Append assistant reply, then trim
    messages.append({"role": "assistant", "content": reply})
    trim_history()
    
    # Auto-learn from this interaction
    auto_learn_from_conversation(user_input, reply)
    
    # Log conversation
    if current_user not in conversation_log:
        conversation_log[current_user] = []
    conversation_log[current_user].append({
        "input": user_input,
        "output": reply,
        "timestamp": datetime.now().isoformat()
    })
    save_json(CONVERSATION_LOG_FILE, conversation_log)

    return reply


def main():
    print("Gratia is running (provider: {}). Type 'exit' to quit, 'voice' to toggle voice mode.\n".format(PROVIDER))
    voice_mode = False  # Start with text mode

    while True:
        theme = get_current_theme()
        if voice_mode:
            user_input = listen()
            if not user_input:
                continue
        else:
            user_input = input(f"{theme['prefix']} You: ").strip()

        # Skip blank lines
        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            reply = "Goodbye!"
            print(f"{theme['assistant']} Gratia: {reply}")
            if voice_mode:
                speak(reply)
            break
        elif user_input.lower() == "voice":
            voice_mode = not voice_mode
            status = "enabled" if voice_mode else "disabled"
            reply = f"Voice mode {status}."
            print(f"{theme['assistant']} Gratia: {reply}")
            if voice_mode:
                speak(reply)
            continue

        try:
            reply = ask_ai(user_input)
            print(f"{theme['assistant']} Gratia: {reply}")
            if voice_mode:
                speak(reply)
        except anthropic.APIConnectionError:
            theme = get_current_theme()
            reply = "Could not reach the API. Check your connection."
            print(f"{theme['assistant']} Gratia: {reply}")
            if voice_mode:
                speak(reply)
        except anthropic.AuthenticationError:
            theme = get_current_theme()
            reply = "Invalid API key."
            print(f"{theme['assistant']} Gratia: {reply}")
            if voice_mode:
                speak(reply)
        except Exception as e:
            theme = get_current_theme()
            reply = "Sorry, something went wrong."
            print(f"{theme['assistant']} Gratia: {reply}")
            print(f"{theme['error']} Error: {e}")
            if voice_mode:
                speak(reply)


if __name__ == "__main__":
    main()
"""
Gratia Mobile App - Works Offline
Built with Kivy for iOS/Android deployment
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import threading
import os

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.spinner import Spinner
    from kivy.core.window import Window
    from kivy.uix.popup import Popup
    from kivy.uix.image import Image
    from kivy.clock import Clock
except ImportError as exc:
    print("Gratia Mobile requires Kivy and compatible Kivy dependencies.")
    print("Install Kivy into the current Python environment, or run using the venv311 interpreter:")
    print("  c:\\Users\\Computer\\OneDrive\\venv311\\Scripts\\python.exe gratia_mobile.py")
    print(f"Import error: {exc}")
    sys.exit(1)

# Set window size for mobile simulation
Window.size = (480, 800)

# Offline AI responses
OFFLINE_RESPONSES = {
    "hello": "Hello! I'm Gratia. How can I help you today?",
    "hi": "Hi there! What can I do for you?",
    "how are you": "I'm doing great! How are you?",
    "what time is it": f"The current time is: {datetime.now().strftime('%H:%M:%S')}",
    "help": "Commands:\nghost - Activate Ghost Mode\nsync - Sync with laptop brain\nbrain status - Show second brain state\nlearn <text> - Teach Gratia something\nremember <item> - Save a memory\nvoice - Speak with Gratia\ntheme - Change interface theme",
    "thank you": "You're welcome. Jarvis is always ready.",
    "thanks": "No problem! Anything else I can do?",
    "bye": "Goodbye! See you soon.",
    "exit": "Thanks for using Gratia!",
    "offline": "I'm currently in offline mode. Some features may be limited.",
}

# Theme system
THEMES = {
    "space": {
        "name": "🚀 Space",
        "primary": (10, 14, 39, 1),      # Dark space blue
        "secondary": (26, 58, 82, 1),    # Space button color
        "text": (224, 224, 255, 1),      # Light blue text
        "accent": (42, 120, 255, 1),     # Bright blue accent
    },
    "ocean": {
        "name": "🌊 Ocean",
        "primary": (0, 26, 51, 1),       # Deep ocean
        "secondary": (0, 105, 92, 1),    # Ocean teal
        "text": (179, 229, 252, 1),      # Light cyan
        "accent": (0, 188, 212, 1),      # Cyan accent
    },
    "default": {
        "name": "Default",
        "primary": (240, 240, 240, 1),   # Light gray
        "secondary": (76, 175, 80, 1),   # Green
        "text": (51, 51, 51, 1),         # Dark gray
        "accent": (33, 150, 243, 1),     # Blue accent
    }
}

# Data storage paths
DATA_DIR = Path.home() / ".gratia_mobile"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
CURRENT_USER_FILE = DATA_DIR / "current_user.txt"
SETTINGS_FILE = DATA_DIR / "settings.json"
MEMORY_FILE = DATA_DIR / "memory.json"
GHOST_BRAIN_FILE = DATA_DIR / "ghost_brain.json"

ONE_DRIVE_DIR = Path.home() / "OneDrive"
if not ONE_DRIVE_DIR.exists():
    ONE_DRIVE_DIR = Path.home()
SHARED_BRAIN_FILE = ONE_DRIVE_DIR / "gratia_shared_brain.json"

def load_json(filepath, default=None):
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return default or {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Global state
current_user = None
if CURRENT_USER_FILE.exists():
    with open(CURRENT_USER_FILE, 'r') as f:
        current_user = f.read().strip()

users = load_json(USERS_FILE, {})
settings = load_json(SETTINGS_FILE, {})
memory = load_json(MEMORY_FILE, {})

class GratiaApp(App):
    def build(self):
        self.title = "Gratia - Mobile AI"
        self.theme_name = "default"
        self.current_user = current_user
        self.conversation_history = []
        self.ghost_mode = False
        self.online_available = False
        self.sync_status = "never"
        self.voice_mode = False
        self.brain_data = self.load_user_brain() if self.current_user else {
            "memories": [],
            "goals": [],
            "learning_notes": [],
            "preferences": {},
            "history": []
        }
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_layout.canvas.before.clear()
        
        # Header
        header_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        self.header_label = Label(text="🚀 Gratia Mobile", size_hint_x=0.7, 
                           font_size='20sp', bold=True)
        header_layout.add_widget(self.header_label)
        
        # Theme selector
        self.theme_spinner = Spinner(
            text='Theme',
            values=list(THEMES.keys()),
            size_hint_x=0.3
        )
        self.theme_spinner.bind(text=self.on_theme_changed)
        header_layout.add_widget(self.theme_spinner)
        main_layout.add_widget(header_layout)
        
        # Auth section
        auth_layout = GridLayout(cols=4, size_hint_y=0.08, spacing=5)
        
        self.username_input = TextInput(
            multiline=False,
            hint_text='Your name',
            size_hint_x=0.45,
            background_color=(1, 1, 1, 0.15),
            foreground_color=(1, 1, 1, 1)
        )
        auth_layout.add_widget(self.username_input)
        
        login_btn = Button(text='Activate Jarvis', size_hint_x=0.55, background_color=THEMES['space']['secondary'])
        login_btn.bind(on_press=self.on_login)
        auth_layout.add_widget(login_btn)
        
        main_layout.add_widget(auth_layout)
        
        # Status bar
        self.status_label = Label(
            text=self.get_status(),
            size_hint_y=0.05,
            font_size='12sp'
        )
        main_layout.add_widget(self.status_label)
        
        # Chat history
        scroll = ScrollView(size_hint_y=0.65)
        self.chat_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5,
            padding=5
        )
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        scroll.add_widget(self.chat_layout)
        main_layout.add_widget(scroll)
        
        # Input section
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=5)
        
        self.message_input = TextInput(
            multiline=True,
            hint_text='Type message...',
            size_hint_x=0.75
        )
        input_layout.add_widget(self.message_input)
        
        send_btn = Button(text='Send', size_hint_x=0.25)
        send_btn.bind(on_press=self.on_send_message)
        input_layout.add_widget(send_btn)
        
        main_layout.add_widget(input_layout)
        
        # Bottom buttons
        bottom_layout = BoxLayout(size_hint_y=0.08, spacing=5)
        
        self.voice_btn = Button(text='🔊 Voice', background_color=THEMES['space']['secondary'])
        self.voice_btn.bind(on_press=self.on_toggle_voice)
        bottom_layout.add_widget(self.voice_btn)
        
        sync_btn = Button(text='🔄 Sync', background_color=THEMES['space']['secondary'])
        sync_btn.bind(on_press=self.on_sync)
        bottom_layout.add_widget(sync_btn)
        
        ghost_btn = Button(text='👻 Ghost', background_color=THEMES['space']['secondary'])
        ghost_btn.bind(on_press=self.on_toggle_ghost)
        bottom_layout.add_widget(ghost_btn)
        
        clear_btn = Button(text='Clear', background_color=THEMES['space']['secondary'])
        clear_btn.bind(on_press=self.on_clear_chat)
        bottom_layout.add_widget(clear_btn)
        
        main_layout.add_widget(bottom_layout)
        
        self.apply_theme()
        return main_layout
    
    def apply_theme(self):
        """Apply theme colors to the app"""
        theme = THEMES.get(self.theme_name, THEMES["default"])
        Window.clearcolor = theme["primary"]
        self.header_label.color = theme["text"]
        self.status_label.color = theme["text"]
        self.username_input.foreground_color = theme["text"]
        self.username_input.background_color = (*theme["secondary"][:3], 0.18)
        self.message_input.foreground_color = theme["text"]
        self.message_input.background_color = (*theme["secondary"][:3], 0.14)
        self.theme_spinner.background_color = theme["secondary"]
        self.theme_spinner.color = theme["text"]
        self.voice_btn.background_color = theme["accent"]

    def on_theme_changed(self, spinner, text):
        """Handle theme change"""
        self.theme_name = text
        self.apply_theme()
        self.add_chat_message("System", f"Theme changed to {text}")

    def get_status(self):
        """Get current login status"""
        if self.current_user:
            mode = "Ghost" if self.ghost_mode else "Online" if self.online_available else "Offline"
            return f"{self.current_user} · Mode: {mode} · Brain synced: {self.sync_status}"
        return "Enter your name to activate Gratia"

    def load_user_brain(self):
        all_brains = load_json(GHOST_BRAIN_FILE, {})
        return all_brains.get(self.current_user, {
            "memories": [],
            "goals": [],
            "learning_notes": [],
            "preferences": {},
            "history": []
        })

    def save_user_brain(self):
        all_brains = load_json(GHOST_BRAIN_FILE, {})
        all_brains[self.current_user] = self.brain_data
        save_json(GHOST_BRAIN_FILE, all_brains)

    def check_online_status(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    def merge_brain_data(self, local, shared):
        merged = {
            "memories": list({item["text"] if isinstance(item, dict) else item for item in local.get("memories", []) + shared.get("memories", [])}),
            "goals": list(dict.fromkeys(local.get("goals", []) + shared.get("goals", []))),
            "learning_notes": local.get("learning_notes", []) + shared.get("learning_notes", []),
            "preferences": {**shared.get("preferences", {}), **local.get("preferences", {})},
            "history": local.get("history", []) + shared.get("history", []),
        }
        return merged

    def sync_with_laptop(self, instance=None):
        if not self.current_user:
            self.add_chat_message("System", "Enter your name first.")
            return

        self.online_available = self.check_online_status()
        self.sync_status = "online" if self.online_available else "offline"
        shared_data = load_json(SHARED_BRAIN_FILE, {})
        if self.online_available and BrainSyncManager is not None:
            try:
                manager = BrainSyncManager()
                result = manager.sync_bidirectional()
                self.add_chat_message("System", "Laptop sync complete. Brain intelligence is unified.")
                self.sync_status = "synced"
                return
            except Exception as err:
                self.add_chat_message("System", f"Sync service failed: {err}")

        local_shared = shared_data.get(self.current_user, {})
        merged = self.merge_brain_data(self.brain_data, local_shared)
        shared_data[self.current_user] = merged
        save_json(SHARED_BRAIN_FILE, shared_data)
        self.brain_data = merged
        self.save_user_brain()
        self.sync_status = "synced"
        self.add_chat_message("System", "Ghost sync complete. Your phone and laptop brains are aligned.")

    def on_toggle_ghost(self, instance):
        self.ghost_mode = not self.ghost_mode
        state = "activated" if self.ghost_mode else "deactivated"
        self.add_chat_message("System", f"Ghost mode {state}. I will use local second-brain memory.")
        self.status_label.text = self.get_status()

    def on_sync(self, instance):
        self.sync_with_laptop(instance)

    def speak_text(self, text):
        if not pyttsx3:
            return
        try:
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', 140)
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def listen_for_voice(self):
        if not sr:
            self.add_chat_message("System", "Voice recognition unavailable.")
            return None
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.add_chat_message("System", "Listening... speak now.")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            return recognizer.recognize_google(audio)
        except Exception as err:
            self.add_chat_message("System", f"Voice recognition error: {err}")
            return None

    def on_toggle_voice(self, instance):
        if not self.current_user:
            self.add_chat_message("System", "Enter your name to activate Gratia first.")
            return

        self.voice_mode = not self.voice_mode
        if self.voice_mode:
            self.voice_btn.text = "🔊 Listening..."
            self.add_chat_message("System", "Voice chat activated. Speak now.")
            thread = threading.Thread(target=self.capture_voice_input, daemon=True)
            thread.start()
        else:
            self.voice_btn.text = "🔊 Voice"
            self.add_chat_message("System", "Voice chat disabled.")

    def capture_voice_input(self):
        voice_text = self.listen_for_voice()
        if voice_text:
            Clock.schedule_once(lambda dt: self.add_chat_message("You", voice_text), 0)
            self.process_message(voice_text)
            Clock.schedule_once(lambda dt: self.voice_btn.__setattr__('text', '🔊 Voice'), 0)
            self.voice_mode = False

    def on_login(self, instance):
        username = self.username_input.text.strip()
        if not username:
            self.add_chat_message("System", "Please enter your name to activate Gratia.")
            return

        self.current_user = username
        self.brain_data = self.load_user_brain()
        with open(CURRENT_USER_FILE, 'w') as f:
            f.write(username)

        self.username_input.text = ""
        self.status_label.text = self.get_status()
        self.add_chat_message("System", f"Hello {username}. Jarvis is online and ready.")
        self.save_user_brain()

    def on_show_memory(self, instance):
        """Show memory"""
        if not self.current_user:
            self.add_chat_message("System", "Activate Gratia with your name first.")
            return
        user_mem = self.brain_data
        memories = user_mem.get("memories", [])
        if not memories:
            self.add_chat_message("Gratia", "No memories yet. Use 'learn' or 'remember' commands.")
        else:
            result = "📚 Your Memories:\n"
            for item in memories[-5:]:
                text = item.get("text") if isinstance(item, dict) else str(item)
                result += f"  • {text}\n"
            self.add_chat_message("Gratia", result)
    
    def on_send_message(self, instance):
        """Handle sending a message"""
        message = self.message_input.text.strip()
        if not message:
            return
        
        self.add_chat_message("You", message)
        self.message_input.text = ""
        
        # Process message in thread to avoid freezing
        thread = threading.Thread(target=self.process_message, args=(message,))
        thread.daemon = True
        thread.start()
    
    def process_message(self, message):
        """Process message and get response (works offline)"""
        response = self.get_offline_response(message)
        # Schedule UI update on main Kivy thread
        Clock.schedule_once(lambda dt: self.add_chat_message("Gratia", response), 0)
    
    def get_offline_response(self, user_input):
        """Get response using offline mode (no internet required)"""
        user_input_lower = user_input.lower().strip()

        if not self.current_user:
            return "Activate Gratia by entering your name and pressing Activate Jarvis."

        if user_input_lower in ["ghost", "ghost mode", "go ghost"]:
            self.ghost_mode = True
            self.sync_status = "ghost"
            self.save_user_brain()
            return "Ghost mode activated. I will keep your second brain working locally."

        if user_input_lower in ["online", "connect", "internet"]:
            self.online_available = self.check_online_status()
            self.sync_status = "online" if self.online_available else "offline"
            return "Internet connection detected." if self.online_available else "No internet connection available. Working offline."

        if user_input_lower in ["sync", "sync brain", "sync laptop"]:
            self.sync_with_laptop()
            return "Sync command executed. Your brain data has been merged."

        if user_input_lower.startswith("learn "):
            item = user_input[6:].strip()
            self.brain_data.setdefault("learning_notes", []).append({
                "text": item,
                "timestamp": datetime.now().isoformat(),
                "source": "mobile"
            })
            self.brain_data.setdefault("memories", []).append({
                "text": f"Learned: {item}",
                "timestamp": datetime.now().isoformat()
            })
            self.save_user_brain()
            return f"✓ Jarvis learned: {item}"

        if user_input_lower.startswith("remember "):
            item = user_input[9:].strip()
            self.brain_data.setdefault("memories", []).append({
                "text": item,
                "timestamp": datetime.now().isoformat(),
                "source": "memory"
            })
            self.save_user_brain()
            return f"✓ Remembered: {item}"

        if user_input_lower in ["brain status", "status", "what's my status", "what is my status"]:
            memories = len(self.brain_data.get("memories", []))
            goals = len(self.brain_data.get("goals", []))
            notes = len(self.brain_data.get("learning_notes", []))
            return f"🧠 Brain status: {memories} memories, {goals} goals, {notes} notes. Mode={ 'Ghost' if self.ghost_mode else 'Online' if self.online_available else 'Offline' }."

        if user_input_lower in ["what can you do", "help me", "jarvis"]:
            return (
                "I can remember facts, learn from your input, sync with your laptop, "
                "and run in Ghost Mode without internet. Say 'learn <text>', 'remember <text>', "
                "'sync', 'ghost', or use voice mode."
            )

        response = "I'm in offline mode. Ghost brain is active and I can still think locally. "
        response += "Use 'brain status' or 'sync' to connect with your laptop." if self.ghost_mode else ""
        self.brain_data.setdefault("history", []).append({
            "input": user_input,
            "timestamp": datetime.now().isoformat(),
            "mode": "ghost" if self.ghost_mode else "offline"
        })
        self.save_user_brain()
        return response
    
    def on_toggle_voice(self, instance):
        """Toggle voice mode"""
        self.add_chat_message("System", "🔊 Voice mode toggled (voice features available in full app)")
    
    def on_show_memory(self, instance):
        """Show memory"""
        if not self.current_user:
            self.add_chat_message("System", "Please login first")
            return
        user_mem = memory.get(self.current_user, {})
        if not user_mem:
            self.add_chat_message("Gratia", "No memories yet. Use 'learn' or 'remember' commands.")
        else:
            result = "📚 Your Memories:\n"
            for mem_type, items in user_mem.items():
                if items:
                    result += f"\n{mem_type}:\n"
                    for item in items[-3:]:
                        result += f"  • {item.get('text', item)}\n"
            self.add_chat_message("Gratia", result)
    
    def on_clear_chat(self, instance):
        """Clear chat history"""
        self.chat_layout.clear_widgets()
        self.conversation_history = []
    
    def add_chat_message(self, sender, message):
        """Add a message to chat display"""
        msg_label = Label(
            text=f"[b]{sender}:[/b] {message}",
            size_hint_y=None,
            height=100,
            markup=True,
            text_size=(400, None)
        )
        self.chat_layout.add_widget(msg_label)
        self.conversation_history.append((sender, message))


if __name__ == '__main__':
    app = GratiaApp()
    app.run()

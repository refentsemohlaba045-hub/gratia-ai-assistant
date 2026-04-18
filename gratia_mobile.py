"""
Gratia Mobile App - Works Offline
Built with Kivy for iOS/Android deployment
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.popup import Popup
from kivy.uix.image import Image
import json
import hashlib
from pathlib import Path
from datetime import datetime
import threading
import os

# Set window size for mobile simulation
Window.size = (480, 800)

# Offline AI responses
OFFLINE_RESPONSES = {
    "hello": "Hello! I'm Gratia. How can I help you today?",
    "hi": "Hi there! What can I do for you?",
    "how are you": "I'm doing great! How are you?",
    "what time is it": f"The current time is: {datetime.now().strftime('%H:%M:%S')}",
    "help": "Available commands:\nlogin - Login to your account\nregister - Create new account\nset - Set a preference\nmemory - View your memories\nlearn - Learn something new\ntheme - Change theme",
    "thank you": "You're welcome! Happy to help.",
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
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        main_layout.canvas.before.clear()
        
        # Header
        header_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        header_label = Label(text="🚀 Gratia Mobile", size_hint_x=0.7, 
                           font_size='20sp', bold=True)
        header_layout.add_widget(header_label)
        
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
            hint_text='Username',
            size_hint_x=0.25
        )
        auth_layout.add_widget(self.username_input)
        
        self.password_input = TextInput(
            multiline=False,
            hint_text='Password',
            password=True,
            size_hint_x=0.25
        )
        auth_layout.add_widget(self.password_input)
        
        login_btn = Button(text='Login', size_hint_x=0.25)
        login_btn.bind(on_press=self.on_login)
        auth_layout.add_widget(login_btn)
        
        register_btn = Button(text='Register', size_hint_x=0.25)
        register_btn.bind(on_press=self.on_register)
        auth_layout.add_widget(register_btn)
        
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
        
        voice_btn = Button(text='🔊 Voice')
        voice_btn.bind(on_press=self.on_toggle_voice)
        bottom_layout.add_widget(voice_btn)
        
        memory_btn = Button(text='💾 Memory')
        memory_btn.bind(on_press=self.on_show_memory)
        bottom_layout.add_widget(memory_btn)
        
        logout_btn = Button(text='Logout')
        logout_btn.bind(on_press=self.on_logout)
        bottom_layout.add_widget(logout_btn)
        
        clear_btn = Button(text='Clear')
        clear_btn.bind(on_press=self.on_clear_chat)
        bottom_layout.add_widget(clear_btn)
        
        main_layout.add_widget(bottom_layout)
        
        self.apply_theme()
        return main_layout
    
    def apply_theme(self):
        """Apply theme colors to the app"""
        theme = THEMES.get(self.theme_name, THEMES["default"])
        
    def on_theme_changed(self, spinner, text):
        """Handle theme change"""
        self.theme_name = text
        self.apply_theme()
        self.add_chat_message("System", f"Theme changed to {text}")
    
    def get_status(self):
        """Get current login status"""
        if self.current_user:
            return f"✓ Logged in as: {self.current_user}"
        return "✗ Not logged in"
    
    def on_login(self, instance):
        """Handle login"""
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.add_chat_message("System", "Please enter username and password")
            return
        
        if username not in users:
            self.add_chat_message("System", "User not found. Try registering.")
            return
        
        if users[username]["password"] != hash_password(password):
            self.add_chat_message("System", "Incorrect password")
            return
        
        self.current_user = username
        with open(CURRENT_USER_FILE, 'w') as f:
            f.write(username)
        
        self.username_input.text = ""
        self.password_input.text = ""
        self.status_label.text = self.get_status()
        self.add_chat_message("System", f"Welcome back, {username}!")
    
    def on_register(self, instance):
        """Handle registration"""
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.add_chat_message("System", "Please enter username and password")
            return
        
        if username in users:
            self.add_chat_message("System", "User already exists")
            return
        
        users[username] = {
            "password": hash_password(password),
            "created": datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
        
        self.add_chat_message("System", f"User {username} registered successfully!")
        self.username_input.text = ""
        self.password_input.text = ""
    
    def on_logout(self, instance):
        """Handle logout"""
        self.current_user = None
        if CURRENT_USER_FILE.exists():
            CURRENT_USER_FILE.unlink()
        self.status_label.text = self.get_status()
        self.add_chat_message("System", "Logged out successfully")
    
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
        self.add_chat_message("Gratia", response)
    
    def get_offline_response(self, user_input):
        """Get response using offline mode (no internet required)"""
        user_input_lower = user_input.lower().strip()
        
        # Handle specific commands
        if user_input_lower.startswith("memory"):
            if not self.current_user:
                return "Please login first"
            user_mem = memory.get(self.current_user, {})
            if not user_mem:
                return "No memories recorded yet"
            result = "📚 Your Memories:\n"
            for mem_type, items in user_mem.items():
                if items:
                    result += f"{mem_type}: {len(items)} items\n"
            return result
        
        if user_input_lower.startswith("learn "):
            if not self.current_user:
                return "Please login first"
            fact = user_input[6:].strip()
            if self.current_user not in memory:
                memory[self.current_user] = {}
            if "facts" not in memory[self.current_user]:
                memory[self.current_user]["facts"] = []
            memory[self.current_user]["facts"].append({
                "text": fact,
                "timestamp": datetime.now().isoformat()
            })
            save_json(MEMORY_FILE, memory)
            return f"✓ Learned: {fact}"
        
        if user_input_lower.startswith("remember "):
            if not self.current_user:
                return "Please login first"
            item = user_input[9:].strip()
            if self.current_user not in memory:
                memory[self.current_user] = {}
            if "memories" not in memory[self.current_user]:
                memory[self.current_user]["memories"] = []
            memory[self.current_user]["memories"].append({
                "text": item,
                "timestamp": datetime.now().isoformat()
            })
            save_json(MEMORY_FILE, memory)
            return f"✓ Remembered: {item}"
        
        # Check for keyword matches in offline responses
        for keyword, response in OFFLINE_RESPONSES.items():
            if keyword in user_input_lower:
                return response
        
        # Default offline response
        return "I'm in offline mode. Try asking about time, help, or use 'learn'/'remember' commands to store information locally."
    
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
            text_size=(self.width - 20, None)
        )
        self.chat_layout.add_widget(msg_label)
        self.conversation_history.append((sender, message))


if __name__ == '__main__':
    app = GratiaApp()
    app.run()

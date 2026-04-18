# Gratia - Complete App Suite

Three versions of Gratia are now available:

## 1. Console/CLI Version (Original)
**File**: `import os.py`
**Best for**: Terminal users, automation, scripting

### Run:
```bash
uv run python "c:\Users\Computer\OneDrive\import os.py"
```

### Features:
- Text and voice input/output
- Real-time AI responses (requires internet)
- Theme support (space/ocean)
- User authentication
- Task management
- Message system
- Learning and memory

---

## 2. Desktop GUI App
**File**: `gratia_gui.py`
**Best for**: Windows/Mac/Linux desktop users

### Run:
```bash
uv run python "c:\Users\Computer\OneDrive\gratia_gui.py"
```

### Features:
- Modern graphical interface with buttons
- Chat history display
- Theme dropdown selector
- User login/registration buttons
- Voice mode toggle
- All CLI features with better UX

### Requirements:
```bash
uv pip install tkinter
```

---

## 3. Mobile App (Works Offline!)
**File**: `gratia_mobile.py`
**Best for**: iOS and Android devices

### Run on Desktop (Testing):
```bash
uv pip install kivy
uv run python "c:\Users\Computer\OneDrive\gratia_mobile.py"
```

### Deploy to Phone:
See `MOBILE_DEPLOYMENT.md` for full Android/iOS build instructions

### Features:
- ✅ **WORKS OFFLINE** - No internet required!
- Local user authentication
- Memory and learning system
- Theme customization
- Mobile-optimized interface
- Touch-friendly buttons
- Persistent local data storage
- Cross-platform (iOS & Android)

### Build for Android:
```bash
cd "c:\Users\Computer\OneDrive"
uv pip install buildozer cython
buildozer android debug
```

Output: `bin/gratia_mobile-1.0-debug.apk`

---

## Quick Comparison

| Feature | CLI | Desktop | Mobile |
|---------|-----|---------|--------|
| **Works Offline** | No | No | ✅ Yes |
| **Voice Support** | ✅ Yes | ✅ Yes | Ready |
| **GUI** | No | ✅ Yes | ✅ Yes |
| **Mobile** | No | No | ✅ Yes |
| **AI Responses** | ✅ Online AI | ✅ Online AI | Local fallback |
| **Themes** | ✅ Yes | ✅ Yes | ✅ Yes |
| **User Accounts** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Memory System** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cross-platform** | ✅ Any | ✅ Any | ✅ iOS/Android |

---

## Recommended Use Cases

### **Use CLI Version When:**
- Working in terminal/PowerShell
- Running in headless environment
- Building automation scripts
- Want full feature set with online AI

### **Use Desktop GUI When:**
- On Windows/Mac/Linux
- Want visual interface
- Need easy theme/voice toggle
- Prefer clicking buttons

### **Use Mobile App When:**
- On iPhone or Android
- Need offline functionality
- Want to use on the go
- Don't want to rely on internet

---

## Installation Summary

### 1. Install Dependencies
```bash
cd "c:\Users\Computer"
uv pip install tkinter kivy buildozer cython
```

### 2. Set API Keys (for online AI only)
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key-here"
$env:OPENAI_API_KEY = "your-key-here"
```

### 3. Create Test User
```bash
# Using any version, register:
register refentse puv57MQN
```

### 4. Run Your Chosen Version
```bash
# CLI
uv run python "c:\Users\Computer\OneDrive\import os.py"

# Desktop GUI
uv run python "c:\Users\Computer\OneDrive\gratia_gui.py"

# Mobile (desktop test)
uv run python "c:\Users\Computer\OneDrive\gratia_mobile.py"
```

---

## Data Storage

All three apps share the same data directory:

```
~/.gratia/              # CLI and GUI data
  ├── users.json
  ├── settings.json
  ├── memory.json
  └── conversation_log.json

~/.gratia_mobile/       # Mobile app data (isolated)
  ├── users.json
  ├── settings.json
  └── memory.json
```

**Note**: Mobile app has separate storage to avoid conflicts.

---

## Next Steps

1. **Test all three versions** to see which you prefer
2. **Deploy mobile app** using buildozer for Android/iOS
3. **Customize themes** by editing THEMES dictionary
4. **Add features** like file storage or calendar integration

---

## Support Matrix

| Issue | Solution |
|-------|----------|
| CLI not responding | Check if waiting for voice input, press Ctrl+C |
| GUI window frozen | Wait a moment, AI requests can take time |
| Mobile app crashes | Check Python 3.8+, reinstall Kivy |
| Theme not changing | Restart app to see theme changes |
| User auth failing | Check username/password spelling |
| No API responses | Verify ANTHROPIC_API_KEY is set |

---

## File Manifest

```
c:\Users\Computer\OneDrive\
├── import os.py                    # CLI version (main)
├── gratia_gui.py                   # Desktop GUI
├── gratia_mobile.py                # Mobile app
├── MOBILE_DEPLOYMENT.md            # Build instructions
└── QUICKSTART.md                   # This file

~/.gratia/                          # Shared data (CLI/GUI)
~/.gratia_mobile/                   # Mobile data
```

---

**Enjoy using Gratia in all its forms! 🚀🌊**

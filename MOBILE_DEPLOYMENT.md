# Gratia Mobile App - Deployment Guide

## Overview
This guide explains how to deploy the Gratia mobile app to iOS and Android using Kivy and Buildozer.

## Features
- ✅ Works completely offline (no internet required)
- ✅ User authentication with local storage
- ✅ Memory and learning system
- ✅ Space and Ocean themes
- ✅ Voice support ready (with additional setup)
- ✅ Cross-platform (iOS & Android)

## Prerequisites

### Windows Setup
```powershell
# Install Kivy and Buildozer
uv pip install kivy buildozer cython

# For Android deployment, install JDK and Android SDK
# Download from: https://www.oracle.com/java/technologies/javase-downloads.html
# Download Android SDK: https://developer.android.com/studio
```

### macOS Setup
```bash
# Install Kivy and Buildozer
uv pip install kivy buildozer cython

# Install dependencies
brew install python3 pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer
```

### Linux Setup
```bash
# Install dependencies
sudo apt-get install python3-dev python3-pip build-essential git libffi-dev libssl-dev
uv pip install kivy buildozer cython

# Additional packages
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

## Testing on Desktop

### Run the desktop version:
```bash
uv run python "c:\Users\Computer\OneDrive\gratia_mobile.py"
```

This runs the app in a desktop window (480x800) simulating mobile size.

## Building for Android

### Step 1: Create buildozer.spec
```bash
cd "c:\Users\Computer\OneDrive"
buildozer android debug
```

### Step 2: Configure buildozer.spec
Edit the generated `buildozer.spec`:

```ini
[app]
title = Gratia Mobile
package.name = gratia_mobile
package.domain = com.example
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
requirements = python3,kivy,pyjnius

[buildozer]
log_level = 2
android.permissions = INTERNET,RECORD_AUDIO,ACCESS_FINE_LOCATION
android.api = 31
android.minapi = 21
android.ndk = 25b
```

### Step 3: Build APK
```bash
buildozer android debug
```

The APK will be in the `bin/` folder. Transfer to Android device and install.

## Building for iOS

### Requirements
- macOS only
- Xcode installed
- Kivy iOS dependencies

### Build Steps
```bash
# Install Kivy for iOS
pip install kivy-ios

# Build the app
buildozer ios debug
```

This creates an Xcode project that you can further customize and deploy to the App Store.

## File Structure

```
gratia_mobile.py          # Main app code (works offline)
gratia_gui.py            # Desktop GUI version
import os.py             # Console CLI version
buildozer.spec           # Build configuration
~/.gratia_mobile/        # Data storage (local)
  ├── users.json         # User accounts
  ├── current_user.txt   # Active session
  ├── settings.json      # User preferences
  └── memory.json        # Learned facts and memories
```

## Data Storage

All user data is stored locally on the device:
- User accounts and passwords (hashed)
- User memories and learned facts
- Theme preferences
- Conversation history

**No data is sent to the cloud** - everything works offline!

## Offline Features

The mobile app works completely offline with:
- Local user authentication
- Memory system (learn, remember commands)
- Theme customization
- Built-in response library for common queries
- Local data persistence

## Adding Online Features Later

To add online AI responses in the future:

1. Add network connectivity check:
```python
from kivy.network import UrlRequest

def has_internet():
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False
```

2. Wrap API calls with fallback:
```python
if has_internet():
    response = ask_anthropic(message)
else:
    response = get_offline_response(message)
```

## Testing Checklist

- [ ] Register new user
- [ ] Login with credentials
- [ ] Change theme (space/ocean)
- [ ] Use learn command
- [ ] Use remember command
- [ ] View memory
- [ ] Clear chat history
- [ ] Logout
- [ ] Test without internet

## Troubleshooting

### "Kivy not found"
```bash
uv pip install kivy
```

### "Buildozer not found"
```bash
uv pip install buildozer cython
```

### Android SDK issues
1. Download Android Studio
2. Set ANDROID_SDK_ROOT environment variable
3. Accept all licenses in SDK Manager

### App crashes on startup
- Check that ANTHROPIC_API_KEY and OPENAI_API_KEY are not required for offline mode
- Verify `~/.gratia_mobile/` directory exists
- Check Python version compatibility (3.8+)

## Performance Tips

1. **Reduce bundle size**: Remove unused assets
2. **Optimize images**: Use PNG/WebP instead of large images
3. **Cache data**: Use local JSON storage instead of repeated API calls
4. **Threading**: Long operations run on separate threads to prevent UI freezing

## Security Notes

- Passwords are hashed with SHA256
- No credentials stored in plain text
- No data transmitted online
- All storage is local and private

## Future Enhancements

- [ ] Add offline ML model for better responses
- [ ] Implement dark mode
- [ ] Add push notifications
- [ ] Support multiple languages
- [ ] Add backup/sync to cloud (optional)
- [ ] Implement file sharing
- [ ] Add camera integration
- [ ] Voice input/output (with text-to-speech)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Kivy documentation: https://kivy.org/doc/
3. Check Buildozer docs: https://buildozer.readthedocs.io/

---

**Happy Building! 🚀**

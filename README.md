# Apple TV Game Remote

A cross-platform mobile remote control app for Apple TV gaming, built with Kivy and Python.

## Overview

This app turns your Android phone/tablet (or iPhone in the future) into a game controller for Apple TV. It replicates the gaming capabilities of the Siri Remote including:

- **Touch Surface** - Swipe gestures for navigation and gameplay
- **Motion Controls** - Accelerometer and gyroscope for tilt-based gaming
- **Game Buttons** - A, B, X, Y buttons plus D-pad
- **Standard Remote Controls** - Menu, Home, Play/Pause, Volume

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KIVY MOBILE APP                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Touch Pad   │  │ Game Buttons│  │ Motion Sensors          │  │
│  │ (Gestures)  │  │ (A/B/X/Y)   │  │ (Accelerometer/Gyro)    │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│                    ┌─────▼─────┐                                 │
│                    │ Command   │                                 │
│                    │ Processor │                                 │
│                    └─────┬─────┘                                 │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   pyatv     │  (Apple TV Protocol)
                    │   Library   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Apple TV   │
                    │  (tvOS)     │
                    └─────────────┘
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| UI Framework | Kivy 2.3+ |
| Apple TV Communication | pyatv |
| Sensors (Android) | Plyer |
| Sensors (iOS) | Pyobjus |
| Build (Android) | Buildozer |
| Build (iOS) | kivy-ios |

## Project Structure

```
appletv-game-remote/
├── src/
│   ├── main.py                 # Application entry point
│   ├── app.py                  # Main Kivy App class
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── home.py             # Device discovery/connection
│   │   ├── remote.py           # Basic remote control
│   │   └── game_controller.py  # Game controller mode
│   ├── services/
│   │   ├── __init__.py
│   │   ├── apple_tv_service.py # pyatv wrapper service
│   │   ├── sensor_service.py   # Accelerometer/Gyroscope
│   │   └── haptic_service.py   # Vibration feedback
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── touch_pad.py        # Touch surface widget
│   │   ├── dpad.py             # D-pad widget
│   │   ├── game_buttons.py     # A/B/X/Y buttons
│   │   └── analog_stick.py     # Virtual analog stick
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # App configuration
│       └── credentials.py      # Credential storage
├── assets/
│   ├── fonts/
│   ├── images/
│   └── sounds/
├── tests/
│   ├── test_apple_tv_service.py
│   ├── test_touch_pad.py
│   └── test_sensor_service.py
├── buildozer.spec              # Android build config
├── requirements.txt
└── README.md
```

## Features

### Controller Modes

1. **Navigation Mode** - Standard remote for browsing
2. **Game Mode** - Full game controller with motion

### Input Mapping

| Input | Apple TV Function |
|-------|-------------------|
| Touch swipe | Navigate / Look around |
| Touch tap | Select |
| Touch hold | Secondary action |
| Button A | Primary action |
| Button B | Back / Cancel |
| Menu | Menu |
| Tilt (motion) | Steering / Tilt control |

## Getting Started

### Prerequisites

- Python 3.10+ (Python 3.11 or 3.12 recommended for Android builds)
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- Docker (recommended for Android builds)
- Xcode (for iOS builds, macOS only)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd appletv-game-remote

# Install dependencies with uv
uv sync

# Run on desktop (for development)
uv run altremote
# or with debug logging:
make run-debug
```

### Quick Reference

```bash
make help          # Show all available commands
make run           # Run the app locally (desktop)
make test          # Run tests
make lint          # Run linter
make android       # Build Android APK (Docker)
make ios-build     # Build iOS app (macOS only)
```

---

## Building for Android

### Option 1: Docker Build (Recommended)

Docker builds avoid Python version conflicts and dependency issues. This is the most reliable method.

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

```bash
# Build debug APK
make android
# or explicitly:
make android-docker

# Build release APK
make android-docker-release
```

The APK will be created in `bin/altremote-0.1.0-arm64-v8a_armeabi-v7a-debug.apk`

**First build takes longer** as it downloads Android SDK, NDK, and compiles dependencies. Subsequent builds are much faster.

### Option 2: Local Build

For local builds, you need Python 3.11 or 3.12 (buildozer doesn't support Python 3.13+).

```bash
# Check requirements
make android-requirements

# Setup and build locally
make android-local
```

### Deploying to Android Device via USB

1. **Enable Developer Options** on your Android device:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings → Developer Options
   - Enable "USB Debugging"

2. **Connect your device** via USB and authorize the connection when prompted

3. **Deploy the APK:**
```bash
# Deploy and run
make android-deploy

# Or manually with adb:
adb install bin/altremote-0.1.0-arm64-v8a_armeabi-v7a-debug.apk

# Launch the app
adb shell am start -n com.example.altremote/org.kivy.android.PythonActivity
```

4. **View logs:**
```bash
make android-logcat
# or:
adb logcat | grep -i python
```

### Running on Android Emulator

1. **Install Android Studio** and create an AVD (Android Virtual Device)

2. **Start the emulator:**
```bash
# List available emulators
emulator -list-avds

# Start an emulator
emulator -avd <avd_name>
```

3. **Deploy to emulator:**
```bash
# The emulator appears as a regular device
adb devices
adb install bin/altremote-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

**Note:** Network features (Apple TV discovery) may not work in emulators. Use a physical device for full testing.

---

## Building for iOS (macOS only)

iOS builds require macOS with Xcode installed.

### Setup iOS Toolchain

```bash
# Install kivy-ios and build dependencies (takes a while)
make ios-setup
```

This installs:
- kivy-ios toolchain
- Python 3 for iOS
- Kivy framework
- pyatv dependencies

### Build iOS App

```bash
make ios-build
```

This creates an Xcode project at `altremote-ios/altremote.xcodeproj`

### Running on iOS Simulator

```bash
# Open the Xcode project
make ios-simulator
```

Then in Xcode:
1. Select a simulator device (e.g., iPhone 15)
2. Click the Run button (▶)

### Deploying to iOS Device via USB

1. **Connect your iPhone/iPad** via USB

2. **Open the Xcode project:**
```bash
open altremote-ios/altremote.xcodeproj
```

3. **Configure signing:**
   - Select the project in Xcode
   - Go to "Signing & Capabilities"
   - Select your Team (requires Apple Developer account)
   - Enable "Automatically manage signing"

4. **Select your device** from the device dropdown

5. **Click Run** (▶) to build and deploy

**Note:** For distribution, you'll need an Apple Developer account ($99/year).

---

## Development Workflow

### Desktop Development

The fastest way to develop and test UI:

```bash
# Run with hot reload (just restart when needed)
make run

# Run with debug logging
make run-debug

# View Kivy logs
make logs
```

### Testing

```bash
# Run all tests
make test

# Run linter
make lint

# Format code
make format

# Type checking
make typecheck
```

### Clean Build Artifacts

```bash
# Clean Python cache
make clean

# Clean Android build
make android-clean

# Clean iOS build
make ios-clean

# Clean everything
make clean-all
```

---

## Troubleshooting

### Android Build Issues

**"API target 33 is not available"**
- The buildozer.spec is configured for API 31 for compatibility
- If you need a different API, edit `buildozer.spec` and set `android.api`

**Docker permission errors on macOS**
- These `chown` warnings are normal and can be ignored
- The build will continue successfully

**Python version errors**
- Local builds require Python 3.11 or 3.12
- Use Docker builds (`make android`) to avoid this

### iOS Build Issues

**"kivy-ios not found"**
- Run `make ios-setup` first

**Code signing errors**
- Ensure you have a valid Apple Developer account
- Check Xcode signing settings

### Runtime Issues

**"Apple TV not found"**
- Ensure your phone and Apple TV are on the same network
- Check that the Apple TV is awake (not in sleep mode)
- Try restarting the Apple TV

**"Pairing failed"**
- Make sure you enter the PIN displayed on the TV correctly
- Try removing the app from Apple TV's paired devices and re-pair

## Protocol Details

This app uses the **Companion Protocol** via the pyatv library to communicate with Apple TV. Modern Apple TVs (tvOS 15+) require this protocol for full functionality. The protocol supports:

- Device discovery via Bonjour/mDNS
- Secure pairing with PIN
- Remote control commands
- Touch/swipe gestures
- Volume control
- Game controller input

### Pairing Process

1. App discovers Apple TV on local network
2. User selects device to connect
3. PIN displayed on Apple TV screen
4. User enters PIN in app
5. Credentials stored securely (persisted across app restarts)

## Limitations

- **No native MFi controller support**: This is a software remote, not a hardware controller
- **Latency**: Network latency may affect gameplay for fast-paced games
- **Game compatibility**: Some games may require an actual MFi controller

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## License

MIT License - see LICENSE for details

## Acknowledgments

- [pyatv](https://github.com/postlund/pyatv) - Apple TV protocol implementation
- [Kivy](https://kivy.org) - Cross-platform Python framework
- [Plyer](https://github.com/kivy/plyer) - Platform-independent APIs

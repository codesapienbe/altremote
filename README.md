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

- Python 3.9+
- Kivy 2.3+
- pyatv 0.14+
- Android SDK (for Android builds)
- Xcode (for iOS builds)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd appletv-game-remote

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run on desktop (for development)
python src/main.py
```

### Building for Android

```bash
# Install buildozer
pip install buildozer

# Build APK
buildozer android debug

# Build and deploy
buildozer android debug deploy run
```

### Building for iOS

```bash
# Clone kivy-ios
git clone https://github.com/kivy/kivy-ios
cd kivy-ios

# Build toolchain
./toolchain.py build kivy pyobjus

# Create Xcode project
./toolchain.py create AppTVRemote ../appletv-game-remote/src
```

## Protocol Details

This app uses the **Media Remote Protocol (MRP)** via the pyatv library to communicate with Apple TV. The protocol supports:

- Device discovery via Bonjour/mDNS
- Secure pairing with PIN
- Remote control commands
- Touch/swipe gestures
- Volume control

### Pairing Process

1. App discovers Apple TV on local network
2. User initiates pairing
3. PIN displayed on Apple TV screen
4. User enters PIN in app
5. Credentials stored securely for future use

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

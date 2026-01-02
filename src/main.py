#!/usr/bin/env python3
"""
Apple TV Game Remote - Entry Point

A mobile remote control app for Apple TV gaming.
"""

from .app import AppleTVRemoteApp


def main():
    """Application entry point."""
    AppleTVRemoteApp().run()


if __name__ == '__main__':
    main()

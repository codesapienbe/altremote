# Apple TV Game Remote - Cross-Platform Build Makefile
# Supports: Desktop (macOS/Linux/Windows), Android, iOS

.PHONY: all help install run clean test lint format \
        desktop android ios \
        android-debug android-release android-deploy android-logcat \
        ios-setup ios-build ios-simulator \
        deps deps-dev deps-build \
        docker-android

# Default target
all: help

# =============================================================================
# Configuration
# =============================================================================

PYTHON := python3
UV := uv
APP_NAME := altremote
VERSION := 0.1.0
SRC_DIR := src
BUILD_DIR := .buildozer
BIN_DIR := bin

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# Help
# =============================================================================

help:
	@echo "$(CYAN)Apple TV Game Remote - Build System$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install      - Install dependencies with uv"
	@echo "  make run          - Run the app locally (desktop)"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "$(GREEN)Desktop Builds:$(NC)"
	@echo "  make desktop      - Package for current desktop platform"
	@echo ""
	@echo "$(GREEN)Android Builds:$(NC)"
	@echo "  make android              - Build debug APK (Docker, recommended)"
	@echo "  make android-docker       - Build debug APK via Docker"
	@echo "  make android-docker-release - Build release APK via Docker"
	@echo "  make android-local        - Build debug APK locally (Python 3.11/3.12)"
	@echo "  make android-deploy       - Deploy APK to connected device"
	@echo "  make android-logcat       - View Android logs"
	@echo "  make android-clean        - Clean Android build"
	@echo ""
	@echo "$(GREEN)iOS Builds:$(NC)"
	@echo "  make ios-setup     - Setup iOS toolchain"
	@echo "  make ios-build     - Build iOS app"
	@echo "  make ios-simulator - Run in iOS Simulator"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-android - Build Android APK in Docker"
	@echo ""

# =============================================================================
# Development
# =============================================================================

install:
	@echo "$(CYAN)Installing dependencies...$(NC)"
	$(UV) sync

deps:
	@echo "$(CYAN)Installing runtime dependencies...$(NC)"
	$(UV) add kivy pyatv plyer zeroconf cryptography pyyaml keyring

deps-dev:
	@echo "$(CYAN)Installing dev dependencies...$(NC)"
	$(UV) add --dev pytest pytest-asyncio pytest-cov ruff mypy

deps-build:
	@echo "$(CYAN)Installing build dependencies...$(NC)"
	$(UV) add --dev buildozer cython pillow

run:
	@echo "$(CYAN)Running $(APP_NAME)...$(NC)"
	$(UV) run $(APP_NAME)

run-debug:
	@echo "$(CYAN)Running $(APP_NAME) with debug logging...$(NC)"
	KIVY_LOG_LEVEL=debug $(UV) run $(APP_NAME)

test:
	@echo "$(CYAN)Running tests...$(NC)"
	$(UV) run pytest tests/ -v --cov=$(SRC_DIR) --cov-report=term-missing

lint:
	@echo "$(CYAN)Running linter...$(NC)"
	$(UV) run ruff check $(SRC_DIR)

format:
	@echo "$(CYAN)Formatting code...$(NC)"
	$(UV) run ruff format $(SRC_DIR)

typecheck:
	@echo "$(CYAN)Running type checker...$(NC)"
	$(UV) run mypy $(SRC_DIR)

# =============================================================================
# Cleaning
# =============================================================================

clean:
	@echo "$(CYAN)Cleaning build artifacts...$(NC)"
	rm -rf $(BUILD_DIR)
	rm -rf $(BIN_DIR)
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean android-clean ios-clean
	@echo "$(GREEN)Full clean complete!$(NC)"

# =============================================================================
# Desktop Builds
# =============================================================================

desktop:
	@echo "$(CYAN)Creating desktop package...$(NC)"
	$(UV) run pyinstaller --onefile \
		--name $(APP_NAME) \
		--add-data "$(SRC_DIR)/data:data" \
		$(SRC_DIR)/main.py
	@echo "$(GREEN)Desktop build complete! Check dist/$(NC)"

desktop-macos: desktop
	@echo "$(CYAN)Creating macOS app bundle...$(NC)"
	# Additional macOS packaging can be added here

desktop-linux: desktop
	@echo "$(CYAN)Creating Linux AppImage...$(NC)"
	# AppImage creation can be added here

# =============================================================================
# Android Builds (Docker recommended for reliability)
# =============================================================================

# Docker-based Android build (recommended - avoids Python version conflicts)
android: android-docker

android-docker:
	@echo "$(CYAN)Building Android debug APK via Docker...$(NC)"
	@mkdir -p $(BIN_DIR)
	docker run --rm \
		-v $(PWD):/home/user/hostcwd \
		-e BUILDOZER_WARN_ON_ROOT=0 \
		--entrypoint="" \
		kivy/buildozer:latest \
		bash -c "cd /home/user/hostcwd && buildozer android debug"
	@echo "$(GREEN)APK created in $(BIN_DIR)/$(NC)"

android-docker-release:
	@echo "$(CYAN)Building Android release APK via Docker...$(NC)"
	@mkdir -p $(BIN_DIR)
	docker run --rm \
		-v $(PWD):/home/user/hostcwd \
		-e BUILDOZER_WARN_ON_ROOT=0 \
		--entrypoint="" \
		kivy/buildozer:latest \
		bash -c "cd /home/user/hostcwd && buildozer android release"
	@echo "$(GREEN)Release APK created in $(BIN_DIR)/$(NC)"

# Local buildozer setup (alternative - requires Python 3.11 or 3.12)
PYTHON_FOR_BUILDOZER := $(shell command -v python3.11 2>/dev/null || command -v python3.12 2>/dev/null || echo "python3")

android-local-setup:
	@echo "$(CYAN)Setting up buildozer locally (requires Python 3.11/3.12)...$(NC)"
	@echo "Using Python: $(PYTHON_FOR_BUILDOZER)"
	@echo "$(YELLOW)Note: Docker build (make android-docker) is recommended for reliability$(NC)"
	$(PYTHON_FOR_BUILDOZER) -m pip install --user buildozer cython
	@echo "$(GREEN)Buildozer ready!$(NC)"

android-local: android-local-setup
	@echo "$(CYAN)Building Android debug APK locally...$(NC)"
	@mkdir -p $(BIN_DIR)
	$(PYTHON_FOR_BUILDOZER) -m buildozer android debug
	@echo "$(GREEN)APK created in $(BIN_DIR)/$(NC)"

android-deploy:
	@echo "$(CYAN)Deploying to Android device...$(NC)"
	buildozer android deploy run || $(PYTHON_FOR_BUILDOZER) -m buildozer android deploy run

android-logcat:
	@echo "$(CYAN)Showing Android logs...$(NC)"
	adb logcat | grep -i python

android-clean:
	@echo "$(CYAN)Cleaning Android build...$(NC)"
	rm -rf $(BUILD_DIR)/android
	rm -rf $(BIN_DIR)/*.apk
	@echo "$(GREEN)Android clean complete!$(NC)"

android-requirements:
	@echo "$(CYAN)Checking Android build requirements...$(NC)"
	@echo "Required tools:"
	@echo "  - Java JDK 11+ (for buildozer)"
	@echo "  - Android SDK (auto-downloaded by buildozer)"
	@echo "  - Android NDK (auto-downloaded by buildozer)"
	@echo "  - pipx (recommended for buildozer)"
	@command -v java >/dev/null 2>&1 && echo "  $(GREEN)✓ Java found$(NC)" || echo "  $(RED)✗ Java not found$(NC)"
	@command -v pipx >/dev/null 2>&1 && echo "  $(GREEN)✓ pipx found$(NC)" || echo "  $(YELLOW)! pipx not found (install with: brew install pipx)$(NC)"
	@command -v buildozer >/dev/null 2>&1 && echo "  $(GREEN)✓ buildozer found$(NC)" || echo "  $(YELLOW)! buildozer not found (will install on first build)$(NC)"

# =============================================================================
# iOS Builds (macOS only)
# =============================================================================

ios-setup:
	@echo "$(CYAN)Setting up iOS toolchain...$(NC)"
ifeq ($(shell uname),Darwin)
	@echo "Installing kivy-ios..."
	pip install kivy-ios
	@echo "Building iOS dependencies (this takes a while)..."
	toolchain build python3 kivy
	toolchain build pyatv
else
	@echo "$(RED)iOS builds are only supported on macOS$(NC)"
	@exit 1
endif

ios-build:
	@echo "$(CYAN)Building iOS app...$(NC)"
ifeq ($(shell uname),Darwin)
	toolchain create $(APP_NAME) $(SRC_DIR)
	@echo "$(GREEN)iOS project created! Open $(APP_NAME)-ios/$(APP_NAME).xcodeproj$(NC)"
else
	@echo "$(RED)iOS builds are only supported on macOS$(NC)"
	@exit 1
endif

ios-simulator:
	@echo "$(CYAN)Running in iOS Simulator...$(NC)"
ifeq ($(shell uname),Darwin)
	@echo "Open the Xcode project and run in simulator"
	open $(APP_NAME)-ios/$(APP_NAME).xcodeproj
else
	@echo "$(RED)iOS Simulator is only available on macOS$(NC)"
	@exit 1
endif

ios-clean:
	@echo "$(CYAN)Cleaning iOS build...$(NC)"
	rm -rf $(APP_NAME)-ios
	rm -rf .kivy-ios
	@echo "$(GREEN)iOS clean complete!$(NC)"

# =============================================================================
# Docker Builds (for CI/CD)
# =============================================================================

docker-android:
	@echo "$(CYAN)Building Android APK in Docker...$(NC)"
	docker run --rm -v $(PWD):/app -w /app \
		kivy/buildozer \
		buildozer android debug
	@echo "$(GREEN)Docker Android build complete!$(NC)"

# =============================================================================
# CI/CD Helpers
# =============================================================================

ci-install:
	@echo "$(CYAN)CI: Installing dependencies...$(NC)"
	pip install uv
	$(UV) sync

ci-test:
	@echo "$(CYAN)CI: Running tests...$(NC)"
	$(UV) run pytest tests/ -v --junitxml=test-results.xml

ci-lint:
	@echo "$(CYAN)CI: Running linter...$(NC)"
	$(UV) run ruff check $(SRC_DIR) --output-format=github

# =============================================================================
# Version Management
# =============================================================================

version:
	@echo "$(APP_NAME) v$(VERSION)"

bump-patch:
	@echo "$(CYAN)Bumping patch version...$(NC)"
	# Version bump logic here

bump-minor:
	@echo "$(CYAN)Bumping minor version...$(NC)"
	# Version bump logic here

bump-major:
	@echo "$(CYAN)Bumping major version...$(NC)"
	# Version bump logic here

# =============================================================================
# Release
# =============================================================================

release: clean test lint android-release
	@echo "$(GREEN)Release build complete!$(NC)"
	@echo "Artifacts:"
	@ls -la $(BIN_DIR)/

# =============================================================================
# Development Shortcuts
# =============================================================================

dev: install run

quick: run

logs:
	@tail -f ~/.kivy/logs/kivy_*.txt 2>/dev/null || echo "No Kivy logs found"

# Platform detection for conditional builds
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
endif
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
endif

info:
	@echo "$(CYAN)Build Information$(NC)"
	@echo "  Platform: $(PLATFORM)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  UV: $(shell $(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "  App: $(APP_NAME) v$(VERSION)"

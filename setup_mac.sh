#!/bin/bash

echo "Setting up Chessable Course Builder..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    echo "You can use: brew install python"
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "pip is not installed. Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Homebrew dependencies for CairoSVG
if command -v brew &> /dev/null; then
    echo "Installing Cairo dependencies with Homebrew..."
    brew install cairo pango
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Make scripts executable
chmod +x run_gui.sh
chmod +x chessable_gui.py
chmod +x split_pgn_for_chessable.py

echo "Setup complete! Run ./run_gui.sh to start the application."

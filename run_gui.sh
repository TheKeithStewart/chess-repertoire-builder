#!/bin/bash

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Make sure the GUI script is executable
chmod +x chessable_gui.py

# Check if we have Python with Tkinter support
if command -v /opt/homebrew/bin/python3 &> /dev/null; then
    # Use the Homebrew Python that should have Tkinter support
    PYTHON=/opt/homebrew/bin/python3
else
    # Fallback to system Python
    PYTHON=python3
fi

# Create a dedicated virtual environment for the GUI if it doesn't exist
GUI_VENV="gui_venv"
if [ ! -d "$GUI_VENV" ]; then
    echo "Creating a virtual environment for the GUI..."
    $PYTHON -m venv $GUI_VENV
fi

# Activate the virtual environment
source $GUI_VENV/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install python-chess pillow cairosvg

# Run the GUI
python chessable_gui.py

# Deactivate the virtual environment
deactivate

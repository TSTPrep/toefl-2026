#!/bin/bash
# Quick activation script for speaker detection virtual environment
# Usage: source activate_venv.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "Python: $(which python)"
    echo "Pip: $(which pip)"
    echo ""
    echo "To deactivate: deactivate"
else
    echo "❌ Virtual environment not found. Run: python -m venv venv"
fi

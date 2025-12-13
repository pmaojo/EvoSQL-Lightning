#!/bin/bash
# run_app.sh
# reliable launcher using the local virtual environment

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Check if venv exists
if [ -d ".venv" ]; then
    echo "✅ Using local .venv environment..."
    ./.venv/bin/python -m streamlit run src/components/ui.py
else
    echo "⚠️  .venv not found. Trying global python..."
    python3 -m streamlit run src/components/ui.py
fi

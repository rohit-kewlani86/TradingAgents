#!/bin/bash

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Define the path to the Python executable
PYTHON_EXEC="/usr/local/bin/python3"

# Check if the correct Python exists
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "Warning: Python executable not found at $PYTHON_EXEC"
    echo "Using default python3..."
    PYTHON_EXEC="python3"
fi

# Function to display usage
show_help() {
    echo "TradingAgents Startup Script"
    echo ""
    echo "Usage: ./start.sh [options]"
    echo ""
    echo "Options:"
    echo "  --cli       Run the interactive CLI (default)"
    echo "  --script    Run the main.py script directly"
    echo "  --install   Install/update dependencies before running"
    echo "  --help      Show this help message"
    echo ""
}

# Parse arguments
RUN_MODE="cli"
INSTALL_DEPS=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --cli) RUN_MODE="cli" ;;
        --script) RUN_MODE="script" ;;
        --install) INSTALL_DEPS=true ;;
        --help) show_help; exit 0 ;;
        *) echo "Unknown parameter passed: $1"; show_help; exit 1 ;;
    esac
    shift
done

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo "Installing dependencies..."
    $PYTHON_EXEC -m pip install -e .
fi

# Run the selected mode
if [ "$RUN_MODE" = "cli" ]; then
    echo "Starting TradingAgents CLI..."
    $PYTHON_EXEC -m cli.main
elif [ "$RUN_MODE" = "script" ]; then
    echo "Starting TradingAgents via main.py..."
    $PYTHON_EXEC main.py
fi

#!/bin/bash

# Palette wrapper script that loads .env file
# This ensures environment variables are available even when called directly

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a  # Export all variables
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Also check current directory for .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Run palette with all arguments
exec palette "$@"
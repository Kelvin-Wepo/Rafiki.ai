#!/bin/bash
# Render.com build script for Rafiki.ai backend

echo "Starting Render build process..."

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

# Create necessary directories
echo "Creating asset directories..."
mkdir -p backend/assets/avatars
mkdir -p backend/assets/avatar_cache

# Check if default avatar exists, if not create a placeholder
if [ ! -f "backend/assets/avatars/rafiki_avatar.png" ]; then
    echo "Note: Default avatar image not found. Upload via Render shell or include in repo."
fi

echo "Build complete!"

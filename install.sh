#!/bin/bash
# Installation script for Hugging Face Spaces

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

# Install langchain-core separately to ensure it's installed
echo "Installing langchain-core..."
pip install langchain-core>=0.1.0

echo "Installation complete."
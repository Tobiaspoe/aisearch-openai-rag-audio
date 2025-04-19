#!/bin/bash

# Define the zip name
ZIP_NAME="app.zip"

# Remove any existing zip
rm -f "$ZIP_NAME"

# Zip only the necessary parts of the app
zip -r "$ZIP_NAME" app/ \
  -x "**/node_modules/*" \
     "**/__pycache__/*" \
     "**/*.wav" \
     "**/.git/*" \
     "**/.env" \
     "**/venv/*" \
     "**/.DS_Store"

echo "✅ Successfully zipped to $ZIP_NAME"


#!/bin/bash

# Define zip name
ZIP_NAME="app.zip"

# Remove existing zip if it exists
rm -f "$ZIP_NAME"

# Zip the entire app folder from root
zip -r "$ZIP_NAME" app/ \
  -x "app/frontend/node_modules/*" \
     "app/backend/__pycache__/*" \
     "app/backend/*.wav"

echo "✅ Zipped app folder into $ZIP_NAME"

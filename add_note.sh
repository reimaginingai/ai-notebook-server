#!/bin/bash

# Check if at least one note argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <note> [notebook] [folder] [device_id]"
    exit 1
fi

# Combine all arguments into a single note string
NOTE="$1"
NOTEBOOK="$2"
FOLDER="$3"
DEVICE_ID="${4:-test_user}"
# Send the POST request with the note, notebook, and folder
curl -X POST \
-H "Content-Type: application/json" \
-d '{
    "device_id": "'"$DEVICE_ID"'",
    "note": "'"$NOTE"'",
    "notebook": "'"$NOTEBOOK"'",
    "folder": "'"$FOLDER"'"
}' http://localhost:5000/add_note

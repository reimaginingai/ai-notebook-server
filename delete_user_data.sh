#!/bin/bash

# Check if device_id is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <device_id>"
    exit 1
fi

DEVICE_ID=$1
SERVER_URL="http://localhost:5000/delete_notes/$DEVICE_ID"

# Send DELETE request
curl -X DELETE "$SERVER_URL"

# Check the response
if [ $? -eq 0 ]; then
    echo "Successfully deleted all notes for Device ID: $DEVICE_ID"
else
    echo "Failed to delete notes for Device ID: $DEVICE_ID"
fi

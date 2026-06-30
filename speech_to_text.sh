#!/bin/bash

# Check if an audio file argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <audio_file>"
    exit 1
fi

# Get the audio file from the first argument
AUDIO_FILE="$1"

# Check if audio file exists
if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found!"
    exit 1
fi

# Send the POST request with the audio file
curl -X POST -F "audio=@$AUDIO_FILE" http://localhost:5000/speech_to_text

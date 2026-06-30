#!/bin/bash

# Check if a note argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <user>"
    exit 1
fi

# Combine all arguments into a single note string
USER="$*"

curl -X GET "http://localhost:5000/get_user_notes?device_id=$USER"


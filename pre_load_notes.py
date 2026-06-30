#!/usr/bin/env python3

import csv
import sys
import subprocess
from time import sleep
from os import system
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("USAGE: ./pre_load_notes.py notes_csv_file device_id")
        print("NOTE: Daniel can help you get the device_id")
        sys.exit(1)
    with open(sys.argv[1], newline='') as csvfile:
        notes_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in notes_reader:
            print(f'./add_note.sh "{row[1]}" "{row[0]}" "Notes" "{sys.argv[2]}"')
            subprocess.run(["./add_note.sh", row[1], row[0], "Notes", sys.argv[2]])
            print(', '.join(row))

import os
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
import firebase_admin
import subprocess
from firebase_admin import credentials, db
import logging
import os
import json
from server.model.retrieval_model import encode_sentence, get_encoding_similarities, get_top_k_indices
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Initialize Firebase
private_key = os.environ.get("PRIVATE_KEY")
firebase_credentials = json.loads(private_key)
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notebookai-79e56-default-rtdb.firebaseio.com/'
})

@app.route('/add_note', methods=['POST'])
def add_note():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    folder = json_string.get("folder")
    notebook = json_string.get("notebook")
    note = json_string.get("note")
    
    app.logger.info("\n")

    if not device_id or not note:
        app.logger.error("Add Note: Device ID and note are required")
        return jsonify({"error": "Device ID and note are required"}), 400
    
    if not folder:
        app.logger.warning("Add Note: Folder not found, assigning default")
        folder = "default"
    
    if not notebook:
        app.logger.warning("Add Note: Notebook not found, assigning defualt")
        notebook = "default"
    
    note_embedding = encode_sentence(note)

    ref = db.reference(f'notes/{device_id}')
    
    # FIXME: Duplicate notes are not always unintentional, maybe make some type of time threshold between requests?
    if os.environ.get("DUPLICATE_NOTE_CHECKING") == "TRUE":
        try:
            existing_notes = ref.order_by_child('note').equal_to(note).get()
        except Exception as e:
            app.logger.error(f"Error checking for existing notes: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

        if existing_notes:
            app.logger.warning(f"Add Note: Duplicate note found for Device ID: {device_id}")
            return jsonify({"error": "Duplicate note found"}), 409  # Conflict status code

    try:
        new_note_ref = ref.push({
            'note': note,
            'embedding': note_embedding,
            'folder': folder,
            'notebook': notebook
        })
        note_id = new_note_ref.key
    except Exception as e:
        app.logger.error(f"Error adding note to database: {str(e)}")
        return jsonify({"error": "Failed to get add note"}), 500  # Internal Server Error

    app.logger.info(f"{device_id} Added Note: '{note}'")

    return jsonify({"id": note_id}), 201

@app.route('/get_response', methods=['POST'])
def get_response():
    app.logger.info("\n")

    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    question = json_string.get("question")
    try:
        k = int(json_string.get("k"))
    except Exception as e:
        app.logger.warning(" Ask Question: K parameter not specified. Returning top answer")
        k = 1

    if not device_id or not question:
        app.logger.error("Ask Question: Device ID and note are required")
        return jsonify({"error": "Device ID and question are required"}), 400
    
    # Load all notes from Firebase
    ref = db.reference(f'notes/{device_id}')
    notes_data = ref.get()

    if notes_data is None:
        app.logger.warning("Ask Question: No note data found, returning empty list")
        return jsonify([]), 200  # Return an empty list if no notes
    
    try:
        # Extract embeddings and calculate similarities
        question_embedding = encode_sentence(question)        

        app.logger.info(f"{device_id} Asked Question: '{question}'")

        note_embeddings = []
        notes = []    # <--
        note_ids = [] # <-- ts probably ass idk how to fix
        folders = []  # <--
        notebooks = []# <--
        for key, value in notes_data.items():
            notes.append(value['note'])
            note_embeddings.append(value['embedding'])
            folders.append(value['folder'])
            notebooks.append(value['notebook'])
            note_ids.append(key)

        similarities = get_encoding_similarities(question_embedding, note_embeddings)
        k = min(k, len(notes)) # make sure k isn't too high
        top_indices, top_values = get_top_k_indices(similarities, k)
        
        top_answers = [notes[i] for i in top_indices[0].tolist()]
        top_ids = [note_ids[i] for i in top_indices[0].tolist()]
        top_folders = [folders[i] for i in top_indices[0].tolist()]
        top_notebooks = [notebooks[i] for i in top_indices[0].tolist()]
   
    except Exception as e:
        app.logger.error(f"Error getting question response: {str(e)}")
        return jsonify({"error": "Failed to get question response"}), 500  # Internal Server Error
    
    app.logger.info(f"{device_id} Got Response: '{top_answers}'")

    response = [{"id": top_ids[i], "answer": top_answers[i], "folder": top_folders[i], "notebook": top_notebooks[i]} for i in range(len(top_answers))]

    return jsonify(response), 200

@app.route('/prepopulate_notes', methods=['GET'])
def prepopulate_notes():
    device_id = request.args.get('device_id')  # Get device ID from query parameters
    notes_file = request.args.get('notes_file')  # The file of notes to preload

    app.logger.info("\n")
    print(device_id, notes_file)
    subprocess.run(["./pre_load_notes.py", notes_file, device_id])
    if not device_id:
        app.logger.error("Get User Notes: Device ID is required")
        return jsonify({"error": "Device ID is required"}), 400
    if not notes_file:
        app.logger.error("Prepopulate Notes: Notes File is required")
        return jsonify({"error": "Notes File is required"}), 400

    return jsonify([]), 200  # Return an empty list if no notes

@app.route('/get_user_notes', methods=['GET'])
def get_user_notes():
    device_id = request.args.get('device_id')  # Get device ID from query parameters

    app.logger.info("\n")

    if not device_id:
        app.logger.error("Get User Notes: Device ID is required")
        return jsonify({"error": "Device ID is required"}), 400

    ref = db.reference(f'notes/{device_id}')
    notes_data = ref.get()

    if notes_data is None:
        app.logger.warning("Get User Notes: No note data found, returning empty list")
        return jsonify([]), 200  # Return an empty list if no notes

    notes = [{
        'id': key,
        'note': value['note'],
        'folder': value['folder'],
        'notebook': value['notebook']
    } for key, value in notes_data.items()]

    num_notes = len(notes)

    app.logger.info(f"Get User Notes: Got {num_notes} notes for Device ID: {device_id}")
    
    return jsonify(notes), 200

@app.route('/delete_user_notes/<device_id>', methods=['DELETE'])
def delete_user_notes(device_id):
    # Reference to the notes for the specific device ID
    ref = db.reference(f'notes/{device_id}')

    app.logger.info("\n")
    
    # Attempt to delete the notes
    try:
        ref.delete()  # This will delete all entries under the specified device ID
        app.logger.info(f"Deleted all notes for Device ID: {device_id}")
        return jsonify({"message": "All notes deleted successfully"}), 204  # No Content status
    except Exception as e:
        app.logger.error(f"Error deleting notes for Device ID: {device_id}: {str(e)}")
        return jsonify({"error": "Failed to delete notes"}), 500  # Internal Server Error
    
@app.route('/delete_note/<device_id>/<note_id>', methods=['DELETE'])
def delete_note(device_id, note_id):
    # Reference to the specific note for the device ID
    ref = db.reference(f'notes/{device_id}/{note_id}')

    app.logger.info("\n")
    
    # Attempt to delete the specific note
    try:
        ref.delete()  # This will delete the specific note under the specified device ID
        app.logger.info(f"Deleted note ID: {note_id} for Device ID: {device_id}")
        return jsonify({"message": f"Note ID: {note_id} deleted successfully"}), 204  # No Content status
    except Exception as e:
        app.logger.error(f"Error deleting note ID: {note_id} for Device ID: {device_id}: {str(e)}")
        return jsonify({"error": "Failed to delete note"}), 500  # Internal Server Error
    
@app.route('/update_note', methods=['PUT'])
def update_note():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    note_id = json_string.get("note_id")      # Get note ID from the request
    new_note_text = json_string.get("note")   # Get the new note text from the request

    app.logger.info("\n")

    if not device_id or not note_id or not new_note_text:
        app.logger.error("Update Note: Device ID, Note ID, and new note text are required")
        return jsonify({"error": "Device ID, Note ID, and new note text are required"}), 400

    # Reference to the specific note using device_id and note_id
    ref = db.reference(f'notes/{device_id}/{note_id}')

    if ref.get() is None:
        app.logger.error(f"Update Note: Note ID {note_id} not found for Device ID: {device_id}")
        return jsonify({"error": "Note not found"}), 404  # Not Found status

    try:
        # Retrieve the original note text
        original_note_data = ref.get()
        original_note_text = original_note_data.get('note')

        # Check if the new note text is the same as the original
        if original_note_text == new_note_text:
            app.logger.info(f"No update needed for Note ID: {note_id} as the text is unchanged.")
            return jsonify({"message": "No update needed; the note text is unchanged."}), 200  # OK status

        # Update the note text in Firebase
        ref.update({'note': new_note_text})
        new_note_embedding = encode_sentence(new_note_text)
        ref.update({'embedding': new_note_embedding})
        app.logger.info(f"Updated Note: '{new_note_text}' for Device ID: {device_id} and Note ID: {note_id}")
        return jsonify({"message": "Note updated successfully"}), 200  # OK status
    except Exception as e:
        app.logger.error(f"Error updating note for Device ID: {device_id}, Note ID: {note_id}: {str(e)}")
        return jsonify({"error": "Failed to update note"}), 500  # Internal Server Error
    
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    app.logger.info("\n")

    json_string = request.get_json()

    try:
        username = json_string.get("username") 
        question = json_string.get("question")
        answer = json_string.get("answer")
        is_pair = int(json_string.get("is_pair"))
    except Exception as e:
        app.logger.error(f"Error parsing info: {str(e)}")
        return jsonify({"error": "Error parsing info"}), 500
    
    if not username or not question or not answer:
        app.logger.error("Submit Feedback: Missing info")
        return jsonify({"error": "Missing info"}), 400
    
    if is_pair == 1:
        app.logger.info(f"Got positive pair: {question} - {answer} by {username}")
    else:
        app.logger.info(f"Got negative pair: {question} - {answer} by {username}")
        
    ref = db.reference(f'qa-pairs/')
    try:
        ref.push({
            'question': question,
            'answer': answer,
            'username': username, 
            'is_pair': is_pair
        })
    except Exception as e:
        app.logger.error(f"Error adding qa pair to database: {str(e)}")
        return jsonify({"error": "Failed to add qa pair"}), 500  # Internal Server Error
   
    return '', 200

from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
import logging
import os
import json
from server.model.retrieval_model import encode_sentence, get_encoding_similarities
from server.model.stt_model import speech_to_text

app = Flask(__name__)

# Initialize Firebase
private_key = os.environ.get("PRIVATE_KEY")
firebase_credentials = json.loads(private_key)
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://notebookai-79e56-default-rtdb.firebaseio.com/'
})

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s] - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

@app.route('/add_note', methods=['POST'])
def add_note_db():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    folder = json_string.get("folder")
    notebook = json_string.get("notebook")
    note = json_string.get("note")
    
    logger.info("\n")

    if not device_id or not note:
        logger.error("Add Note: Device ID and note are required")
        return jsonify({"error": "Device ID and note are required"}), 400
    
    if not folder:
        logger.warning("Add Note: Folder not found, assigning default")
        folder = "default"
    
    if not notebook:
        logger.warning("Add Note: Notebook not found, assigning defualt")
        notebook = "default"
    
    note_embedding = encode_sentence(note)

    # FIXME: Duplicate notes are not always unintentional, maybe make some type of time threshold between requests?
    ref = db.reference(f'notes/{device_id}')
    try:
        existing_notes = ref.order_by_child('note').equal_to(note).get()
    except Exception as e:
        logger.error(f"Error checking for existing notes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    if existing_notes:
        logger.warning(f"Add Note: Duplicate note found for Device ID: {device_id}")
        return jsonify({"error": "Duplicate note found"}), 409  # Conflict status code

    ref.push({
        'note': note,
        'embedding': note_embedding,
        'folder': folder,
        'notebook': notebook
    })

    logger.info(f"{device_id} Added Note: '{note}'")

    return '', 204

@app.route('/get_response', methods=['POST'])
def get_response_db():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    question = json_string.get("question")
    
    if not device_id or not question:
        logger.error("Ask Question: Device ID and note are required")
        return jsonify({"error": "Device ID and question are required"}), 400
    
    # Load all notes from Firebase
    ref = db.reference(f'notes/{device_id}')
    notes_data = ref.get()

    if notes_data is None:
        logger.warning("Ask Question: No note data found, returning empty list")
        return jsonify([]), 200  # Return an empty list if no notes

    # Extract embeddings and calculate similarities
    question_embedding = encode_sentence(question)

    logger.info("\n")
    logger.info(f"{device_id} Asked Question: '{question}'")

    note_embeddings = []
    notes = []
    for key, value in notes_data.items():
        notes.append(value['note'])
        note_embeddings.append(value['embedding'])

    similarities = get_encoding_similarities(question_embedding, note_embeddings)
    
    # Find closest match in the database
    max_val, max_idx = similarities.max(1)
    answer = notes[max_idx]


    logger.info(f"{device_id} Got Response: '{answer}'")
    return jsonify({"response": answer}), 200

@app.route('/get_user_notes', methods=['GET'])
def get_user_notes():
    device_id = request.args.get('device_id')  # Get device ID from query parameters

    logger.info("\n")

    if not device_id:
        logger.error("Get User Notes: Device ID is required")
        return jsonify({"error": "Device ID is required"}), 400

    ref = db.reference(f'notes/{device_id}')
    notes_data = ref.get()

    if notes_data is None:
        logger.warning("Get User Notes: No note data found, returning empty list")
        return jsonify([]), 200  # Return an empty list if no notes

    notes = [{
        'id': key,
        'note': value['note'],
        'folder': value['folder'],
        'notebook': value['notebook']
    } for key, value in notes_data.items()]

    logger.info(f"Get User Notes: Got notes for Device ID: {device_id}")
    
    return jsonify(notes), 200

@app.route('/sync_database', methods=['POST'])
def sync_database_db():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    notes = json_string.get("notes")

    logger.info("\n")
    
    if not device_id or not isinstance(notes, list):
        logger.error("Sync Database: Device ID and notes list are required")
        return jsonify({"error": "Device ID and notes list are required"}), 400

    logger.info(f"Sync Database: Syncing notes for Device ID: {device_id}")
    
    # Clear existing notes in Firebase
    ref = db.reference(f'notes/{device_id}')
    ref.delete()  # Deletes all existing notes

    for note in notes:
        note_embedding = encode_sentence(note)
        # Save note and its embedding to Firebase
        ref.push({
            'note': note,
            'embedding': note_embedding
        })
    return '', 200

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text_db():

    logger.info("\n")

    if 'audio' not in request.files:
        logger.error("STT: No audio file provided")
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        logger.error("STT: No file selected")
        return jsonify({'error': 'No file selected'}), 400
    
    text_result = speech_to_text(audio_file)
    
    return jsonify({'text': text_result}), 200

@app.route('/delete_notes/<device_id>', methods=['DELETE'])
def delete_notes(device_id):
    # Reference to the notes for the specific device ID
    ref = db.reference(f'notes/{device_id}')

    logger.info("\n")
    
    # Attempt to delete the notes
    try:
        ref.delete()  # This will delete all entries under the specified device ID
        logger.info(f"Deleted all notes for Device ID: {device_id}")
        return jsonify({"message": "All notes deleted successfully"}), 204  # No Content status
    except Exception as e:
        logger.error(f"Error deleting notes for Device ID: {device_id}: {str(e)}")
        return jsonify({"error": "Failed to delete notes"}), 500  # Internal Server Error
    
@app.route('/update_note', methods=['PUT'])
def update_note_db():
    json_string = request.get_json()
    device_id = json_string.get("device_id")  # Get device ID from the request
    note_id = json_string.get("note_id")      # Get note ID from the request
    new_note_text = json_string.get("note")   # Get the new note text from the request

    logger.info("\n")

    if not device_id or not note_id or not new_note_text:
        logger.error("Update Note: Device ID, Note ID, and new note text are required")
        return jsonify({"error": "Device ID, Note ID, and new note text are required"}), 400

    # Reference to the specific note using device_id and note_id
    ref = db.reference(f'notes/{device_id}/{note_id}')

    if ref.get() is None:
            logger.error(f"Update Note: Note ID {note_id} not found for Device ID: {device_id}")
            return jsonify({"error": "Note not found"}), 404  # Not Found status

    try:
        # Update the note text in Firebase
        ref.update({'note': new_note_text})
        logger.info(f"Updated Note: '{new_note_text}' for Device ID: {device_id} and Note ID: {note_id}")
        return jsonify({"message": "Note updated successfully"}), 200  # OK status
    except Exception as e:
        logger.error(f"Error updating note for Device ID: {device_id}, Note ID: {note_id}: {str(e)}")
        return jsonify({"error": "Failed to update note"}), 500  # Internal Server Error
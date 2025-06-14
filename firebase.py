from flask import Flask, request, jsonify, Response
import pyrebase
import os
from dotenv import load_dotenv
import base64
import mimetypes
from datetime import datetime

load_dotenv()

app = Flask(__name__)

firebase_config = {
    "apiKey": os.getenv('FIREBASE_API_KEY'),
    "authDomain": os.getenv('FIREBASE_AUTH_DOMAIN'),
    "projectId": os.getenv('FIREBASE_PROJECT_ID'),
    "storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.getenv('FIREBASE_APP_ID'),
    "measurementId": os.getenv('FIREBASE_MEASUREMENT_ID'),
    "databaseURL": f"https://{os.getenv('FIREBASE_PROJECT_ID')}-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()  

@app.route('/')
def index():
    return jsonify({"message": "SecureVault Realtime DB API"})

@app.route('/api/vault', methods=['GET'])
def get_vault_items():
    try:
        items = db.child("vault").get()  
        if items.val():
            vault_items = []
            for key, value in items.val().items():
                vault_items.append({
                    'id': key,
                    **value
                })
            return jsonify(vault_items)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault', methods=['POST'])
def add_vault_item():
    try:
        print("POST request received") 
        data = {}
        if request.is_json:
            data = request.json
        elif request.form or request.files:
            data = request.form.to_dict()
        else:
            print("No JSON or form data found")
        
        file = request.files.get('file')
        if file:
            file_content = file.read()
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            data['file_name'] = file.filename
            data['file_extension'] = file_extension
            data['file_type'] = mime_type
            data['file_size'] = len(file_content)
            data['file_content'] = file_base64
            data['title'] = file.filename if not data.get('title') else data['title']
            data['uploaded_at'] = datetime.now().isoformat()
            
            print(f"File info - Name: {file.filename}, Type: {mime_type}, Size: {len(file_content)} bytes")
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        result = db.child("vault").push(data)
        
        return jsonify({"message": "Item added successfully", "id": result['name']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault/<item_id>', methods=['DELETE'])
def delete_vault_item(item_id):
    try:
        db.child("vault").child(item_id).remove()  # Change this
        return jsonify({"message": "Item deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault/<item_id>/download-file', methods=['GET'])
def download_file_direct(item_id):
    try:
        item = db.child("vault").child(item_id).get()
        if not item.val():
            return jsonify({"error": "Item not found"}), 404
        
        item_data = item.val()
        
        if 'file_content' not in item_data:
            return jsonify({"error": "No file content found"}), 404
        
        file_content = base64.b64decode(item_data['file_content'])
        
        return Response(
            file_content,
            mimetype=item_data.get('file_type', 'application/octet-stream'),
            headers={
                "Content-Disposition": f"attachment; filename={item_data.get('file_name', 'download')}"
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['username', 'userid', 'public_key']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        user_data = {
            'username': data['username'],
            'userid': data['userid'],
            'public_key': data['public_key']
        }
        
        result = db.child("users").push(user_data)
        
        return jsonify({"message": "User added successfully", "id": result['name']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
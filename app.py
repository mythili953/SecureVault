from flask import Flask, request, render_template, jsonify, Response
import base64
import cv2
import numpy as np
from src.face_recognition_system import FaceRecognitionSystem
from collections import defaultdict
from src.encryption import key_manager
import string
import random
import pyrebase
import os
from dotenv import load_dotenv
import mimetypes
from datetime import datetime

load_dotenv()

app = Flask(__name__)
face_system = FaceRecognitionSystem()
image_buffer = defaultdict(list)

# Firebase configuration
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

# Main application routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/upload_captured_images', methods=['POST'])
def upload_captured_images():
    """Handle uploaded images from webcam capture"""
    try:
        data = request.get_json()
        name = data.get('name')
        images = data.get('images', [])
        
        if not name or not images:
            return jsonify({'success': False, 'message': 'Name and images are required'})
        image_buffer[name] = []
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        processed_faces = []
        
        for i, image_data in enumerate(images):
            try:
                if ',' in image_data:
                    encoded = image_data.split(",", 1)[1]
                else:
                    encoded = image_data
            
                image_bytes = base64.b64decode(encoded)
                np_array = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                
                if img is None:
                    print(f"Warning: Could not decode image {i}")
                    continue
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(faces) > 0:
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    (x, y, w, h) = largest_face
                
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                
                    processed_faces.append(face_roi)
                    
            except base64.binascii.Error as e:
                print(f"Base64 decode error for image {i}: {e}")
                continue
            except Exception as e:
                print(f"Error processing image {i}: {e}")
                continue
        
        if len(processed_faces) >= 10:  
            image_buffer[name] = processed_faces  
            
            return jsonify({
                'success': True, 
                'message': f'Successfully processed {len(processed_faces)} face images for {name}',
                'images_processed': len(processed_faces)
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Only {len(processed_faces)} valid face images found. Please ensure your face is clearly visible.',
                'images_processed': len(processed_faces)
            })
            
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/register_face', methods=['POST'])
def register_face():
    """Register face using captured images"""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        if name not in image_buffer or len(image_buffer[name]) < 10:
            return jsonify({'success': False, 'message': 'Not enough images captured. Please capture images first.'})

        face_images = image_buffer[name]
        success = face_system.register_face(name, face_images)
        user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        public_key = key_manager.generate_keys(user_id)
        
        # Handle public key conversion
        if isinstance(public_key, bytes):
            public_key_str = public_key.decode('utf-8')
        else:
            public_key_str = str(public_key)
        
        print(f"Generated public key for {name}: {public_key_str}")

        # Store user data directly in Firebase
        try:
            user_data = {
                'username': name,
                'userid': user_id,
                'public_key': public_key_str,
                'created_at': datetime.now().isoformat()
            }
            
            result = db.child("users").push(user_data)
            print(f"User data stored in Firebase with ID: {result['name']}")
            
        except Exception as firebase_error:
            print(f"Firebase error: {firebase_error}")
        
        if success:
            image_buffer[name] = []
            return jsonify({'success': True, 'message': f'Face registered successfully for {name}'})
        else:
            return jsonify({'success': False, 'message': 'Face registration failed'})
            
    except Exception as e:
        print(f"Error in register_face: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_capture_status/<name>')
def get_capture_status(name):
    """Get current capture status for a user"""
    count = len(image_buffer.get(name, []))
    return jsonify({'images_captured': count, 'total_needed': 50})

@app.route('/authenticate')
def authenticate():
    return render_template("authenticate.html")

@app.route('/list_users')
def list_users():
    """Get list of registered users"""
    try:
        users = face_system.get_registered_users()
        json_safe_users = []
        for user in users:
            json_safe_users.append({
                'id': int(user['id']),
                'name': str(user['name']),
                'face_count': int(user['face_count'])
            })
        return jsonify({'success': True, 'users': json_safe_users})
    except Exception as e:
        print(f"Error in list_users: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/authenticate_face', methods=['POST'])
def authenticate_face():
    """Authenticate a face from uploaded image"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Image is required'})
    
        if ',' in image_data:
            encoded = image_data.split(",", 1)[1]
        else:
            encoded = image_data
        
        image_bytes = base64.b64decode(encoded)
        np_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': 'Could not decode image'})
        
        result = face_system.authenticate_face_from_image(img)
        
        if result:
            return jsonify({
                'success': True, 
                'message': f'Welcome back, {result["name"]}!',
                'user': {
                    'name': str(result['name']),
                    'confidence': float(result['confidence']),
                    'confidence_percent': float(result['confidence_percent']),
                    'user_id': int(result['user_id'])
                }
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Face not recognized. Please try again or register first.'
            })
            
    except Exception as e:
        print(f"Error in authenticate_face: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# Firebase API routes
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
        db.child("vault").child(item_id).remove()
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
        
        # Handle public_key if it's in bytes format
        public_key = data['public_key']
        if isinstance(public_key, bytes):
            public_key = public_key.decode('utf-8')
        elif isinstance(public_key, str) and public_key.startswith("b'"):
            # Handle string representation of bytes
            public_key = public_key[2:-1]  # Remove b' and '
        
        user_data = {
            'username': data['username'],
            'userid': data['userid'],
            'public_key': public_key,
            'created_at': datetime.now().isoformat()
        }
        
        result = db.child("users").push(user_data)
        
        return jsonify({"message": "User added successfully", "id": result['name']})
    except Exception as e:
        print(f"Firebase error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = db.child("users").get()
        if users.val():
            user_list = []
            for key, value in users.val().items():
                user_list.append({
                    'id': key,
                    **value
                })
            return jsonify(user_list)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8001)
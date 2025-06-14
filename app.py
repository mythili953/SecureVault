from flask import Flask, request, render_template, jsonify, Response
from src.face_recognition_system import FaceRecognitionSystem
from collections import defaultdict
from src.encryption import key_manager
from dotenv import load_dotenv
from datetime import datetime
from src.encryption.web_crypto_utils import encrypt_file_for_users, decrypt_file_for_user, get_current_user_id
import os
import pyrebase
import mimetypes
import json

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

@app.route('/vault')
def vault():
    return render_template("vault.html")

@app.route('/authenticate')
def authenticate():
    return render_template("authenticate.html")

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
            vault_list = []
            for key, item in items.val().items():
                item['id'] = key
                vault_list.append(item)
            return jsonify(vault_list)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault', methods=['POST'])
def add_vault_item():
    try:
        print("POST request received")
        
        # Get form data
        data = request.form.to_dict()
        file = request.files.get('file')
        
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        # Read file content and encode as base64
        file_content = file.read()
        import base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Get file info
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        vault_data = {
            'title': data.get('title', file.filename),
            'file_name': file.filename,
            'file_content': encoded_content,
            'file_extension': file_extension,
            'file_type': mime_type,
            'file_size': len(file_content),
            'uploaded_at': datetime.now().isoformat()
        }
        
        # Store in Firebase
        result = db.child("vault").push(vault_data)
        
        return jsonify({"message": "File uploaded successfully", "id": result['name']})
        
    except Exception as e:
        print(f"Error in add_vault_item: {e}")
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
            return jsonify({"error": "File not found"}), 404
        
        item_data = item.val()
        
        # Decode base64 content
        import base64
        file_content = base64.b64decode(item_data['file_content'])
        
        return Response(
            file_content,
            mimetype=item_data.get('file_type', 'application/octet-stream'),
            headers={"Content-Disposition": f"attachment; filename={item_data.get('file_name', 'download')}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        
        # Generate key pair for the user
        key_pair = key_manager.generate_key_pair()
        
        # Store public key in Firebase, private key locally
        public_key_pem = key_manager.serialize_public_key(key_pair['public_key'])
        key_manager.store_private_key(data['userid'], key_pair['private_key'])
        
        user_data = {
            'username': data['username'],
            'userid': data['userid'],
            'public_key': public_key_pem,
            'created_at': datetime.now().isoformat()
        }
        
        result = db.child("users").push(user_data)
        return jsonify({"message": "User created successfully", "id": result['name']})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = db.child("users").get()
        if users.val():
            user_list = []
            for key, user_data in users.val().items():
                user_list.append({
                    'id': key,
                    'username': user_data.get('username'),
                    'userid': user_data.get('userid'),
                    'created_at': user_data.get('created_at')
                })
            return jsonify(user_list)
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault/encrypted', methods=['POST'])
def add_encrypted_vault_item():
    try:
        print("Encrypted POST request received")
        
        # Get form data
        data = request.form.to_dict()
        file = request.files.get('file')
        recipients_json = request.form.get('recipients')
        
        if not file:
            return jsonify({"error": "No file provided"}), 400
            
        if not recipients_json:
            return jsonify({"error": "No recipients specified"}), 400
        
        # Parse recipients
        try:
            recipients = json.loads(recipients_json)
        except:
            return jsonify({"error": "Invalid recipients format"}), 400
        
        # Get current user ID
        current_username = data.get('current_user')
        if not current_username:
            return jsonify({"error": "Current user not identified"}), 400
            
        sender_user_id = get_current_user_id(current_username)
        if not sender_user_id:
            return jsonify({"error": "Sender user ID not found"}), 400
        
        # Read file content
        file_content = file.read()
        
        # Get recipient user IDs
        recipient_user_ids = [r['userid'] for r in recipients]
        
        # Encrypt file for all recipients
        encrypted_data = encrypt_file_for_users(file_content, sender_user_id, recipient_user_ids)
        
        # Prepare data for storage
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        vault_data = {
            'title': data.get('title', file.filename),
            'file_name': file.filename,
            'file_extension': file_extension,
            'file_type': mime_type,
            'file_size': len(file_content),
            'uploaded_at': datetime.now().isoformat(),
            'sender_id': sender_user_id,
            'sender_username': current_username,
            'recipients': recipients,
            'is_encrypted': True,
            'encrypted_data': encrypted_data
        }
        
        # Store in Firebase
        result = db.child("vault").push(vault_data)
        
        return jsonify({
            "message": "Encrypted file uploaded successfully", 
            "id": result['name'],
            "recipients": len(recipients)
        })
        
    except Exception as e:
        print(f"Encryption upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vault/<item_id>/decrypt', methods=['POST'])
def decrypt_vault_item(item_id):
    try:
        # Get current user info
        current_username = request.json.get('current_user') if request.is_json else None
        
        if not current_username:
            current_username = request.args.get('user')
        
        if not current_username:
            return jsonify({"error": "Current user not identified"}), 400
        
        current_user_id = get_current_user_id(current_username)
        if not current_user_id:
            return jsonify({"error": "User ID not found"}), 400
        
        # Get file from Firebase
        item = db.child("vault").child(item_id).get()
        if not item.val():
            return jsonify({"error": "File not found"}), 404
        
        item_data = item.val()
        
        if not item_data.get('is_encrypted'):
            return jsonify({"error": "File is not encrypted"}), 400
        
        # Check if user has permission to decrypt
        encrypted_data = item_data.get('encrypted_data', {})
        if current_user_id not in encrypted_data.get('encrypted_keys', {}):
            return jsonify({"error": "You don't have permission to decrypt this file"}), 403
        
        # Decrypt file
        decrypted_content = decrypt_file_for_user(encrypted_data, current_user_id)
        
        # Return decrypted file
        return Response(
            decrypted_content,
            mimetype=item_data.get('file_type', 'application/octet-stream'),
            headers={
                "Content-Disposition": f"attachment; filename={item_data.get('file_name', 'decrypted_file')}"
            }
        )
        
    except Exception as e:
        print(f"Decryption error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8001)
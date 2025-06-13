from flask import Flask, request, render_template, jsonify
import base64
import cv2
import numpy as np
from pathlib import Path
from src.face_recognition_system import FaceRecognitionSystem
from collections import defaultdict
import time

app = Flask(__name__)
face_system = FaceRecognitionSystem()
image_buffer = defaultdict(list)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template("register.html")


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
        
        if success:
            image_buffer[name] = []
            return jsonify({'success': True, 'message': f'Face registered successfully for {name}'})
        else:
            return jsonify({'success': False, 'message': 'Face registration failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

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

if __name__ == '__main__':
    app.run(debug=True)
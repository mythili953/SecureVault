import cv2
import numpy as np
import pickle
from pathlib import Path

class FaceRecognitionSystem:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        self.face_data = {}
        self.face_data_file = self.data_dir / "face_data.pkl"
        self.model_file = self.data_dir / "face_model.xml"
        
        self.load_face_data()
    
    def load_face_data(self):

        if self.face_data_file.exists():
            with open(self.face_data_file, 'rb') as f:
                self.face_data = pickle.load(f)
            print(f"Loaded {len(self.face_data)} registered users")
            
        if self.model_file.exists():
            self.recognizer.read(str(self.model_file))
            print("Face recognition model loaded")

    
    def save_face_data(self):

        with open(self.face_data_file, 'wb') as f:
            pickle.dump(self.face_data, f)
        
        if len(self.face_data) > 0:
            self.train_model()
    
    def train_model(self):
        faces = []
        labels = []
        
        for user_id, user_data in self.face_data.items():
            for face in user_data['faces']:
                faces.append(face)
                labels.append(user_id)
        
        if faces:
            self.recognizer.train(faces, np.array(labels))
            self.recognizer.save(str(self.model_file))
            print("Model trained and saved")
    
    def register_face(self, name, face_images):
        try:
            print(f"Registering face for: {name} with {len(face_images)} images")

            if len(face_images) < 10:
                print("Not enough images provided for training.")
                return False

            user_id = len(self.face_data) + 1
            
            self.face_data[user_id] = {
                'name': name,
                'faces': face_images
            }

            self.save_face_data()
            self.train_model()  
            
            print(f"Registration complete for {name}. Trained with {len(face_images)} samples.")
            return True
            
        except Exception as e:
            print(f" Error during registration: {e}")
            return False

    def authenticate_face_from_image(self, image):
        try:
            if image is None:
                print("No image provided")
                return None
            
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
        
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                print("No face found in the image")
                return None
            
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            (x, y, w, h) = largest_face
            
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            if not self.model_file.exists():
                print("No trained model found. Please register faces first.")
                return None
            
            label, confidence = self.recognizer.predict(face_roi)
            
            if confidence < 100:  
                for user_id, data in self.face_data.items():
                    if user_id == label:
                        print(f"Face recognized: {data['name']} (confidence: {confidence:.2f})")
                        return {
                            'name': data['name'],
                            'confidence': confidence,
                            'user_id': user_id
                        }
            
            print(f"Face not recognized (confidence: {confidence:.2f})")
            return None
            
        except Exception as e:
            print(f"Error during authentication: {e}")
            return None

    def get_registered_users(self):
        users = []
        for user_id, data in self.face_data.items():
            users.append({
                'id': int(user_id),  
            'name': str(data['name']), 
            'face_count': len(data['faces']) if 'faces' in data else 0
            })
        return users

    
    def register_face_direct(self, name, face_images):
        try:
            print(f"Registering face for: {name} with {len(face_images)} images")

            if len(face_images) < 10:
                print("Not enough images provided for training.")
                return False
            
            user_id = len(self.face_data) + 1
    
            self.face_data[user_id] = {
                'name': str(name),  
                'faces': list(face_images)  
            }

            self.save_face_data()
            self.train_model()
            
            print(f"Registration complete for {name}. Trained with {len(face_images)} samples.")
            return True
            
        except Exception as e:
            print(f"Error during registration: {e}")
            return False

    def authenticate_face_from_image(self, image):
        try:
            if image is None:
                print("No image provided")
                return None
            
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                print("No face found in the image")
                return None
            
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            (x, y, w, h) = largest_face
            
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            if not self.model_file.exists() or len(self.face_data) == 0:
                print("No trained model found. Please register faces first.")
                return None
            
            label, confidence = self.recognizer.predict(face_roi)
            
            if confidence < 100:
                for user_id, data in self.face_data.items():
                    if user_id == label:
                        confidence_percent = round(100 - confidence, 2)
                        print(f"Face recognized: {data['name']} (confidence: {confidence_percent}%)")
                        return {
                            'name': str(data['name']),  
                            'confidence': float(confidence), 
                            'confidence_percent': float(confidence_percent),  
                            'user_id': int(user_id) 
                        }
            
            print(f"Face not recognized (confidence: {round(100-confidence, 2)}%)")
            return None
            
        except Exception as e:
            print(f"Error during authentication: {e}")
            return None
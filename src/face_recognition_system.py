import cv2
import numpy as np
import pickle
import os
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
        """Load saved face data"""
        if self.face_data_file.exists():
            with open(self.face_data_file, 'rb') as f:
                self.face_data = pickle.load(f)
            print(f"Loaded {len(self.face_data)} registered users")
            
        if self.model_file.exists():
            self.recognizer.read(str(self.model_file))
            print("Face recognition model loaded")
    
    def save_face_data(self):
        """Save face data"""
        with open(self.face_data_file, 'wb') as f:
            pickle.dump(self.face_data, f)
        
        if len(self.face_data) > 0:
            self.train_model()
    
    def train_model(self):
        """Train the face recognition model"""
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
    
    def register_face(self, name):
        """Register a new face"""
        cap = cv2.VideoCapture(0)
        print(f"Registering face for: {name}")
        print("Press SPACE to capture face samples, ESC to finish")
        
        user_id = len(self.face_data) + 1
        face_samples = []
        sample_count = 0
        max_samples = 20
        
        while sample_count < max_samples:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord(' '):  # Space to capture
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    face_samples.append(face_roi)
                    sample_count += 1
                    print(f"Captured sample {sample_count}/{max_samples}")
            
            # Show progress
            cv2.putText(frame, f"Samples: {sample_count}/{max_samples}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Register Face', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
                break
        
        if face_samples:
            self.face_data[user_id] = {
                'name': name,
                'faces': face_samples
            }
            self.save_face_data()
            print(f"Registration complete for {name}!")
        else:
            print("No face samples captured")
        
        cap.release()
        cv2.destroyAllWindows()
    
    def recognize_face(self):
        """Start face recognition"""
        cap = cv2.VideoCapture(0)
        print("Starting face recognition...")
        print("Press ESC to exit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                if len(self.face_data) > 0 and self.model_file.exists():
                    # Predict
                    label, confidence = self.recognizer.predict(face_roi)
                    
                    # Lower confidence means better match
                    if confidence < 100:
                        name = self.face_data[label]['name']
                        confidence_percent = round(100 - confidence, 2)
                        color = (0, 255, 0)  # Green for recognized
                    else:
                        name = "Unknown"
                        confidence_percent = 0
                        color = (0, 0, 255)  # Red for unknown
                else:
                    name = "No model"
                    confidence_percent = 0
                    color = (0, 0, 255)
                
                # Draw rectangle and label
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, f"{name} ({confidence_percent}%)", 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            cv2.imshow('Face Recognition - Press ESC to exit', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def list_registered_faces(self):
        """List registered faces"""
        if self.face_data:
            print("Registered faces:")
            for user_id, data in self.face_data.items():
                print(f"{user_id}. {data['name']} ({len(data['faces'])} samples)")
        else:
            print("No faces registered yet")
    
    def authenticate_user(self, username):
        """Check if a specific user can be authenticated via face recognition"""
        # This will be used later for vault access
        cap = cv2.VideoCapture(0)
        print(f"Authenticating {username}...")
        print("Look at the camera, press ESC to cancel")
        
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                if len(self.face_data) > 0 and self.model_file.exists():
                    label, confidence = self.recognizer.predict(face_roi)
                    
                    if confidence < 80:  # Good match threshold
                        recognized_name = self.face_data[label]['name']
                        if recognized_name.lower() == username.lower():
                            cap.release()
                            cv2.destroyAllWindows()
                            return True
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            cv2.putText(frame, f"Authenticating {username}...", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Authentication', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
            
            attempts += 1
        
        cap.release()
        cv2.destroyAllWindows()
        return False
from src.face_recognition_system import FaceRecognitionSystem

def main():
    face_system = FaceRecognitionSystem()
    
    while True:
        print("\n=== SecureVault - Face Recognition ===")
        print("1. Register new face")
        print("2. Start face recognition")
        print("3. Authenticate user")
        print("4. List registered faces")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            name = input("Enter name for registration: ").strip()
            if name:
                face_system.register_face(name)
            else:
                print("Name cannot be empty")
        
        elif choice == '2':
            if face_system.face_data:
                face_system.recognize_face()
            else:
                print("No faces registered yet. Register a face first.")
        
        elif choice == '3':
            if face_system.face_data:
                username = input("Enter username to authenticate: ").strip()
                if username:
                    if face_system.authenticate_user(username):
                        print(f"✓ Authentication successful for {username}")
                    else:
                        print(f"✗ Authentication failed for {username}")
                else:
                    print("Username cannot be empty")
            else:
                print("No faces registered yet.")
        
        elif choice == '4':
            face_system.list_registered_faces()
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
# SecureVault

A face recognition system for secure authentication using OpenCV.

<!-- ## Features

- Face registration with multiple samples
- Real-time face recognition
- User authentication system
- Persistent data storage -->

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv .SecureVault-venv
source .SecureVault-venv/bin/activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```
```

## Usage

1. **Register Face**: Capture face samples for a new user
2. **Face Recognition**: Start real-time face recognition
3. **Authenticate User**: Verify a specific user's identity
4. **List Users**: View all registered users

## Files Structure

```
    SecureVault/
    ├── main.py              # Main application entry
    ├── src/
    │   └── face_recognition_system.py  # Core face recognition logic
    ├── data/                # Generated data files (face_data.pkl, face_model.xml)
    ├── requirements.txt     # Dependencies
```
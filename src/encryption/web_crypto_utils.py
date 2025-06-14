from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
import os
import base64
import tempfile

def encrypt_file_for_users(file_content, sender_user_id, recipient_user_ids):
    """
    Encrypt file content for multiple recipients
    Returns encrypted content and metadata
    """
    # Generate AES key for file encryption
    aes_key = os.urandom(32)
    iv = os.urandom(16)
    
    # Encrypt the file content with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # Pad the file content
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(file_content) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # Encrypt AES key for each recipient
    encrypted_keys = {}
    
    for recipient_id in recipient_user_ids:
        try:
            # Load recipient's public key from Firebase (we'll need to modify this)
            recipient_public_key = load_user_public_key(recipient_id)
            
            if recipient_public_key:
                encrypted_aes_key = recipient_public_key.encrypt(
                    aes_key,
                    asym_padding.OAEP(
                        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encrypted_keys[recipient_id] = base64.b64encode(encrypted_aes_key).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting for user {recipient_id}: {e}")
            continue
    
    # Prepare encrypted file data
    encrypted_file_data = {
        'iv': base64.b64encode(iv).decode('utf-8'),
        'encrypted_content': base64.b64encode(ciphertext).decode('utf-8'),
        'encrypted_keys': encrypted_keys,
        'sender_id': sender_user_id
    }
    
    return encrypted_file_data

def decrypt_file_for_user(encrypted_file_data, user_id):
    """
    Decrypt file for a specific user using their private key
    """
    try:
        # Load user's private key
        private_key = load_user_private_key(user_id)
        if not private_key:
            raise Exception("Private key not found for user")
        
        # Get encrypted AES key for this user
        if user_id not in encrypted_file_data['encrypted_keys']:
            raise Exception("You don't have permission to decrypt this file")
        
        encrypted_aes_key = base64.b64decode(encrypted_file_data['encrypted_keys'][user_id])
        
        # Decrypt AES key
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt file content
        iv = base64.b64decode(encrypted_file_data['iv'])
        ciphertext = base64.b64decode(encrypted_file_data['encrypted_content'])
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext
        
    except Exception as e:
        print(f"Decryption error: {e}")
        raise e

def load_user_public_key(user_id):
    """Load user's public key from stored data"""
    try:
        # This will be loaded from Firebase users collection
        from app import db
        
        users = db.child("users").get()
        if users.val():
            for key, user_data in users.val().items():
                if user_data.get('userid') == user_id:
                    public_key_pem = user_data.get('public_key')
                    if public_key_pem:
                        return serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        return None
    except Exception as e:
        print(f"Error loading public key for {user_id}: {e}")
        return None

def load_user_private_key(user_id):
    """Load user's private key from data/keys directory"""
    try:
        private_key_path = f"data/keys/{user_id}_private_key.pem"
        if os.path.exists(private_key_path):
            with open(private_key_path, "rb") as f:
                return serialization.load_pem_private_key(f.read(), password=None)
        return None
    except Exception as e:
        print(f"Error loading private key for {user_id}: {e}")
        return None

def get_current_user_id(username):
    """Get user ID from username by looking up in Firebase"""
    try:
        from app import db
        
        users = db.child("users").get()
        if users.val():
            for key, user_data in users.val().items():
                if user_data.get('username') == username:
                    return user_data.get('userid')
        return None
    except Exception as e:
        print(f"Error getting user ID for {username}: {e}")
        return None
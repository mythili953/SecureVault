from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os

def generate_keys(user_id):
    """Generate RSA key pair for a user"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Create data/keys directory if it doesn't exist
    keys_dir = "data/keys"
    os.makedirs(keys_dir, exist_ok=True)
    
    # Save private key in data/keys folder
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(f"{keys_dir}/{user_id}_private_key.pem", "wb") as f:
        f.write(pem_private)
    
    # Get public key as string
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Return public key as string
    return pem_public.decode('utf-8')

def exchange_public_keys(users):
    """Simulate secure key exchange between users"""
    for user in users:
        for other_user in users:
            if user != other_user:
                # In real implementation, this would be a secure exchange
                with open(f"users/{other_user}/public_key.pem", "rb") as src, \
                     open(f"users/{user}/contacts/{other_user}_public.pem", "wb") as dst:
                    dst.write(src.read())

def delete_user_keys(user_id):
    """Delete all keys for a specific user"""
    try:
        # Define key file paths
        private_key_path = f"data/keys/{user_id}_private_key.pem"
        public_key_path = f"data/keys/{user_id}_public_key.pem"
        
        deleted_files = []
        
        # Delete private key
        if os.path.exists(private_key_path):
            os.remove(private_key_path)
            deleted_files.append(private_key_path)
            print(f"Deleted private key: {private_key_path}")
        
        # Delete public key
        if os.path.exists(public_key_path):
            os.remove(public_key_path)
            deleted_files.append(public_key_path)
            print(f"Deleted public key: {public_key_path}")
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'message': f"Deleted {len(deleted_files)} key files for user {user_id}"
        }
        
    except Exception as e:
        print(f"Error deleting keys for user {user_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to delete keys for user {user_id}"
        }

def list_user_keys():
    """List all users who have keys stored"""
    try:
        if not os.path.exists("data/keys"):
            return []
        
        key_files = os.listdir("data/keys")
        users_with_keys = set()
        
        for file in key_files:
            if file.endswith("_private_key.pem") or file.endswith("_public_key.pem"):
                user_id = file.replace("_private_key.pem", "").replace("_public_key.pem", "")
                users_with_keys.add(user_id)
        
        users_list = []
        for user_id in users_with_keys:
            private_exists = os.path.exists(f"data/keys/{user_id}_private_key.pem")
            public_exists = os.path.exists(f"data/keys/{user_id}_public_key.pem")
            
            users_list.append({
                'user_id': user_id,
                'has_private_key': private_exists,
                'has_public_key': public_exists,
                'complete_keypair': private_exists and public_exists
            })
        
        return users_list
        
    except Exception as e:
        print(f"Error listing user keys: {e}")
        return []

def generate_key_pair():
    """Generate RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return {'private_key': private_key, 'public_key': public_key}

def serialize_public_key(public_key):
    """Serialize public key to PEM format"""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

def store_private_key(user_id, private_key):
    """Store private key locally"""
    keys_dir = "data/keys"
    os.makedirs(keys_dir, exist_ok=True)
    
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open(f"{keys_dir}/{user_id}_private_key.pem", "wb") as f:
        f.write(pem_private)
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
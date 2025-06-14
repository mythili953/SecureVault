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
    
    # Save private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(f"users/{user_id}/private_key.pem", "wb") as f:
        f.write(pem_private)
    
    # Save public key
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(f"users/{user_id}/public_key.pem", "wb") as f:
        f.write(pem_public)
    
    return private_key

def exchange_public_keys(users):
    """Simulate secure key exchange between users"""
    for user in users:
        for other_user in users:
            if user != other_user:
                # In real implementation, this would be a secure exchange
                with open(f"users/{other_user}/public_key.pem", "rb") as src, \
                     open(f"users/{user}/contacts/{other_user}_public.pem", "wb") as dst:
                    dst.write(src.read())
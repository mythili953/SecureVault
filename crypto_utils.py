from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
import os

def ensure_shared_dir():
    os.makedirs("shared", exist_ok=True)

def encrypt_file(sender_id, receiver_id, file_path):
    ensure_shared_dir()
    aes_key = os.urandom(32)
    iv = os.urandom(16)
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    with open(file_path, "rb") as f:
        plaintext = f.read()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    with open(f"users/{sender_id}/contacts/{receiver_id}_public.pem", "rb") as f:
        receiver_public_key = serialization.load_pem_public_key(f.read())
    
    encrypted_aes_key = receiver_public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    encrypted_file_path = f"shared/{sender_id}_to_{receiver_id}_{os.path.basename(file_path)}.enc"
    with open(encrypted_file_path, "wb") as f:
        f.write(iv)
        f.write(encrypted_aes_key)
        f.write(ciphertext)
    
    return encrypted_file_path

def decrypt_file(receiver_id, encrypted_file_path, output_path):
    with open(encrypted_file_path, "rb") as f:
        iv = f.read(16)
        encrypted_aes_key = f.read(256)
        ciphertext = f.read()
    
    with open(f"users/{receiver_id}/private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    
    with open(output_path, "wb") as f:
        f.write(plaintext)
    
    return output_path
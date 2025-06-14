from key_manager import generate_keys, exchange_public_keys
from crypto_utils import encrypt_file, decrypt_file
import os
import shutil

def setup_demo():
    """Initialize demo environment"""
    users = ["user1", "user2", "user3"]


    os.makedirs("shared", exist_ok=True)  # Add this line
    
    # Create directories
    for user in users:
        os.makedirs(f"users/{user}/contacts", exist_ok=True)
        generate_keys(user)
    
    # Exchange public keys
    exchange_public_keys(users)
    
    # Create a test file
    with open("test_file.txt", "w") as f:
        f.write("This is a secret message for the demo!")
    
    print("Demo setup complete. Test file created.")

def run_demo():
    """Run the demo file transfer"""
    print("\nRunning demo: User1 sends file to User3")
    
    # User1 encrypts file for User3
    encrypted_path = encrypt_file("user1", "user3", "test_file.txt")
    print(f"File encrypted and saved to: {encrypted_path}")
    
    # User3 decrypts the file
    decrypted_path = decrypt_file("user3", encrypted_path, "decrypted_file.txt")
    print(f"File decrypted and saved to: {decrypted_path}")
    
    # Verify contents
    with open("test_file.txt", "r") as original, open(decrypted_path, "r") as decrypted:
        original_content = original.read()
        decrypted_content = decrypted.read()
        print("\nOriginal content:", original_content)
        print("Decrypted content:", decrypted_content)
        assert original_content == decrypted_content, "Decryption failed!"
        print("Verification successful - contents match!")

if __name__ == "__main__":
    setup_demo()
    run_demo()
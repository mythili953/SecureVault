import os
from tkinter import Tk, filedialog, messagebox
from cryptography.fernet import Fernet

# Load the encryption key from file
def load_key():
    with open("vault.key", "rb") as key_file:
        return key_file.read()

key = load_key()
cipher = Fernet(key)

# Encrypt file
def encrypt_file(file_path):
    try:
        with open(file_path, "rb") as file:
            data = file.read()

        encrypted_data = cipher.encrypt(data)

        # Save as .enc file
        encrypted_path = file_path + ".enc"
        with open(encrypted_path, "wb") as file:
            file.write(encrypted_data)

        messagebox.showinfo("Success", f"File Encrypted: {encrypted_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Encryption failed: {e}")

# Decrypt file
def decrypt_file(file_path):
    try:
        with open(file_path, "rb") as file:
            encrypted_data = file.read()

        decrypted_data = cipher.decrypt(encrypted_data)

        # Remove '.enc' extension to get original name
        if file_path.endswith(".enc"):
            decrypted_path = file_path[:-4]
        else:
            decrypted_path = file_path + ".dec"

        with open(decrypted_path, "wb") as file:
            file.write(decrypted_data)

        messagebox.showinfo("Success", f"File Decrypted: {decrypted_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Decryption failed: {e}")

# File selection dialog and operation
def select_file(operation):
    file_path = filedialog.askopenfilename()

    if not file_path:
        return

    if operation == "encrypt":
        encrypt_file(file_path)
    elif operation == "decrypt":
        decrypt_file(file_path)

# Simple UI to trigger operations
def main_ui():
    root = Tk()
    root.withdraw()  # Hide main window

    while True:
        action = messagebox.askquestion("Select Operation", "Do you want to Encrypt a file? (No means Decrypt)")

        if action == 'yes':
            select_file("encrypt")
        else:
            select_file("decrypt")

        again = messagebox.askquestion("Continue?", "Do you want to process another file?")
        if again != 'yes':
            break

if __name__ == "__main__":
    main_ui()

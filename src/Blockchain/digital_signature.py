import hashlib
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def private_key_exists():
    return os.path.exists("private_key.pem")

def public_key_exists():
    return os.path.exists("public_key.pem")

def create_digital_signature(private_key, message: str) -> str:
    message_bytes = message.encode('utf-8')
    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    # Encode as Base64 string for JSON compatibility
    return base64.b64encode(signature).decode('utf-8')

def verify_digital_signature(public_key, signature_b64: str, message: str) -> bool:
    message_bytes = message.encode('utf-8')
    signature = base64.b64decode(signature_b64)
    try:
        public_key.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False

def create_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open("private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open("public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def load_private_key():
    if not os.path.exists("private_key.pem"):
        raise FileNotFoundError("Private key file not found.")
    with open("private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key():
    if not os.path.exists("public_key.pem"):
        raise FileNotFoundError("Public key file not found.")
    with open("public_key.pem", "rb") as f:
        return serialization.load_pem_public_key(f.read())

def get_address(public_key) -> str:
    # Converts the public key object into a string so it can be sent via JSON
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8').strip()

def load_public_key_from_address(address_str: str):
    # Converts a string address back into a public key object for verification
    return serialization.load_pem_public_key(address_str.encode('utf-8'))
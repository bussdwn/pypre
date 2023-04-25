import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_BYTES = bytes.fromhex("149b684b85ccb9502180180ba672335e")
ITERATIONS = 480000


def decrypt_config(key_str: str, config_data: bytes) -> bytes:
    """Decrypt config data.

    Args:
        key_str: The string representation of the key.
        config_data: The config data to be decrypted.

    Returns:
        The decrypted config data.
    """
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT_BYTES, iterations=ITERATIONS)
    key = base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
    fernet = Fernet(key)
    return fernet.decrypt(config_data)

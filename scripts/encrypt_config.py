from __future__ import annotations

import base64
from argparse import ArgumentParser, Namespace
from getpass import getpass
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_BYTES = bytes.fromhex("149b684b85ccb9502180180ba672335e")
ITERATIONS = 480000


class TypedNamespace(Namespace):
    config_path: Path
    outpath: Path | None


def handle_args() -> TypedNamespace:
    parser = ArgumentParser(description="Encrypt a config file from a user-provided passphrase.")
    parser.add_argument("config_path", type=Path, help="Path of the config file to be encrypted.")
    parser.add_argument(
        "--outpath",
        type=Path,
        help="Path of the output encrypted config file. If not provided, will override the original file.",
    )

    return parser.parse_args(namespace=TypedNamespace())


def encrypt_config_file(key_str: str, config_path: Path, outpath: Path | None) -> Path:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT_BYTES, iterations=ITERATIONS)
    key = base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
    fernet = Fernet(key)

    with open(config_path, "r+b") as cfg_file:
        encrypted_data = fernet.encrypt(cfg_file.read())
        if outpath is None:
            cfg_file.truncate(0)
            cfg_file.write(encrypted_data)
        else:
            with open(outpath, "wb") as outfile:
                outfile.write(encrypted_data)

    return outpath or config_path


def get_password() -> str:
    password = getpass("Enter AES passphrase: ")
    password_confirm = getpass("Confirm AES passphrase: ")
    if password != password_confirm:
        print("Passphrase does not match")
        return get_password()
    return password


if __name__ == "__main__":
    args = handle_args()
    if not args.config_path.exists() or not args.config_path.is_file():
        raise ValueError(f"{args.config_path} does not exist or is not a file.")

    print(f"Reading config from {args.config_path}...")
    outpath = encrypt_config_file(get_password(), args.config_path, args.outpath)
    print(f"Encrypted config written to {outpath}")
    raise SystemExit(0)

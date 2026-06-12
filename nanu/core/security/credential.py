"""Cifrado de credenciales usando AES-256-GCM."""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from typing import Optional

class CredentialManager:
    """Gestiona el cifrado/descifrado de credenciales con una passphrase."""
    
    def __init__(self, passphrase: str, salt: Optional[bytes] = None):
        self.passphrase = passphrase
        if salt is None:
            salt = os.urandom(16)
        self.salt = salt
        self._derive_key()
    
    def _derive_key(self) -> None:
        """Deriva una clave AES-256 usando HKDF-SHA256."""
        # Primero, obtener bytes de la passphrase
        pass_bytes = self.passphrase.encode('utf-8')
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            info=b"nanu-credential",
        )
        self.key = hkdf.derive(pass_bytes)
    
    def encrypt(self, plaintext: str) -> str:
        """Cifra un texto y retorna en formato base64 con prefijo 'enc://'."""
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        combined = nonce + ciphertext
        b64 = base64.urlsafe_b64encode(combined).decode('ascii')
        return f"enc://{b64}"
    
    def decrypt(self, encrypted: str) -> str:
        """Descifra un string con prefijo 'enc://'."""
        if not encrypted.startswith("enc://"):
            # Si no está cifrado, asumir texto plano
            return encrypted
        b64 = encrypted[6:]  # quitar 'enc://'
        combined = base64.urlsafe_b64decode(b64)
        nonce = combined[:12]
        ciphertext = combined[12:]
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    
    @classmethod
    def from_env(cls, env_var: str = "NANU_CREDENTIAL_PASSPHRASE") -> Optional['CredentialManager']:
        """Crea un manager desde una variable de entorno."""
        passphrase = os.environ.get(env_var)
        if not passphrase:
            return None
        salt = os.environ.get("NANU_CREDENTIAL_SALT")
        if salt:
            salt = base64.urlsafe_b64decode(salt)
        return cls(passphrase, salt)
    
    def save_salt(self) -> str:
        """Guarda la salt como string base64 para almacenar en entorno."""
        return base64.urlsafe_b64encode(self.salt).decode('ascii')

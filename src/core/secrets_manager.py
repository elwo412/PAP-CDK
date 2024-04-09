import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Dict, Optional
import os

class SecretManager:
    def __init__(self) -> None:
        # load password from dotenv
        password = os.getenv("SECRET_MANAGER_PASSWORD")
        self.secret_file = "secrets.json"
        self.key_file = "secret.key"
        self.cipher = self.init_cipher()
        self.password = password  # Consider using this to further secure the key storage
        self.secrets = {}
        self.load_secrets()

    def init_cipher(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as keyfile:
                key = keyfile.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as keyfile:
                keyfile.write(key)
        return Fernet(key)

    def encrypt(self, message: str) -> str:
        return self.cipher.encrypt(message.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()

    def generate_secret(self, key: str, secret: str) -> None:
        now = datetime.now().isoformat()
        self.secrets[key] = {
            'secret': self.encrypt(secret),
            'created': now,
            'updated': now
        }
        self.save_secrets()

    def get_secret(self, key: str) -> Optional[str]:
        data = self.secrets.get(key)
        if data:
            return self.decrypt(data['secret'])
        else:
            raise KeyError(f"Secret '{key}' not found!")

    def update_secret(self, key: str, secret: str) -> None:
        now = datetime.now().isoformat()
        if key in self.secrets:
            self.secrets[key]['secret'] = self.encrypt(secret)
            self.secrets[key]['updated'] = now
            self.save_secrets()
        else:
            raise KeyError(f"Secret '{key}' not found!")

    def save_secrets(self) -> None:
        with open(self.secret_file, 'w') as f:
            json.dump(self.secrets, f)

    def load_secrets(self) -> None:
        try:
            with open(self.secret_file, 'r') as f:
                self.secrets = json.load(f)
        except FileNotFoundError:
            self.secrets = {}

    def warn_if_outdated(self, key: str, days: int = 90) -> None:
        data = self.secrets.get(key)
        if data:
            last_updated = datetime.fromisoformat(data['updated'])
            if datetime.now() - last_updated > timedelta(days=days):
                print(f"Warning: The secret '{key}' has not been updated for more than {days} days!")
                
                
if __name__ == "__main__":
    sm = SecretManager()
    #print(sm.get_secret("REFERER_SECRET"))
    #sm.generate_secret("REFERER_SECRET", "my_secret")
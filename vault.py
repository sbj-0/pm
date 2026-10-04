import hashlib, os, base64, getpass, json
from cryptography.fernet import Fernet, InvalidToken

#---PATHS---#
BASE_DIR = os.path.expanduser("~/.config/pm")
VAULT_PATH = os.path.join(BASE_DIR, 'valut.enc')
SALT_PATH = os.path.join(BASE_DIR, 'vault.salt')
RECOVERY_PATH = os.path.join(BASE_DIR, 'recovery.enc')

#---RECOVERY KEY---#
def generate_recovery_key() -> str:
    import secrets
    return secrets.token_urlsafe(32)

#---KEY DERIVATION---#
def derive_key(pin: str, salt: bytes) -> Fernet:
    key = hashlib.scrypt(
        pin.encode(), 
        salt=salt, 
        n=2**14, 
        r=8, 
        p=1, 
        dklen=32
    )
    return Fernet(base64.urlsafe_b64encode(key))

#---INITIALIZATION---#
def init_vault(pin: str):
    if os.path.exists(VAULT_PATH):
        print("Vault already exists. Use your PIN to access it.")
        return

    os.makedirs(BASE_DIR, exist_ok=True)

    salt = os.urandom(16)
    with open(SALT_PATH, 'wb') as f:
        f.write(salt)

    fernet = derive_key(pin, salt)
    # Extract the raw key from the Fernet object
    vault_key = fernet._signing_key + fernet._encryption_key

    # Generate recovery key and use it to encrypt the vault key
    recovery_key = generate_recovery_key()
    recovery_salt = os.urandom(16)
    recovery_fernet = derive_key(recovery_key, recovery_salt)
    recovery_token = recovery_fernet.encrypt(vault_key)

    # Save recovery.enc as: salt (16 bytes) + token
    with open(RECOVERY_PATH, 'wb') as f:
        f.write(recovery_salt + recovery_token)


    token = fernet.encrypt(json.dumps({}).encode())
    with open(VAULT_PATH, 'wb') as f:
        f.write(token)

    print("Vault created.")
    print("\nRecovery key (save this somewhere safe - shown once only): ")
    print(f"\n {recovery_key}\n")


#---LOAD---#
def load_vault(pin: str) -> dict:
    if not os.path.exists(VAULT_PATH):
        print("No Vault found. Run: pm init")
        exit(1)

    with open(SALT_PATH, 'rb') as f:
        salt = f.read()

    fernet = derive_key(pin, salt)

    with open(VAULT_PATH, 'rb') as f:
        token = f.read()

    try:
        data = fernet.decrypt(token)
        return json.loads(data.decode())
    except InvalidToken:
        print("Wrong PIN.")
        exit(1)

#---SAVE---#
def save_vault(pin: str, data: dict) -> None:
    if not os.path.exists(SALT_PATH):
        print("Salt file missing. Vault may be curropted.")
        exit(1)

    with open(SALT_PATH, 'rb') as f:
        salt = f.read()

    fernet = derive_key(pin, salt)
    token = fernet.encrypt(json.dumps(data).encode())

    with open(VAULT_PATH, 'wb') as f:
        f.write(token)

    print("Vault saved.")


#---PIN RESET---#
def reset_pin(recovery_key: str, new_pin: str):
    if not os.path.exists(RECOVERY_PATH):
        print("No recovery file found.")
        exit(1)

    #Read recovery.enc - first 16 bytes are the salt, rest is the token.
    with open(RECOVERY_PATH, 'rb') as f:
        data = f.read()

    recovery_salt = data[:16]
    recovery_token = data[16:]

    #Derive the recovery lock and decrypt to get the raw vault key
    recovery_fernet = derive_key(recovery_key, recovery_salt)
    try:
        vault_key = recovery_fernet.decrypt(recovery_token)
    except InvalidToken:
        print("Wrong recovery key.")
        exit(1)

    #Reconstruct fernet from raw key bytes
    old_fernet = Fernet(base64.urlsafe_b64encode(vault_key))

    #Decrypt the vault with the old key
    with open(VAULT_PATH, 'rb') as f:
        token = f.read()
    vault_data = json.loads(old_fernet.decrypt(token).decode())

    #Re-encrypt vault with the new pin
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
        new_fernet = derive_key(new_pin, salt)
        new_token = new_fernet.encrypt(json.dumps(vault_data).encode())

    with open(VAULT_PATH, 'wb') as f:
        f.write(new_token)

    #Update recovery.enc with the new vault key
    new_vault_key = new_fernet._signing_key + new_fernet._encryption_key
    new_recovery_fernet = derive_key(recovery_key, recovery_salt)
    new_recovery_token = new_recovery_fernet.encrypt(new_vault_key)

    with open(RECOVERY_PATH, 'wb') as f:
        f.write(recovery_salt + new_recovery_token)

    print("PIN reset successfully.")


def vault_exists() -> bool:
    return os.path.exists(VAULT_PATH)

def get_pin(prompt="Enter PIN: ") -> str:
    return getpass.getpass(prompt)

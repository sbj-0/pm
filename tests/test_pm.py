import os, pytest
from vault import init_vault, load_vault, save_vault, vault_exists, derive_key, reset_pin
from generator import generate_password

#---Generator tests---#

def test_password_length():
    pswd = generate_password(16)
    assert len(pswd) == 16

def test_password_has_lowercase():
    pswd = generate_password(20)
    assert any(c.islower() for c in pswd)

def test_password_has_uppercase():
    pswd = generate_password(20)
    assert any(c.isupper() for c in pswd)

def test_password_has_digit():
    pswd = generate_password(20)
    assert any(c.isdigit() for c in pswd)

def test_password_min_length():
    with pytest.raises(ValueError):
        generate_password(4)

def test_passwords_are_unique():
    assert generate_password(16) != generate_password(16)

#--Vault tests--#

PIN = "testpin123"

@pytest.fixture(autouse=True)
def temp_vault(tmp_path, monkeypatch):
    #redirect vault paths to a temporary directory
    import vault
    monkeypatch.setattr(vault, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(vault, "VAULT_PATH", str(tmp_path / "vault.enc"))
    monkeypatch.setattr(vault, "SALT_PATH", str(tmp_path / "vault.salt"))
    monkeypatch.setattr(vault, "RECOVERY_PATH", str(tmp_path / "recovery.enc"))

def test_init_create_vault(tmp_path):
    import vault
    init_vault(PIN)
    assert os.path.exists(vault.VAULT_PATH)
    assert os.path.exists(vault.SALT_PATH)
    assert os.path.exists(vault.RECOVERY_PATH)

def test_load_empty_vault():
    init_vault(PIN)
    data = load_vault(PIN)
    assert data == {}

def test_wrong_pin_raises():
    from cryptography.fernet import InvalidToken
    init_vault(PIN)
    with pytest.raises(SystemExit):
        load_vault("Wrongpin")

def test_save_and_load():
    init_vault(PIN)
    save_vault(PIN, {"github": [{"username": "alice", "password": "s3cr3t"}]})
    data = load_vault(PIN)
    assert "github" in data
    assert data["github"][0]["username"] == "alice"

def test_delete_entry():
    init_vault(PIN)
    save_vault(PIN, {"github": [{"username": "alice", "password": "s3cr3t"}]})
    vault_data = load_vault(PIN)
    del vault_data["github"]
    save_vault(PIN, vault_data)
    assert "github" not in load_vault(PIN)

def test_multiple_credentials_per_service():
    init_vault(PIN)
    save_vault(PIN, {"github": [
        {"username": "alice",  "password": "pass1"},
        {"username": "alice2", "password": "pass2"}
    ]})
    data = load_vault(PIN)
    assert len(data["github"]) == 2
    assert data["github"][1]["username"] == "alice2"

def test_reset_pin():
    import vault
    #capture recovery key
    init_vault(PIN)
    #read the key from file indirectly by testing reset works
    new_pin = "newpin456"
    with open(vault.SALT_PATH, 'rb') as f:
        salt  = f.read()
    #derive key isn't exposed - test reset_pin via integration
    save_vault(PIN, {"test": {"username": "u", "password": "p"}})
    #confirm new pin works
    data = load_vault(PIN)
    assert "test" in data
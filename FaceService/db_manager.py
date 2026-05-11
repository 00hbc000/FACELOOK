import os, sqlite3, numpy as np, uuid
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

DB_DIR = r"C:\FACELOOK\Database"
DB_PATH = os.path.join(DB_DIR, "biometric.db")
KEY_FILE = r"C:\FACELOOK\Config\secret.key"
DB_PASSPHRASE = "FACELOOK_Secret_DB_Key_2025!"

def _get_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key = get_random_bytes(32)
        with open(KEY_FILE, "wb") as f: f.write(key)
    with open(KEY_FILE, "rb") as f: return f.read()

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"PRAGMA key = '{DB_PASSPHRASE}';")
    conn.execute("SELECT count(*) FROM sqlite_master;")
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_guid TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            embedding BLOB NOT NULL,
            encrypted_password BLOB NOT NULL,
            salt BLOB NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit(); conn.close()

def encrypt_password(plain_text):
    key = _get_key()
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    salt = get_random_bytes(16)
    return nonce + tag + ciphertext, salt

def decrypt_password(encrypted_blob, salt):
    key = _get_key()
    nonce = encrypted_blob[:12]
    tag = encrypted_blob[12:28]
    ciphertext = encrypted_blob[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

def add_user(username, password, embedding):
    conn = get_db_connection()
    guid = str(uuid.uuid4())
    emb_blob = embedding.astype(np.float64).tobytes()
    enc_pw, salt = encrypt_password(password)
    conn.execute("INSERT INTO users (user_guid, username, embedding, encrypted_password, salt) VALUES (?,?,?,?,?)",
                 (guid, username, emb_blob, enc_pw, salt))
    conn.commit(); conn.close()
    return guid

def delete_user(guid):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE user_guid = ?", (guid,))
    conn.commit()
    conn.close()
    return True

def get_all_users():
    conn = get_db_connection()
    cur = conn.execute("SELECT user_guid, username, embedding, encrypted_password, salt FROM users")
    users = []
    for row in cur.fetchall():
        users.append({
            "guid": row[0], "username": row[1],
            "embedding": np.frombuffer(row[2], dtype=np.float64),
            "enc_pw": row[3], "salt": row[4]
        })
    conn.close()
    return users
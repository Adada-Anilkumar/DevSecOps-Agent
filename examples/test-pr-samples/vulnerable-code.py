"""
Sample vulnerable code for testing the DevSecOps agent.
Create a PR with this file to see the agent in action!
"""

# 1. SQL Injection Vulnerability
def get_user_by_name(username):
    """Vulnerable to SQL injection"""
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return database.execute(query)


# 2. Hardcoded Secret
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
SECRET_TOKEN = "ghp_AbCdEfGhIjKlMnOpQrStUvWxYz123456"


def authenticate():
    """Using hardcoded credentials"""
    return requests.post(
        "https://api.example.com/auth",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )


# 3. Command Injection
import subprocess

def run_command(user_input):
    """Vulnerable to command injection"""
    subprocess.call(f"echo {user_input}", shell=True)


# 4. Path Traversal
def read_file(filename):
    """Vulnerable to path traversal"""
    with open(f"/var/data/{filename}", "r") as f:
        return f.read()


# 5. Weak Cryptography
import hashlib

def hash_password(password):
    """Using weak MD5 hashing"""
    return hashlib.md5(password.encode()).hexdigest()


# 6. Missing Error Handling
def process_payment(amount):
    """No error handling for critical operation"""
    result = payment_gateway.charge(amount)
    return result


# 7. Logging Sensitive Data
import logging

def login(username, password):
    """Logging sensitive information"""
    logging.info(f"Login attempt: username={username}, password={password}")
    return authenticate(username, password)


# 8. Insecure Deserialization
import pickle

def load_user_data(data):
    """Unsafe deserialization"""
    return pickle.loads(data)


# 9. Missing Authentication Check
def delete_user(user_id):
    """No authentication or authorization check"""
    database.delete("users", user_id)
    return {"status": "deleted"}


# 10. Exposed Debug Endpoint
from flask import Flask, request

app = Flask(__name__)

@app.route("/debug")
def debug():
    """Debug endpoint exposed in production"""
    return {
        "env": os.environ,
        "request": request.headers,
        "config": app.config
    }

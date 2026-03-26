"""
Sample secure code showing fixes for common vulnerabilities.
Use this to compare with vulnerable-code.py
"""

import os
import hashlib
import logging
from functools import wraps
from flask import Flask, request, abort

# 1. SQL Injection - FIXED with parameterized query
def get_user_by_name(username):
    """Safe parameterized query"""
    query = "SELECT * FROM users WHERE username = %s"
    return database.execute(query, (username,))


# 2. Secrets Management - FIXED with environment variables
API_KEY = os.environ.get("API_KEY")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")


def authenticate():
    """Using environment variables for secrets"""
    if not API_KEY:
        raise ValueError("API_KEY not configured")
    return requests.post(
        "https://api.example.com/auth",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )


# 3. Command Injection - FIXED with safe subprocess usage
import subprocess

def run_command(user_input):
    """Safe command execution with argument list"""
    # Validate input
    if not user_input.isalnum():
        raise ValueError("Invalid input")
    # Use argument list instead of shell=True
    subprocess.run(["echo", user_input], check=True, shell=False)


# 4. Path Traversal - FIXED with path validation
from pathlib import Path

def read_file(filename):
    """Safe file reading with path validation"""
    base_dir = Path("/var/data").resolve()
    file_path = (base_dir / filename).resolve()
    
    # Ensure file is within base directory
    if not file_path.is_relative_to(base_dir):
        raise ValueError("Invalid file path")
    
    with open(file_path, "r") as f:
        return f.read()


# 5. Strong Cryptography - FIXED with bcrypt
import bcrypt

def hash_password(password):
    """Using strong bcrypt hashing"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)


def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hashed)


# 6. Error Handling - FIXED with proper exception handling
def process_payment(amount):
    """Proper error handling for critical operation"""
    try:
        if amount <= 0:
            raise ValueError("Invalid amount")
        
        result = payment_gateway.charge(amount)
        
        if not result.success:
            logging.error(f"Payment failed: {result.error_code}")
            raise PaymentError("Payment processing failed")
        
        return result
    except PaymentGatewayTimeout as e:
        logging.error(f"Payment timeout: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected payment error: {e}")
        raise


# 7. Secure Logging - FIXED without sensitive data
def login(username, password):
    """Logging without sensitive information"""
    logging.info(f"Login attempt: username={username}")
    
    try:
        result = authenticate(username, password)
        logging.info(f"Login successful: username={username}")
        return result
    except AuthenticationError:
        logging.warning(f"Login failed: username={username}")
        raise


# 8. Safe Deserialization - FIXED with JSON
import json

def load_user_data(data):
    """Safe JSON deserialization"""
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON data: {e}")
        raise ValueError("Invalid data format")


# 9. Authentication & Authorization - FIXED
def require_auth(f):
    """Decorator for authentication check"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not verify_token(token):
            abort(401, "Unauthorized")
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """Decorator for admin authorization check"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            abort(403, "Forbidden")
        return f(*args, **kwargs)
    return decorated_function


@require_auth
@require_admin
def delete_user(user_id):
    """Proper authentication and authorization"""
    current_user = get_current_user()
    
    # Additional check: can't delete yourself
    if current_user.id == user_id:
        raise ValueError("Cannot delete your own account")
    
    database.delete("users", user_id)
    logging.info(f"User deleted: {user_id} by admin {current_user.id}")
    return {"status": "deleted"}


# 10. Debug Endpoint - FIXED with environment check
app = Flask(__name__)

@app.route("/debug")
def debug():
    """Debug endpoint only available in development"""
    if not app.config.get("DEBUG") or os.environ.get("ENV") == "production":
        abort(404)
    
    # Return limited, safe debug info
    return {
        "version": app.config.get("VERSION"),
        "environment": os.environ.get("ENV", "development"),
        "timestamp": datetime.now().isoformat()
    }


# Additional security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

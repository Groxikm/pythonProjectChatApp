"""
JWT Authentication Enhancement for Chat App
============================================

This module provides JWT token-based authentication that can be integrated
into the existing authentication system for enhanced security.

Installation required:
pip install PyJWT

Usage:
1. Add JWT_SECRET_KEY to settings.py
2. Replace/enhance the login endpoint to return JWT tokens
3. Add token verification middleware
4. Update client to send tokens in Authorization header
"""

import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any

# Configuration
JWT_SECRET_KEY = "your-secret-key-change-this-in-production"  # Should be in settings.py
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class JWTAuth:
    @staticmethod
    def generate_token(user_id: str, username: str) -> str:
        """Generate a JWT token for a user"""
        payload = {
            'user_id': user_id,
            'username': username,
            'iat': datetime.datetime.now(datetime.timezone.utc),
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
    
    @staticmethod
    def extract_token_from_header(auth_header: str) -> Optional[str]:
        """Extract token from Authorization header"""
        if not auth_header:
            return None
        
        # Expected format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]

def require_jwt_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = JWTAuth.extract_token_from_header(auth_header)
        if not token:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        payload = JWTAuth.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username']
        }
        
        return f(*args, **kwargs)
    return wrapper

# Enhanced login endpoint (to replace existing one)
def enhanced_login():
    """Enhanced login endpoint that returns JWT tokens"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Use existing user service for authentication
        user = user_service.authenticate_user(username, password)
        if user:
            # Generate JWT token
            token = JWTAuth.generate_token(user['id'], user['username'])
            
            return jsonify({
                "message": "Login successful",
                "user": user,
                "token": token,
                "expires_in": JWT_EXPIRATION_HOURS * 3600  # seconds
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

# Token refresh endpoint
def refresh_token():
    """Refresh an existing JWT token"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({'error': 'Authorization header required'}), 401
    
    token = JWTAuth.extract_token_from_header(auth_header)
    if not token:
        return jsonify({'error': 'Invalid authorization header format'}), 401
    
    payload = JWTAuth.verify_token(token)
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    # Generate new token
    new_token = JWTAuth.generate_token(payload['user_id'], payload['username'])
    
    return jsonify({
        "token": new_token,
        "expires_in": JWT_EXPIRATION_HOURS * 3600
    }), 200

# Example of protected endpoint
@require_jwt_auth
def protected_endpoint():
    """Example of how to use JWT authentication on endpoints"""
    user_id = request.current_user['user_id']
    username = request.current_user['username']
    
    return jsonify({
        "message": f"Hello {username}!",
        "user_id": user_id,
        "protected_data": "This data requires authentication"
    }), 200

"""
Integration Instructions:
========================

1. Add to settings.py:
   JWT_SECRET_KEY = "your-very-secure-secret-key-here"

2. Install PyJWT:
   pip install PyJWT

3. Replace login endpoint in server.py:
   @app.route('/api/users/login', methods=['POST'])
   def login():
       return enhanced_login()

4. Add token refresh endpoint:
   @app.route('/api/auth/refresh', methods=['POST'])
   def refresh():
       return refresh_token()

5. Protect endpoints that need authentication:
   @app.route('/api/protected-endpoint')
   @require_jwt_auth
   def my_protected_endpoint():
       return protected_endpoint()

6. Update frontend to:
   - Store JWT token after login
   - Send token in Authorization header: "Bearer <token>"
   - Handle token expiration and refresh

Example frontend usage:
======================

// After login
localStorage.setItem('authToken', response.data.token);

// For authenticated requests
const token = localStorage.getItem('authToken');
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Handle token expiration
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
""" 
"""
Authentication middleware for ComfyUI
Provides session-based authentication to protect routes
"""

import logging
import secrets
import time
import os
from aiohttp import web
from typing import Dict, Optional

# Load environment variables
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Session storage (in production, use Redis or database)
sessions: Dict[str, dict] = {}

# Session timeout in seconds (24 hours by default)
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 86400))

# Credentials from environment variables
VALID_USERNAME = os.getenv('COMFYUI_USERNAME', 'admin')
VALID_PASSWORD = os.getenv('COMFYUI_PASSWORD', 'wjsqnrai')

# API Key for external integrations (e.g., Open-WebUI)
API_KEY = os.getenv('API_KEY', None)

# Routes that don't require authentication
PUBLIC_ROUTES = {
    '/login.html',
    '/api/login',
    '/login',
    '/ws',  # WebSocket endpoint
}


def create_session(username: str) -> str:
    """Create a new session for the user"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        'username': username,
        'created_at': time.time(),
        'last_access': time.time()
    }
    logging.info(f"Session created for user: {username}")
    return session_id


def validate_session(session_id: str) -> bool:
    """Validate if session exists and is not expired"""
    if not session_id or session_id not in sessions:
        return False

    session = sessions[session_id]
    current_time = time.time()

    # Check if session expired
    if current_time - session['created_at'] > SESSION_TIMEOUT:
        del sessions[session_id]
        logging.info(f"Session expired and removed: {session_id[:8]}...")
        return False

    # Update last access time
    session['last_access'] = current_time
    return True


def destroy_session(session_id: str):
    """Destroy a session"""
    if session_id in sessions:
        username = sessions[session_id].get('username', 'unknown')
        del sessions[session_id]
        logging.info(f"Session destroyed for user: {username}")


def get_session_from_request(request: web.Request) -> Optional[str]:
    """Extract session ID from request cookies"""
    return request.cookies.get('comfyui_session')


def get_api_key_from_request(request: web.Request) -> Optional[str]:
    """Extract API key from request headers"""
    # Check Authorization header (Bearer token)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix

    # Check X-API-Key header
    return request.headers.get('X-API-Key')


def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    if not API_KEY:
        # API key authentication is disabled if not configured
        return False
    return api_key == API_KEY


def is_public_route(path: str) -> bool:
    """Check if the route is public (doesn't require auth)"""
    # Exact match for public routes
    if path in PUBLIC_ROUTES:
        return True

    # Allow static files for login page
    if path.startswith('/static/'):
        return True

    return False


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user with hardcoded credentials"""
    return username == VALID_USERNAME and password == VALID_PASSWORD


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """
    Authentication middleware
    - Checks for valid session on protected routes
    - Supports API key authentication for external integrations
    - Redirects to login page if not authenticated
    """

    path = request.path

    # Allow public routes (login page, login API, WebSocket)
    if is_public_route(path):
        return await handler(request)

    # Check for API key authentication first (for Open-WebUI and other integrations)
    api_key = get_api_key_from_request(request)
    if api_key and validate_api_key(api_key):
        logging.debug(f"Request authenticated via API key: {path}")
        return await handler(request)

    # Check for valid session (for web UI)
    session_id = get_session_from_request(request)

    if not validate_session(session_id):
        # No valid session - check if it's an API call or web page request
        if path.startswith('/api/'):
            # API call - return 401 Unauthorized
            return web.json_response(
                {'error': 'Unauthorized', 'message': 'Authentication required. Use session cookie or API key (Authorization: Bearer <key> or X-API-Key: <key>)'},
                status=401
            )
        else:
            # Web page request - redirect to login
            return web.Response(
                status=302,
                headers={'Location': '/login.html'}
            )

    # Valid session - proceed with request
    return await handler(request)

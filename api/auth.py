import jwt
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from functools import wraps
from typing import Optional, Dict, Any
from ninja.security import HttpBearer


class JWTAuth:
    """
    JWT Authentication utility class for handling token encoding/decoding
    """
    
    @staticmethod
    def encode_token(user_id: int, username: str) -> str:
        """
        Encode a JWT token with user information
        
        Args:
            user_id: The user's ID
            username: The user's username
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'username': username,
            'iat': int(now.timestamp()),  # issued at time
            'exp': int((now + timedelta(hours=24)).timestamp())  # expires in 24 hours
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing user info if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            print(f"DEBUG: Token decoded successfully. User ID: {payload.get('user_id')}, Expires: {datetime.fromtimestamp(payload.get('exp', 0))}")
            return payload
        except jwt.ExpiredSignatureError:
            print("DEBUG: Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"DEBUG: Invalid token error: {e}")
            return None
    
    @staticmethod
    def verify_token(token: str) -> Optional[User]:
        """
        Verify token and return user object if valid
        
        Args:
            token: JWT token string
            
        Returns:
            User object if token is valid, None otherwise
        """
        payload = JWTAuth.decode_token(token)
        if not payload:
            return None
            
        try:
            user = User.objects.get(id=payload['user_id'], username=payload['username'])
            return user
        except User.DoesNotExist:
            return None


class JWTCookieAuth:
    """
    Django Ninja JWT Authentication class that checks both Authorization header and cookies
    """
    def authenticate(self, request, token=None):
        # Debug: Print what we're receiving
        print(f"DEBUG: Headers: {dict(request.headers)}")
        print(f"DEBUG: Cookies: {request.COOKIES}")
        
        # First try to get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            print(f"DEBUG: Token from header: {token[:20]}...")
        # If no token in header, try to get from cookie
        elif not token and 'auth_token' in request.COOKIES:
            token = request.COOKIES['auth_token']
            print(f"DEBUG: Token from cookie: {token[:20]}...")
        else:
            print("DEBUG: No token found in header or cookies")
        
        if token:
            user = JWTAuth.verify_token(token)
            if user:
                print(f"DEBUG: Successfully authenticated user: {user.username}")
                return user
            else:
                print("DEBUG: Token verification failed")
        return None

    def __call__(self, request):
        return self.authenticate(request)


class JWTBearer(HttpBearer):
    """
    Django Ninja JWT Authentication class (Header-only for backward compatibility)
    """
    def authenticate(self, request, token):
        user = JWTAuth.verify_token(token)
        if user:
            return user
        return None


class AdminRequired:
    """
    Django Ninja Admin Authentication class that checks both Authorization header and cookies
    """
    def authenticate(self, request, token=None):
        # First try to get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        # If no token in header, try to get from cookie
        elif not token and 'auth_token' in request.COOKIES:
            token = request.COOKIES['auth_token']
        
        if token:
            user = JWTAuth.verify_token(token)
            if user and (user.is_staff or user.is_superuser):
                return user
        return None

    def __call__(self, request):
        return self.authenticate(request)


class BiroRequired:
    """
    Django Ninja Referee (Biro) Authentication class that checks both Authorization header and cookies
    """
    def authenticate(self, request, token=None):
        # First try to get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        # If no token in header, try to get from cookie
        elif not token and 'auth_token' in request.COOKIES:
            token = request.COOKIES['auth_token']
        
        if token:
            user = JWTAuth.verify_token(token)
            if user:
                try:
                    profile = user.profile
                    if profile.biro:
                        return user
                except AttributeError:
                    pass
        return None

    def __call__(self, request):
        return self.authenticate(request)


# Create instances for use in API endpoints
jwt_cookie_auth = JWTCookieAuth()  # New cookie-compatible auth
jwt_auth = JWTBearer()  # Keep for backward compatibility
admin_auth = AdminRequired()
biro_auth = BiroRequired()
import jwt
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from functools import wraps
from typing import Optional, Dict, Any


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
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
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


def jwt_required(view_func):
    """
    Decorator to require JWT authentication for views
    Looks for JWT token in cookies with name 'auth_token'
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get token from cookies
        token = request.COOKIES.get('auth_token')
        
        if not token:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'No authentication token provided'
            }, status=401)
        
        # Verify token
        user = JWTAuth.verify_token(token)
        if not user:
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'Authentication token is invalid or expired'
            }, status=401)
        
        # Add user to request
        request.user = user
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_required(view_func):
    """
    Decorator to require admin authentication for views
    Checks if user exists and has admin privileges (is_staff or is_superuser)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # First check JWT authentication
        token = request.COOKIES.get('auth_token')
        
        if not token:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'No authentication token provided'
            }, status=401)
        
        user = JWTAuth.verify_token(token)
        if not user:
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'Authentication token is invalid or expired'
            }, status=401)
        
        # Check if user has admin privileges
        if not (user.is_staff or user.is_superuser):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Admin privileges required'
            }, status=403)
        
        # Add user to request
        request.user = user
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def biro_required(view_func):
    """
    Decorator to require referee (biro) authentication for views
    Checks if user exists and has biro profile
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # First check JWT authentication
        token = request.COOKIES.get('auth_token')
        
        if not token:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'No authentication token provided'
            }, status=401)
        
        user = JWTAuth.verify_token(token)
        if not user:
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'Authentication token is invalid or expired'
            }, status=401)
        
        # Check if user has biro profile
        try:
            profile = user.profile
            if not profile.biro:
                return JsonResponse({
                    'error': 'Access denied',
                    'message': 'Referee privileges required'
                }, status=403)
        except AttributeError:
            return JsonResponse({
                'error': 'Access denied',
                'message': 'No profile found'
            }, status=403)
        
        # Add user to request
        request.user = user
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
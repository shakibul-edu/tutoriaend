from rest_framework.authentication import BaseAuthentication
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
import os
from dotenv import load_dotenv
load_dotenv()

User = get_user_model()

from drf_spectacular.extensions import OpenApiAuthenticationExtension

class GoogleIDTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                audience=os.getenv("GOOGLE_CLIENT_ID")  
            )

            if not idinfo.get("email_verified", False):
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed("User email is not verified.")

            email = idinfo["email"]
            sub = idinfo["sub"]
            username = idinfo["email"].split('@')[0]  # Use email prefix as username

            user, _ = User.objects.get_or_create(email=email, defaults={"username": username, "first_name": idinfo.get("given_name", ""), "last_name": idinfo.get("family_name", "")})
            return (user, None)
        except ValueError as e:
            from rest_framework.exceptions import AuthenticationFailed
            error_message = str(e)
            if "Token used too late" in error_message or "expired" in error_message:
                raise AuthenticationFailed("Token has expired.")
            raise AuthenticationFailed(f"Invalid token: {error_message}")

class GoogleIDTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'base.authentication.GoogleIDTokenAuthentication'
    name = 'GoogleIDTokenAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Google ID Token authentication using Bearer token in Authorization header.'
        }

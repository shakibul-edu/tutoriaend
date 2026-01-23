# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import TokenAuthentication
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import os
from dotenv import load_dotenv
load_dotenv()

User = get_user_model()


class GoogleLoginView(APIView):
    authentication_classes = []  # Disable JWT authentication for this view
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Missing Google ID token")

        token = auth_header.split(" ")[1]

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                audience=os.getenv("GOOGLE_CLIENT_ID"),
            )
        except ValueError:
            raise AuthenticationFailed("Invalid or expired Google token")

        if not idinfo.get("email_verified"):
            raise AuthenticationFailed("Email not verified")

        email = idinfo["email"]
        username = email.split("@")[0]

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", ""),
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.get_full_name(),
            }
        })

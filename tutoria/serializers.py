from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # The default result (access/refresh tokens)
        data = super().validate(attrs)

        # Custom data you want to include
        data.update({
            'user_id': self.user.id,
            'email': self.user.email,
            'is_teacher': getattr(self.user, 'is_teacher', False),
            'banned': getattr(self.user, 'banned', False),
        })

        # Optional: Prevent login if banned
        if getattr(self.user, 'banned', False):
             raise AuthenticationFailed("This account is banned.")

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        # The default result (new access token)
        data = super().validate(attrs)

        # We need to decode the refresh token to get the user ID
        refresh = RefreshToken(attrs['refresh'])
        
        try:
            user_id = refresh['user_id']
            user = User.objects.get(id=user_id)
        except (KeyError, User.DoesNotExist):
            raise InvalidToken("Invalid user associated with this token.")

        # Optional: Prevent refresh if banned
        if getattr(user, 'banned', False):
            raise AuthenticationFailed("This account is banned.")

        # Add custom fields to the refresh response
        data.update({
            'is_teacher': getattr(user, 'is_teacher'),
            'banned': getattr(user, 'banned')
        })

        return data
import firebase_admin
from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from user.models import User as BoilerMarketUser

class FirebaseEmailVerifiedAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None
        
        id_token = auth_header.split(" ")[-1]

        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired Firebase token")
        
        uid = decoded_token.get("uid")
        email_verified = decoded_token.get("email_verified")

        if not email_verified:
            raise AuthenticationFailed("Email not verified")
        boiler_market_user = BoilerMarketUser.objects.get(uid=uid)
        if not boiler_market_user:
            raise AuthenticationFailed("User not found")
        if not boiler_market_user.purdueEmailVerified:
            raise AuthenticationFailed("Purdue email not verified")
        
        user, created = User.objects.get_or_create(username=uid)
        return (user, None)

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None  # No token provided

        id_token = auth_header.split(" ")[-1]  # Extract token after "Bearer"

        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired Firebase token")

        uid = decoded_token.get("uid")

        # Check if the user exists in Django's User model, create if not
        user, created = User.objects.get_or_create(username=uid)

        return (user, None)  # DRF requires (user, auth)


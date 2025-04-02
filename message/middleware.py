from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from server.authentication import FirebaseEmailVerifiedAuthentication
from user.models import User as BoilerMarketUser

class FirebaseAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract the token from the query string
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]  # Get the first 'token' value if it exists

        if token:
            try:
                user = await database_sync_to_async(self.authenticate_user)(token)
                scope["user"] = user
            except AuthenticationFailed:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    def authenticate_user(self, token):
        # Reuse the logic from FirebaseEmailVerifiedAuthentication
        firebase_auth = FirebaseEmailVerifiedAuthentication()
        # Create a mock request object with headers for compatibility
        mock_request = type("Request", (object,), {"headers": {"Authorization": f"Bearer {token}"}})
        user, _ = firebase_auth.authenticate(mock_request)
        return user
from django.http import JsonResponse
from firebase_admin import auth
from functools import wraps

def firebase_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Authorization header required"}, status=401)

        try:
            token = auth_header.split(" ").pop()  # Extract token
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token  # Attach user info to request
        except Exception:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper

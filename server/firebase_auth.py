# server/authentication.py
import firebase_admin
from firebase_admin import auth
from django.http import JsonResponse
from functools import wraps
from user.models import User

def firebase_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JsonResponse({"error": "Authorization header required"}, status=401)
        try:
            # Expect header in the format "Bearer <token>"
            parts = auth_header.split(" ")
            if len(parts) != 2 or parts[0] != "Bearer":
                return JsonResponse({"error": "Invalid Authorization header format. Expected 'Bearer <token>'."}, status=401)
            token = parts[1]
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token.get("uid") or decoded_token.get("sub")
            user = User.objects.get(uid=uid)
            request.user = user
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

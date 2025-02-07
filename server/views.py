from django.http import HttpResponse

from server.firebase_auth import firebase_required

@firebase_required
def create_user(request):
    return HttpResponse("Create User")
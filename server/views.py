from django.http import HttpResponse

def create_user(request):
    return HttpResponse("Create User")
# pylint: disable=unused-argument
from django.core import serializers
from django.http import HttpResponse
from django.contrib.auth import authenticate
# from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token

from api.models import User, Event


def validate(request):
    """ Check the connection works """
    return HttpResponse("Success!", content_type="text/html")

# @login_required
def validateLogin(request):
    """ Check the login worked """
    if request.user.is_authenticated:
        return HttpResponse("Success!", content_type="text/html")
    return HttpResponse("Nope - permission denied", content_type="text/html", status = 401)

def getUser(request):
    """ Return all the info for a given user. Takes: id"""
    uid = request.GET.get("id", "")
    user = User.objects.get(pk = uid)
    userJson = serializers.serialize("json", user)
    return HttpResponse(userJson, content_type="application/json")


def getEvent(request):
    """ Return all the info for a event user. Takes: id"""
    uid = request.GET.get("id", "")
    event = Event.objects.get(pk = uid)
    eventJson = serializers.serialize("json", event)
    return HttpResponse(eventJson, content_type="application/json")


def apiLogin(request):
    """ Inital login API call - POST accepts 'username' and 'password' and returns a token"""
    username = request.POST.get("username", None)
    password = request.POST.get("password", None)

    # TODO: More Login validation? - check what did on RoosRun and mLab site
    user = authenticate(username=username, password=password)

    if user:
        token = Token.objects.get_or_create(user=user) # token, created
        return HttpResponse({'token': token.key})
    else:
        return HttpResponse({'error': 'Invalid credentials'}, status=401)
    
# pylint: disable=unused-argument
from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# import django.middleware.csrf as csrf
# from rest_framework.views import APIView
# from rest_framework.response import Response
from api.models import Event, User
import api.serializers as serializers

# Maybe TODO: look into class based views?

@ensure_csrf_cookie
def validate(request):
    """ Check the connection works """
    return HttpResponse("Success!", content_type="text/html")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validateLogin(request):
    """ Check the login worked """
    return HttpResponse("Success!", content_type="text/html")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUser(request):
    """ Return all the info for a given user. Takes: id"""
    uid = request.GET.get("id", "")
    user = User.objects.get(pk = uid)
    userJson = serializers.UserSerializer(user)
    return JsonResponse(userJson.data, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getEvent(request):
    """ Return all the info for a event user. Takes: id """
    uid = request.GET.get("id", "")
    event = Event.objects.get(pk = uid)
    eventJson = serializers.EventSerializer(event)
    return JsonResponse(eventJson.data, safe=False)





## In case we need later, here was an attempt at a custom login & token return implementation
# from django.contrib.auth import authenticate
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework.authtoken.models import Token

# @csrf_exempt
# def apiLogin(request):
#     """ Inital login API call - POST accepts 'username' and 'password' and returns a token"""
#     username = request.POST.get("username", None)
#     password = request.POST.get("password", None)

#     # TODO: More Login validation? - check what did on RoosRun and mLab site
#     user = authenticate(request, username=username, password=password)

#     if user:
#         token = Token.objects.get_or_create(user=user) # token, created
#         print(token)
#         return HttpResponse({'token': token[0]})
#     else:
#         return HttpResponse({'error': 'Invalid credentials'}, status=401)

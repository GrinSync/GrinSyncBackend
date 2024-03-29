# pylint: disable=unused-argument
from datetime import datetime
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

# import django.middleware.csrf as csrf
# from rest_framework.views import APIView
# from rest_framework.response import Response
from api.models import Event, User, Organization
import api.serializers as serializers

# Maybe TODO: look into class based views?

@ensure_csrf_cookie
@api_view(['GET'])
def validate(request):
    """ Check the connection works """
    return HttpResponse("Success!", content_type="text/html")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validateLogin(request):
    """ Check the login worked """
    return HttpResponse("Success!", content_type="text/html")

@api_view(['POST'])
def createUser(request):
    """ Creates a new user in the database """
    firstName = request.POST.get("first_name", None)
    lastName = request.POST.get("last_name", None)
    password = request.POST.get("password", None)
    userType = request.POST.get("type", None)
    email = request.POST.get("email", None)

    if not (firstName and lastName and password and userType and email):
        return JsonResponse({'error' : 'Integrity Error: Not all required fields were provided'},
                                safe=False, status = 400)

    try:
        user = User.objects.create_user(first_name = firstName, last_name = lastName,
                                        type = userType, email = email, username = email,
                                        password = password)
    except IntegrityError:
        return JsonResponse({'error' : 'Integrity Error: It\'s possible that username is already in use'},
                                safe=False, status = 400)

    return JsonResponse({'id' : user.id}, safe=False, status = 200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUser(request):
    """ Return all the info for a given user. Takes: id """
    uid = request.GET.get("id", "")
    try:
        user = User.objects.get(pk = uid)
    except ObjectDoesNotExist:
        return HttpResponse("User does not exist", status = 404)

    userJson = serializers.UserSerializer(user)
    return JsonResponse(userJson.data, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createEvent(request):
    """ Creates a new event in the database """
    title = request.POST.get("title", None)
    description = request.POST.get("description", "") # Optional
    orgID = request.POST.get("org_id", "") # Optional
    location = request.POST.get("location", None)
    studentsOnly = request.POST.get("studentsOnly", None)
    tags = request.POST.get("tags", "") # Optional?
    date = request.POST.get("date", None)

    if not (title and location and studentsOnly and date):
        return JsonResponse({'error' : 'Integrity Error: Not all required fields were provided'},
                                safe=False, status = 400)

    if orgID != "":
        hostOrg = Organization.objects.get(id=orgID)
    else:
        hostOrg = None

    try:
        split = date.split("-")
        startDT = datetime.strptime(split[0], "%m/%d/%Y %H:%M")
        endDT = datetime.strptime(split[1], "%m/%d/%Y %H:%M")
        assert startDT < endDT
    except (ValueError, AssertionError):
        return JsonResponse({'error' : 'Invalid DateTime: check your "date" field'},
                                safe=False, status = 400)


    # try:
    event = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    # location = location,
                                    start = startDT, end = endDT,
                                    description = description, studentsOnly = bool(studentsOnly),
                                    tags = tags)
    # except IntegrityError:
    #     return JsonResponse({'error' : 'Integrity Error: It\'s possible that event title is already in use'},
    #                             safe=False, status = 400)

    return JsonResponse({'id' : event.id}, safe=False, status = 200)

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

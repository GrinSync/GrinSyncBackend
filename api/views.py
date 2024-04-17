# pylint: disable=unused-argument
from datetime import datetime, timedelta
from dateutil import relativedelta
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authtoken.models import Token
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

    # Get the info from the request, and provide default values if the keys are not found
    # The POST.get here is because we've recieved a post request so we need to look for the info in that format
    firstName = request.POST.get("first_name", None)
    lastName = request.POST.get("last_name", None)
    password = request.POST.get("password", None)
    userType = request.POST.get("type", None)
    email = request.POST.get("email", None)

    # Check that all of the required fields were provided
    if not (firstName and lastName and password and userType and email):
        return JsonResponse({'error' : 'Integrity Error: Not all required fields were provided'},
                                safe=False, status = 400)

    # Actually interact with the database and create the user
    try:
        user = User.objects.create_user(first_name = firstName, last_name = lastName,
                                        type = userType, email = email, username = email,
                                        password = password)

    # Since the database constraints are checked at creation, make sure they all passed
    except IntegrityError:
        return JsonResponse({'error' : 'Integrity Error: It\'s possible that username is already in use'},
                                safe=False, status = 400)

    # Return the newly created user's id. Although the status code is probably more important
    return JsonResponse({'id' : user.id}, safe=False, status = 200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUser(request):
    """ Return all the info for a given user. Takes: id """

    # Get the desired user's ID from the request
    uid = request.GET.get("id", None)
    if not uid: # If they didn't provide an id, assume they want their own user info
        uid = Token.objects.get(key=request.auth.key).user_id

    # Check if there is a user with that id
    try:
        user = User.objects.get(pk = uid)
    except ObjectDoesNotExist:
        return HttpResponse("User does not exist", status = 404)

    # Seralize the user object and return that info
    userJson = serializers.UserSerializer(user)
    return JsonResponse(userJson.data, safe=False)

@api_view(['POST']) # Make sure the request is the correct format
@permission_classes([IsAuthenticated]) # Make sure the user is logged in
                        # When everyone needs to be logged in, his is prefered over an if statement in
                        # the function for versitility and security
def createEvent(request):
    """ Creates a new event in the database """

    # Get the info from the request, and provide default values if the keys are not found
    # The POST.get here is because we've sent a post request so we need to look for the info in that format
    title = request.POST.get("title", None)
    description = request.POST.get("description", "") # Optional
    orgID = request.POST.get("org_id", "") # Optional
    location = request.POST.get("location", None)
    studentsOnly = request.POST.get("studentsOnly", None)
    tags = request.POST.get("tags", "") # Optional?
    start = request.POST.get("start", None)
    end = request.POST.get("end", None)

    repeatDays = request.POST.get("repeatingDays", 0)
    repeatMonths = request.POST.get("repeatingMonths", 0)
    repeatEnd = request.POST.get("repeatDate", None)

    # Check that all of the required fields were provided
    if not (title and location and studentsOnly and start):
        return JsonResponse({'error' : 'Integrity Error: Not all required fields were provided'},
                                safe=False, status = 400)

    # Associate an event with an organization
    if orgID != "":
        hostOrg = Organization.objects.get(id=orgID)
    else:
        hostOrg = None

    # Turn the start and end times from a string to a datetime that we can actually work with
    try:
        startDT = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
        if end: # And end time is not required. If not provided we'll assume midnight
            endDT = datetime.strptime(end, "%Y-%m-%d %H:%M:%S.%f")
            assert startDT < endDT
        else:
            endDT = startDT.replace(hour=23, minute=59)
    except (ValueError, AssertionError):
        return JsonResponse({'error' : "Invalid DateTime: check your 'start' and 'end' fields"},
                                safe=False, status = 400)

    # Turn studentsOnly from a string to a bool
    studentsOnly = studentsOnly.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'no cap', 'uh-huh']


    # Stuff for repeating events
    if (repeatDays != 0) or (repeatMonths != 0):
        if not repeatEnd:
            return JsonResponse({'error' : "Field not found: All repeating events must have an end date"},
                                safe=False, status = 400)

        repeatEnd = datetime.strptime(repeatEnd, "%Y-%m-%d %H:%M:%S.%f").replace(hour=23, minute=59)
        offset = relativedelta.relativedelta(days=int(repeatDays), months=int(repeatMonths))
        firstEvent = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    location = location, start = startDT, end = endDT,
                                    description = description, studentsOnly =studentsOnly,
                                    tags = tags)

        prevEvent = firstEvent
        startDT = startDT + offset
        endDT = endDT + offset
        while startDT <= repeatEnd:
            event = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    location = location, start = startDT, end = endDT,
                                    description = description, studentsOnly =studentsOnly,
                                    tags = tags)
            prevEvent.nextRepeat = event
            prevEvent.save()
            prevEvent = event
            startDT = startDT + offset
            endDT = endDT + offset

        # Send the user back the information it'll need
        return JsonResponse({'id' : firstEvent.id}, safe=False, status = 200)



    # Actually interact with the database and create the event
    event = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    location = location, start = startDT, end = endDT,
                                    description = description, studentsOnly =studentsOnly,
                                    tags = tags)

    # Send the user back the information it'll need
    return JsonResponse({'id' : event.id}, safe=False, status = 200)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getEvent(request):
    """ Return all the info for an event. Takes: id """
    eid = request.GET.get("id", "")
    event = Event.objects.get(pk = eid)
    eventJson = serializers.EventSerializer(event)
    return JsonResponse(eventJson.data, safe=False)

@api_view(['GET'])
def search(request): # TODO: decide if want one search for everything or different for events vs users
    """ Return all the matching events for a given search. Takes: query """
    query = request.GET.get("query", None)
    if not query:
        return JsonResponse({'error' : "Required Argument 'query' was not provided"}, safe=False, status = 400)

    matching = (Event.objects.filter(title__contains = query) |
                    Event.objects.filter(location__contains = query)) # TODO: Sort by closeness to date not exceeding?

    # hide student-only events if user is not a student
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        matching = matching.exclude(studentsOnly = True)

    eventJson = serializers.EventSerializer(matching, many = True)
    return JsonResponse(eventJson.data, safe=False)

@api_view(['GET'])
def getAll(request):
    """ Return all the info for all events. """
    events = Event.objects.all()
    # Removes student-only events if user is not a student
    # We do this instead of the decorator for this function because everyone should be able to see public events
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        events = events.exclude(studentsOnly = True)
    eventsJson = serializers.EventSerializer(events, many = True) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getAllCreated(request):
    """ Return all the info for all events. """
    events = request.user.usersEvents
    eventsJson = serializers.EventSerializer(events, many = True) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['GET'])
def getUpcoming(request):
    """ Return all the info for upcoming events. """
    today = datetime.today().replace(minute=0) # assigns today's date to a variable
    upcoming = Event.objects.filter(start__gte=today) # gets events with a starting date >= to today
    upcoming = upcoming.exclude(start__gt = today + timedelta(weeks = 4)) # limits upcoming events a week out
    # hide student-only events if user is not a student
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        upcoming = upcoming.exclude(studentsOnly = True)
    upcoming = upcoming.order_by('start')
    eventsJson = serializers.EventSerializer(upcoming, many = True) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['GET'])
def getEventsInDay(request):
    """ Return the info for a day's events. """
    requestedDay = request.GET.get("start") # get the requested day
    eventsInDay = Event.objects.filter(start__gte=requestedDay) # get events that start on the request day
    eventsInDay = eventsInDay.exclude(start__gt = requestedDay + timedelta(day = 1)) # limits events to the requested day
    # hide student-only events if user is not a student
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        eventsInDay = eventsInDay.exclude(studentsOnly = True)
    eventsJson = serializers.EventSerializer(eventsInDay, many = True) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False) #returns the info that the user needs in JSON form

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def likeEvent(request):
    """ Adds an event to a user's like events list. Takes: id (of event) """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)

    user = request.user
    user.likedEvents.add(event)
    user.save()
    eventJson = serializers.EventSerializer(event)
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getlikedEvents(request):
    """ Return all of a users liked events. """
    user = request.user
    eventJson = serializers.EventSerializer(user.likedEvents.all(), many = True)
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def editEvent(request): # TODO: Test this more thoroughly 
    """ Edits the fields on an event. Takes: id (of event) """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)

    # Update the start and end times
    newStart = request.POST.get("start", None)
    newEnd = request.POST.get("end", None)
    if newStart:
        try:
            startDT = datetime.strptime(newStart, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return JsonResponse({'error' : "Invalid DateTime: check your 'start' and 'end' fields"},
                                    safe=False, status = 400)
    else:
        startDT = event.start

    if newEnd:
        try:
            endDT = datetime.strptime(newEnd, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return JsonResponse({'error' : "Invalid DateTime: check your 'start' and 'end' fields"},
                                    safe=False, status = 400)
    else:
        endDT = event.end

    try:
        assert event.start < event.end
    except AssertionError:
        return JsonResponse({'error' : "Invalid DateTime: your event start is after the end"},
                                safe=False, status = 400)

    startOffset = startDT - event.start
    endOffset = endDT - event.end
    newLocation = request.POST.get("location", None)
    newTitle = request.POST.get("title", None)
    newDescription = request.POST.get("description", None)
    newStudentsOnly = request.POST.get("studentsOnly", None)
    newTags = request.POST.get("tags", None)
    newRepeatEnd = request.POST.get("repeatDate", None)
    newRepeatEnd = datetime.strptime(newRepeatEnd, "%Y-%m-%d %H:%M:%S.%f").replace(hour=23, minute=59)

    firstEventpk = event.pk
    while event:
        nextEvent = event.nextRepeat
        # Allow users to cut off the repeat # TODO: Add the ability to extend the repeat
        if newRepeatEnd:
            if event.start <= newRepeatEnd:
                event.delete()
                event = nextEvent
                continue

        # Update the start and end times
        event.start = event.start + startOffset
        event.end = event.end + endOffset

        # Update the location
        if newLocation:
            event.location = newLocation

        # Update the title
        if newTitle:
            event.title = newTitle

        # Update the description
        if newDescription:
            event.description = newDescription

        # Update studentsOnly
        if newStudentsOnly:
            event.studentsOnly = newStudentsOnly.lower() in ['true', '1', 't', 'y', 'yes']

        # Update the tags
        if newTags:
            event.tags = newTags

        event.save()
        event = nextEvent

    return JsonResponse(firstEventpk, safe=False, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated]) #PLUS the user should have created the event
def deleteEvent(request):
    """ Delete an event. """
    eid = request.DELETE.get("id","") 
    try:
        event = Event.objects.get(pk = eid) 
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)
    
    #check that request.user = event.host are the same before deleting the vevent
    if(request.user == event.host):
        event.delete()
        eventJson = serializers.EventSerializer(event)
    else:
        return HttpResponse("This event can't be deleted because user is not the event's host.", status = 404)
    return JsonResponse(eventJson.data, safe=False, status = 200)


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

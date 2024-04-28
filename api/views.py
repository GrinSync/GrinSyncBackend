# pylint: disable=unused-argument
from datetime import datetime, timedelta
from smtplib import SMTPException

import pytz
from dateutil import relativedelta
from django.contrib.auth.tokens import default_token_generator
# from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated

import api.serializers as serializers
# import django.middleware.csrf as csrf
# from rest_framework.views import APIView
# from rest_framework.response import Response
from api.aux_functions import addEventTags
from api.models import Event, Organization, Tag, User

CST = pytz.timezone('America/Chicago')

def getAutoPopulatedEventUser():
    """ Just a universal way to make sure we can check who the default host for scraped events is """
    return User.objects.get(username="moderator")

# TODO: What happens if a non student creates a student only event? We prob let this happen, but can they edit it?

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


def sendEmailVerification(request, user):
    """ Generate a token for and send a verification email to the provided user """
    confirmationToken = default_token_generator.make_token(user)

    send_mail(
        "GrinSync Email Verification",
        ("Welcome to GrinSync! Please click here to verify your email: "
            f"{request.build_absolute_uri('/api/verifyUser')}?token={confirmationToken}&tempId={user.pk}"),
        "register@grinsync.com",
        [user.email],
        fail_silently=False,
    )
    return

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
    tags = request.POST.get("tags")

    # Check that all of the required fields were provided
    if not (firstName and lastName and password and userType and email):
        return JsonResponse({'error' : 'Integrity Error: Not all required fields were provided'},
                                safe=False, status = 400)

    # Make sure that student and faculty accounts have grinnell.edu emails for validation
    if ((userType == "STU") or (userType == "FAL")) and (email.split('@')[1].lower() != "grinnell.edu"):
        return JsonResponse({'error' :
                             'Account Validation Error: Student or Staff account registered without grinnell.edu email'},
                                safe=False, status = 422)

    # Actually interact with the database and create the user
    try:
        user = User.objects.create_user(first_name = firstName, last_name = lastName,
                                        type = userType, email = email.lower(), username = email.lower(),
                                        password = password, is_active = False)
        if tags:
            for tag in tags.split(','):
                try:
                    user.interestedTags.add(Tag.objects.get(name=tag))
                except ObjectDoesNotExist:
                    return JsonResponse({'error':f"Requested tag '{tag}' is not a valid tag"}, safe=False, status = 400)
        else:
            user.interestedTags.set(Tag.objects.filter(selectedDefault = True))
        user.save()

    # Since the database constraints are checked at creation, make sure they all passed
    except IntegrityError:
        # TODO: Check if same user exists but is just inactive. Don't leak info. Delete the inactive one
        return JsonResponse({'error' : 'Integrity Error: It\'s possible that username is already in use'},
                                safe=False, status = 400)

    try:
        sendEmailVerification(request, user)
    except SMTPException:
        user.delete()
        return JsonResponse({'error' : "Email failed to send, please try registering again"}, safe=False, status = 400)

    # Return the newly created user's id. Although the status code is probably more important
    return JsonResponse({'id' : user.id}, safe=False, status = 200)


@api_view(['GET'])
def verifyUser(request):
    """ Is called after we've verified their email; Moves a user to an active user status """
    userId = request.query_params.get('tempId', '')
    confirmationToken = request.query_params.get('token', '')
    try:
        user = User.objects.get(pk=userId)
    except ObjectDoesNotExist:
        return render(request, "registration/email_verification_error.html", {"errorMessage":
                'User not found', 
            }, status=400)
    if not default_token_generator.check_token(user, confirmationToken):
        return render(request, "registration/email_verification_error.html", {"errorMessage":
                'Token is invalid or expired. Please request another confirmation email by signing in.', 
            }, status=400)
    user.is_active = True
    user.save()
    return render(request, "registration/email_verification_confirmation.html")
    # return HttpResponse('Email successfully confirmed', status=200)

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
    title = request.POST.get("title", None) # TODO: Filter for profanity
    description = request.POST.get("description", "") # Optional
    orgID = request.POST.get("org_id", "") # Optional
    location = request.POST.get("location", None)
    studentsOnly = request.POST.get("studentsOnly", None)
    tags = request.POST.get("tags", "") # Optional?
    start = request.POST.get("start", None)
    end = request.POST.get("end", None)

    try:
        repeatDays = int(request.POST.get("repeatingDays", 0))
        repeatMonths = int(request.POST.get("repeatingMonths", 0))
        repeatEnd = request.POST.get("repeatDate", None)
    except ValueError:
        return JsonResponse({'error' : 'Value Error: Your repeatingDays or repeatingMonths are not integers'},
                                safe=False, status = 400)

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
        offset = relativedelta.relativedelta(days=repeatDays, months=repeatMonths)
        firstEvent = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    location = location, start = startDT, end = endDT,
                                    description = description, studentsOnly = studentsOnly)
        addEventTags(firstEvent, tags)

        prevEvent = firstEvent
        startDT = startDT + offset
        endDT = endDT + offset
        while startDT <= repeatEnd:
            event = Event.objects.create(host = request.user, parentOrg = hostOrg, title = title,
                                    location = location, start = startDT, end = endDT,
                                    description = description, studentsOnly = studentsOnly)
            addEventTags(event, tags)
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
                                    description = description, studentsOnly = studentsOnly)
    addEventTags(event, tags)

    # Send the user back the information it'll need
    return JsonResponse({'id' : event.id}, safe=False, status = 200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def updateInterestedTags(request):
    """ Updates an user's interested tags """
    tags = request.POST.get("tags", None)
    if not tags:
        return JsonResponse({'error' : 'No tag names provided'}, safe=False, status = 400)

    user = request.user
    user.interestedTags.clear()
    for tag in tags.split(','):
        try:
            user.interestedTags.add(Tag.objects.get(name=tag))
        except ObjectDoesNotExist:
            return JsonResponse({'error':f"Requested tag '{tag}' is not a valid tag"}, safe=False, status = 400)
    user.save()
    return JsonResponse('Success', safe=False, status = 200)


@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getEvent(request):
    """ Return all the info for an event. Takes: id """
    eid = request.GET.get("id", "")
    event = Event.objects.get(pk = eid)
    eventJson = serializers.EventSerializer(event, context={'request': request})
    return JsonResponse(eventJson.data, safe=False)

@api_view(['GET'])
def search(request): # TODO: decide if want one search for everything or different for events vs users
    """ Return all the matching events for a given search. Takes: query """
    tags = request.GET.get("tags", None) 
    query = request.GET.get("query", None)
    if not query:
        return JsonResponse({'error' : "Required Argument 'query' was not provided"}, safe=False, status = 400)

    matching = (Event.objects.filter(title__contains = query) |
                    Event.objects.filter(location__contains = query)) # TODO: Sort by closeness to date not exceeding?

    if tags: # If tags aren't provided, we'll assume we want all events that match
        tagObjs = []
        for tag in tags.split(','):
            # if tag == 'ALL': # If we want to support the "ALL" tag, but I think just not sending any will work
            #     tagObjs = Tag.objects.all()
            #     break
            try:
                tagObjs.append(Tag.objects.get(name=tag))
            except ObjectDoesNotExist:
                return JsonResponse({'error':f"Requested tag '{tag}' is not a valid tag"}, safe=False, status = 400)
        matching = matching.filter(tags__in = tagObjs)

    # hide student-only events if user is not a student
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        matching = matching.exclude(studentsOnly = True)

    eventJson = serializers.EventSerializer(matching, many = True, context={'request': request})
    return JsonResponse(eventJson.data, safe=False)

@api_view(['GET'])
def getAll(request):
    """ Return all the info for all events. """
    ## Do we want the calendar to update the tags by default?
    # tags = request.GET.get("tag", None)
    # if not tags: # This setup lets us do the default by not sending anything. Can't set no tags tho
    #     if request.user.is_authenticated: # If the user's logged in, use their defaults
    #         tags = request.user.interestedTags.all()
    #     else: # Otherwise, we'll use the universal defaults
    #         tags = Tag.objects.filter(selectedDefault = True)
    # else:
    #     tagObjs = []
    #     for tag in tags.split(','):
    #         if tag == 'ALL':
    #             tagObjs = "ALL"
    #             break
    #         try:
    #             tagObjs.append(Tag.objects.get(name=tag))
    #         except ObjectDoesNotExist:
    #             return JsonResponse({'error':f"Requested tag '{tag}' is not a valid tag"}, safe=False, status = 400)
    #     tags = tagObjs

    events = Event.objects.all()
    # events = events.filter(tags__in = tags)

    # Removes student-only events if user is not a student
    # We do this instead of the decorator for this function because everyone should be able to see public events
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        events = events.exclude(studentsOnly = True)
    eventsJson = serializers.EventSerializer(events, many = True, context={'request': request}) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getAllCreated(request):
    """ Return all the info for all events. """
    events = request.user.usersEvents
    events = events.order_by('-start')
    eventsJson = serializers.EventSerializer(events, many = True, context={'request': request}) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['GET'])
def getUpcoming(request):
    """ Return all the info for upcoming events. """
    tags = request.GET.get("tags", None)
    if not tags: # This setup lets us do the default by not sending anything. Can't set no tags tho
        if request.user.is_authenticated: # If the user's logged in, use their defaults
            tags = request.user.interestedTags.all()
        else: # Otherwise, we'll use the universal defaults
            tags = Tag.objects.filter(selectedDefault = True)
    else:
        tagObjs = []
        for tag in tags.split(','):
            if tag == 'ALL':
                tagObjs = "ALL"
                break
            try:
                tagObjs.append(Tag.objects.get(name=tag))
            except ObjectDoesNotExist:
                return JsonResponse({'error':f"Requested tag '{tag}' is not a valid tag"}, safe=False, status = 400)
        tags = tagObjs

    today = datetime.today().replace(minute=0) # assigns today's date to a variable
    upcoming = Event.objects.filter(start__gte=today) # gets events with a starting date >= to today
    upcoming = upcoming.exclude(start__gt = today + timedelta(weeks = 1)) # limits upcoming events a week out
    if tags != "ALL":
        upcoming = upcoming.filter(tags__in = tags)

    # hide student-only events if user is not a student
    if (not request.user.is_authenticated) or (request.user.type != "STU"):
        upcoming = upcoming.exclude(studentsOnly = True)
    upcoming = upcoming.order_by('start')
    eventsJson = serializers.EventSerializer(upcoming, many = True, context={'request': request}) #turns info into a string
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
    eventsJson = serializers.EventSerializer(eventsInDay, many = True,
                                             context={'request': request}) #turns info into a string
    return JsonResponse(eventsJson.data, safe=False) #returns the info that the user needs in JSON form

@api_view(['GET'])
def getTags(request):
    """ Return all the current tags. """
    tags = Tag.objects.all()
    tagsJson = serializers.TagSerializer(tags, many = True) #turns info into a string
    return JsonResponse(tagsJson.data, safe=False)  #returns the info that the user needs in JSON form

@api_view(['POST'])
@permission_classes([IsAdminUser]) # Make sure user is an admin
def createTag(request):
    """ Return all the info for all events. """
    name = request.POST.get("name", None) # get the requested day
    if not name:
        return JsonResponse({'error':"No 'name' field provided"}, safe=False, status = 400)

    try:
        tag = Tag.objects.create(name = name)
    except IntegrityError:
        return JsonResponse({'error':"A tag with that name already exists"}, safe=False, status = 400)
    return JsonResponse({'id':tag.id}, safe=False, status = 200)  #returns the info that the user needs in JSON form

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
    eventJson = serializers.EventSerializer(event, context={'request': request})
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def unlikeEvent(request):
    """ Adds an event to a user's like events list. Takes: id (of event) """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)

    user = request.user
    user.likedEvents.remove(event)
    user.save()
    eventJson = serializers.EventSerializer(event, context={'request': request})
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def toggleLikedEvent(request):
    """ Adds an event to a user's like events list. Takes: id (of event) """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)

    user = request.user
    if event in user.likedEvents.all():
        user.likedEvents.remove(event)
    else:
        user.likedEvents.add(event)
    user.save()
    eventJson = serializers.EventSerializer(event, context={'request': request})
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def getlikedEvents(request):
    """ Return all of a users liked events. """
    user = request.user
    eventJson = serializers.EventSerializer(user.likedEvents.all(), many = True, context={'request': request})
    return JsonResponse(eventJson.data, safe=False, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def editEvent(request):
    """ Edits the fields on an event. Takes: id (of event) """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return JsonResponse({'error':f"Event with id '{eid}' does not exist"}, status = 404)
    except ValueError:
        return JsonResponse({'error':"No id provided"}, status = 404)

    # Check that the user is a host
    if request.user != event.host: #TODO: Add a check that the user part of the student org
        return JsonResponse({'error':"This user is not the event's host"}, status = 403)

    #TODO: Add extending event, which means need to store repeat info

    # Update the start and end times
    newStart = request.POST.get("start", None)
    newEnd = request.POST.get("end", None)
    if newStart:
        try:
            startDT = datetime.strptime(newStart, "%Y-%m-%d %H:%M:%S.%f")
            # Idk if this is ideal but whatever. We should prob be making the front end send their timezone
        except ValueError:
            try:
                startDT = datetime.strptime(newStart, '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                return JsonResponse({'error' : "Invalid DateTime: check your 'start' and 'end' fields"},
                                    safe=False, status = 400)
        if startDT.tzinfo is None:
            startDT = CST.localize(startDT)
    else:
        startDT = event.start

    if newEnd:
        try:
            endDT = datetime.strptime(newEnd, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                endDT = datetime.strptime(newEnd, '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                return JsonResponse({'error' : "Invalid DateTime: check your 'start' and 'end' fields"},
                                    safe=False, status = 400)
        if endDT.tzinfo is None:
            endDT = CST.localize(endDT)
    else:
        endDT = event.end

    try:
        assert startDT < endDT
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
    if newRepeatEnd:
        try:
            newRepeatEnd = datetime.strptime(newRepeatEnd, "%Y-%m-%d %H:%M:%S.%f").replace(hour=23, minute=59)
        except ValueError:
            try:
                newRepeatEnd = datetime.strptime(newRepeatEnd, '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                return JsonResponse({'error' : "Invalid DateTime: check your 'repeatEnd' field"},
                                    safe=False, status = 400)
        if newRepeatEnd.tzinfo is None:
            newRepeatEnd = CST.localize(newRepeatEnd)

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
            tags = newTags.split(',')
            event.tags.clear()
            for tag in tags:
                event.tags.add(Tag.objects.get(name = tag))


        event.save()
        event = nextEvent

    return JsonResponse({"id":firstEventpk}, safe=False, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated]) #PLUS the user should have created the event
def deleteEvent(request):
    """ Delete an event. """
    eid = request.POST.get("id", "")
    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return HttpResponse(f"Event with id '{eid}' does not exist", status = 404)
    except ValueError:
        return HttpResponse("No id provided", status = 404)

    #check that request.user = event.host are the same before deleting the vevent
    if request.user == event.host:
        if hasattr(event, 'previousRepeat') and event.previousRepeat is not None:
                        # Nothing to do if it's the first event (also, it would handle
                        # it just fine if we didn't do this for the last event either, but whatever)
            prevEvent = event.previousRepeat
            prevEvent.nextRepeat = event.nextRepeat
            event.delete() # Need this order otherwise the 1-to-1 field doesn't allow it
            prevEvent.save()
        else:
            event.delete()
    else:
        return HttpResponse("This event can't be deleted because user is not the event's host.", status = 404)

    return JsonResponse("Success", safe=False, status = 200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserTags(request):
    """ Return a user's preferred tags. """
    user = request.user

    # Seralize the user object and return that info
    tagsJson = serializers.TagSerializer(user.interestedTags.all(), many = True)
    return JsonResponse(tagsJson.data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated]) # Make sure user is logged in
def claimEvent(request): #TODO: Frontend should have some sort of check or confirmation
    """ Requests ownership of an event populated by the calendar. Takes: id (of event) """
    eid = request.POST.get("id", None)
    if not eid:
        return JsonResponse({'error':"No 'id' field provided"}, safe = False, status = 400)

    try:
        event = Event.objects.get(pk = eid)
    except ObjectDoesNotExist:
        return JsonResponse({'error':'No event with the given event exists'}, safe = False, status = 400)

    if not event.contactEmail:
        return JsonResponse({'error':'This event is not claimable since there is no contact info'},
                             safe = False, status = 400)

    if event.host != getAutoPopulatedEventUser():
        return JsonResponse({'error':'This event is not claimable as someone already owns it'},
                             safe = False, status = 400)

    user = request.user

    if event.contactEmail.casefold() == user.email.casefold():
        event.host = user
        event.save()
        return JsonResponse("Success", safe = False, status = 200)

    confirmationToken = default_token_generator.make_token(user)

    send_mail(
        "GrinSync Event Claim",
        (f"Hi, this email was sent because { user.first_name } { user.last_name } would like to claim "
         f"overship for { event.title }; an auto-populated event for which you are the contact. If you "
         "would like ownership to be transfered, please click the following link: \n"
            f"{request.build_absolute_uri('/api/reassignEvent')}?"
                f"token={confirmationToken}&event={event.pk}&newHost={user.pk}"),
        "confirmation@grinsync.com",
        [event.contactEmail],
        fail_silently=False,
    )
    return JsonResponse("Confirmation Email Sent", safe = False, status = 200)


@api_view(['GET'])
def reassignEvent(request):
    """ Reassigns ownership to the requested user. Takes: id (of event) """
    token = request.GET.get("token", "")
    eid = request.GET.get("event", "")
    uid = request.GET.get("newHost", "")

    try:
        user = User.objects.get(pk=uid)
    except ObjectDoesNotExist:
        return render(request, "registration/email_verification_error.html", {"errorMessage":
                'User not found', 
            }, status=400)
    try:
        event = Event.objects.get(pk=eid)
    except ObjectDoesNotExist:
        return render(request, "registration/email_verification_error.html", {"errorMessage":
                'User not found', 
            }, status=400)

    if not default_token_generator.check_token(user, token):
        return render(request, "registration/email_verification_error.html", {"errorMessage":
                'Token is invalid or expired. Please request another confirmation email by signing in.', 
            }, status=400)

    event.host = user
    # TODO: Some sort of association of prev event.contact with user/org
    event.save()
    return render(request, "registration/event_verification_confirmation.html")

def tagManagerPage(request):
    """ A html page for us to manage the tags """
     # if this is a POST request we need to process the form data
    if request.method == "POST":
        # Get the monitor from the request
        defTags = request.POST.getlist('default_tags')
        allTags = list(set(request.POST.getlist('tag_ids')))

        for tagPK in allTags:
            tag = Tag.objects.get(pk=tagPK)
            tag.selectedDefault = (tagPK in defTags) #pylint: disable=C0325
            tag.save()


    tags = Tag.objects.all()

    return render(request, "tag_manager.html", {"tags" : tags})


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

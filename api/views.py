from django.shortcuts import render
from django.core import serializers
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect

from models import User, Event


def getUser(request):
    uid = request.GET.get("id", "")
    user = User.objects.get(pk = uid) 
    userJson = serializers.serialize("json", user)
    return HttpResponse(userJson, content_type="application/json")


def getEvent(request):
    uid = request.GET.get("id", "")
    event = Event.objects.get(pk = uid) 
    eventJson = serializers.serialize("json", event)
    return HttpResponse(eventJson, content_type="application/json")

from rest_framework import serializers
from .models import User, Event

class UserSerializer(serializers.ModelSerializer):
    """ Serializes a User model """
    class Meta:
        """ Meta """
        model = User
        fields = ['first_name', 'last_name', 'email', 'type']



class EventSerializer(serializers.ModelSerializer):
    """ Serializes an Event model """
    class Meta:
        """ Meta """
        model = Event
        fields = '__all__'

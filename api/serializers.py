from rest_framework import serializers
from .models import User, Event

class UserSerializer(serializers.ModelSerializer):
    """ Serializes a User model """
    class Meta:
        """ Meta """
        model = User
        fields = ['first_name', 'last_name', 'email', 'type', 'id']



class EventSerializer(serializers.ModelSerializer):
    """ Serializes an Event model """

    # Create a custom method field
    isFavorited = serializers.SerializerMethodField('_isFavorite')
    hostName = serializers.SerializerMethodField('_hostName')
    prevRepeat = serializers.SerializerMethodField('_prevRepeat')

    # Use this method for the custom field
    def _isFavorite(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            if obj.id in request.user.likedEvents.values_list('pk', flat=True):
                return True
        return False

    def _hostName(self, obj):
        if obj.parentOrg is not None:
            return obj.parentOrg.name
        return f"{obj.host.first_name} {obj.host.last_name}"

    def _prevRepeat(self, obj):
        if(hasattr(obj, 'previousRepeat')):
            return obj.previousRepeat.id
        return None


    class Meta:
        """ Meta """
        model = Event
        fields = '__all__'

    # def to_representation(self, instance):
    #     reps = super().to_representation(instance)
    #     print(reps)
    #     return reps

    # def __init__(self, instance):
    #     print(self)

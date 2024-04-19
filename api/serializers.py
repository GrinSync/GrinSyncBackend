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

    # Use this method for the custom field
    def _isFavorite(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            if obj.id in request.user.likedEvents.values_list('pk', flat=True):
                return True
        return False

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

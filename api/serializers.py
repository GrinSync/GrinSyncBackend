"""
This file contains a set of function which allow us to easily and consistently turn objects into JSON data we
can return to the client. In some of them, we create our own field to capture object relationship data that
isn't otherwise included from django by default.
"""
from rest_framework import serializers
from .models import Organization, Tag, User, Event

class UserSerializer(serializers.ModelSerializer):
    """ Serializes a User model """
    class Meta:
        """ Meta """
        model = User
        fields = ['first_name', 'last_name', 'email', 'type', 'id', 'interestedTags', 'childOrgs']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = []
        for tagPk in data['interestedTags']:
            tags.append(Tag.objects.get(pk=tagPk).name)

        data['interestedTags'] = tags

        # flatten the follower data with the user data
        return {**data}


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
        if hasattr(obj, 'previousRepeat'):
            return obj.previousRepeat.id
        return None


    class Meta:
        """ Meta """
        model = Event
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags = []
        for tagPk in data['tags']:
            tags.append(Tag.objects.get(pk=tagPk).name)

        data['tags'] = tags

        # flatten the follower data with the user data
        return {**data}

class TagSerializer(serializers.ModelSerializer):
    """ Serializes a Tag model """
    class Meta:
        """ Meta """
        model = Tag
        fields = ['name','id','selectedDefault']

class OrgSerializer(serializers.ModelSerializer):
    """ Serializes a Org model """
    orgEvents = serializers.SerializerMethodField('_orgEvents')
    isFollowed = serializers.SerializerMethodField('_isFollowed')

    # Use this method for the custom field
    def _orgEvents(self, obj):
        # eventIDs = []
        return list(map(lambda x : x.id, obj.childEvents.all()))

    def _isFollowed(self, obj):
        request = self.context.get('request', None)
        if not request:
            return None
        return request.user.is_authenticated and (obj.id in request.user.followedOrgs.values_list('pk', flat=True))
    class Meta:
        """ Meta """
        model = Organization
        fields = '__all__'

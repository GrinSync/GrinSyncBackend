import string
from django.core.exceptions import ObjectDoesNotExist
from api.models import Tag


## We'll define these funcitons here so that we can ensure consistent formatting in the tag names
# They save the event too, which feels harmless, but I'm not sure if it's really the behavior one would expect
def addEventTags(event, tags, create_new = False):
    """ Adds tags from the iterable to the given event """
    for tag in tags:
        if 'sport' in tag:
            tag = 'Sports'
        tag = tag.replace('&amp;','and')
        tag = string.capwords(tag)
        if create_new:
            tagObj, created = Tag.objects.get_or_create(name=tag) #pylint: disable=W0612
        else:
            try:
                tagObj = Tag.objects.get(name=tag)
            except ObjectDoesNotExist:
                continue
        event.tags.add(tagObj)
    event.save()
    return event

def setEventTags(event, tags, create_new = False):
    """ Set's an events tags to the provded tags"""
    event.tags.clear()
    return addEventTags(event, tags, create_new)

import string
from api.models import Tag

## We'll define these funcitons here so that we can ensure consistent formatting in the tag names
def addEventTags(event, tags):
    """ Adds tags from the iterable to the given event """
    event.tags.clear()
    for tag in tags:
        if 'sport' in tag:
            tag = 'Sports'
        tag = tag.replace('amp;','')
        tag = string.capwords(tag)
        tagObj, created = Tag.objects.get_or_create(name=tag)
        event.tags.add(tagObj)
    event.save()

def setEventTags(event, tags):
    """ Set's an events tags to the provded tags"""
    event.tags.clear()
    addEventTags(event, tags)

""" models.py - interfaces and structures the database """
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError


TYPES = [
    ("STU", "Grinnell College Student"),
    ("FAL", "Grinnell College Faculty"),
    ("COM", "Community Member"),
    (None, "-------"),
]


# Our basic user class. The AbstractUser class already implements names, email, & username/password
class User(AbstractUser):
    """ User Model - extends AbstractUser Model """
    # Whether they're student, faculty, or community
    TYPES = TYPES  # Need this so User.TYPES works later
    type = models.CharField(choices=TYPES, max_length=3, blank=False, default="COM")
    likedEvents = models.ManyToManyField('Event', blank=True, related_name="likedUsers")
    interestedTags = models.ManyToManyField('Tag', blank=True)

class Organization(models.Model):
    """ A model for a student org """
    name = models.CharField(max_length = 64, unique=True)
    email = models.EmailField(blank=False, null=False, unique=True)
    studentLeaders = models.ManyToManyField(User, blank=False, related_name='childOrgs')
    is_active = models.BooleanField(default=False) # Naming to keep consistent with django is_active for users

    # These are here solely so that we can make tokens for orgs
    last_login = models.DateTimeField(blank=True, null=True)
    password = models.CharField(default="HMMMMMMDOESTHISWORK?", max_length=64) # I don't care if this makes the token less
    # ^ DON'T USE THIS FOR ANYTHING                             secure, we're just using it for email confirmation anyways

    def get_email_field_name(self): #pylint: disable=C0103
        """ Yeah, just here so the token thing doesn't flip """
        return 'email'

class Tag(models.Model):
    """ A model for event filtering tags """
    name = models.CharField(max_length=32, unique=True)
    selectedDefault = models.BooleanField(default=False)

# The model for events. This will probably be the main model we're dealing with
class Event(models.Model):
    """ Event Model - stores info for the events we're going to serve """
    # Basic event info
    host = models.ForeignKey(User, related_name='usersEvents', on_delete = models.DO_NOTHING)
    parentOrg = models.ForeignKey(Organization, blank = True, null = True, on_delete = models.DO_NOTHING)
    title = models.CharField(max_length = 64)
    description = models.TextField(blank = True)
    start = models.DateTimeField(blank = False, null = False)
    end = models.DateTimeField(blank = False, null = False)
    location = models.CharField(max_length = 64, blank = True, null = True)
    ## TODO: Should we make it so people can search by location? If so use ForeignKey

    # Other stuff we might want to record about events
    studentsOnly = models.BooleanField(blank = False) # We'll store this as its own field for later
    tags = models.ManyToManyField(Tag, blank=True)

    # For repeating events
    nextRepeat = models.OneToOneField('Event', blank = True, null=True, related_name="previousRepeat",
                                      on_delete=models.SET_NULL)

    # External Infomation
    liveWhaleID = models.PositiveIntegerField(blank=True, null=True, unique=True)
    contactEmail = models.EmailField(blank=True, null=True)
    # Also maybe geolocation info?

    def save(self, *args, **kwargs): # pylint: disable=unused-argument
        if self.host is None and self.parentOrg is None:
            raise ValidationError("Events must have a host or hosting org")

        return super().save()

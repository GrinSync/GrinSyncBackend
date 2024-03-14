""" models.py - interfaces and structures the database """
from django.db import models
from django.contrib.auth.models import AbstractUser


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


class Organization(models.Model):
    """ A model for a student org """
    name = models.CharField(max_length = 64)
    studentLeaders = models.ManyToManyField(User, blank=False, related_name='childOrgs')


# The model for events. This will probably be the main model we're dealing with
class Event(models.Model):
    """ Event Model - stores info for the events we're going to serve """
    # Basic event info
    host = models.ForeignKey(User, on_delete = models.PROTECT)
    parentOrg = models.ForeignKey(Organization, blank = True, on_delete = models.PROTECT)
    title = models.CharField(max_length = 64)
    description = models.TextField(blank = True)
    start = models.DateTimeField(blank = False, null = False)
    end = models.DateTimeField(blank = False, null = False)
    # location = models.CharField()
    ## TODO: Should we make it so people can search by location? If so use ForeignKey

    # Other stuff we might want to record about events
    studentsOnly = models.BooleanField(blank = False) # We'll store this as its own field for later
    tags = models.JSONField(blank = True, null = True)

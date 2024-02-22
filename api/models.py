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
    # Whether they're student, faculty, or community
    TYPES = TYPES  # Need this so User.TYPES works later
    type = models.CharField(choices=TYPES, max_length=3, blank=False, default=None)


# The model for events. This will probably be the main model we're dealing with
class Event(models.Model):
    # Basic event info
    host = models.ForeignKey(User)
    start = models.DateTimeField(blank = False, null = False)
    end = models.DateTimeField(blank = False, null = False)
    # location = models.CharField() ## TODO: Should we make it so people can search by location? If so then we make a model class too and use ForeignKey
    
    # Other stuff we might want to record about events
    studentsOnly = models.BooleanField() # We'll store this as its own field for ease of use later
    tags = models.JSONField()



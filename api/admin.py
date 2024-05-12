from django.contrib import admin
from api.models import User, Event, Organization, Tag

# Registering these models means that we can access them on the admin site, allowing for easy modification
admin.site.register(User)
admin.site.register(Event)
admin.site.register(Organization)
admin.site.register(Tag)

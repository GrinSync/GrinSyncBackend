from django.contrib import admin
from api.models import User, Event, Organization, Tag

# Register your models here.
admin.site.register(User)
admin.site.register(Event)
admin.site.register(Organization)
admin.site.register(Tag)

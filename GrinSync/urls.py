"""
URL configuration for GrinSync project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views as tokenViews
from api import views as apiViews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/search', apiViews.search, name = 'search'),
    path('api/getUser', apiViews.getUser, name = 'getUser'),
    path('api/getEvent', apiViews.getEvent, name = 'getEvent'),
    path('api/getAll', apiViews.getAll, name = 'getAll'),
    path('api/getCreatedEvents', apiViews.getAllCreated, name = 'getCreatedEvents'),
    path('api/getLikedEvents', apiViews.getlikedEvents, name = 'getLikedEvents'),
    path('api/likeEvent', apiViews.likeEvent, name = 'likeEvent'),
    path('api/unlikeEvent', apiViews.unlikeEvent, name = 'likeEvent'),
    path('api/toggleLikedEvent', apiViews.toggleLikedEvent, name = 'likeEvent'),
    path('api/editEvent', apiViews.editEvent, name = 'editEvent'),
    path('api/deleteEvent', apiViews.deleteEvent, name = 'deleteEvent'),
    path('api/upcoming', apiViews.getUpcoming, name = 'getUpcomming'),
    path('api/getAllTags', apiViews.getTags, name = 'getAllTags'),
    path('api/getUserTags', apiViews.getUserTags, name = 'getUsersTags'),
    path('api/auth', tokenViews.obtain_auth_token),
    path('auth/', include('django.contrib.auth.urls')),
    path('api/validate/login', apiViews.validateLogin, name = 'vallog'),
    path('api/validate', apiViews.validate, name = 'val'),
    path('api/create/user', apiViews.createUser, name = 'newUser'),
    path('api/verifyUser', apiViews.verifyUser, name = 'newUser'),
    path('api/create/event', apiViews.createEvent, name = 'newEvent'),
    path('api/create/tag', apiViews.createTag, name = 'newTag'),
    path('api/updateInterestedTags', apiViews.updateInterestedTags, name = 'updateTags'),
    path('api/claimEvent', apiViews.claimEvent, name = 'newTag'),
    path('api/reassignEvent', apiViews.reassignEvent, name = 'newTag'),
    path('tags/', apiViews.tagManagerPage, name = 'tagManager'),
]

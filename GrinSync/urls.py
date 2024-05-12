"""
This file tells django where to direct each incoming request.

Each url is linked to a function. Currently these are all in one file, but we should probably change that, 
I'm just too worried it would break something. 
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken import views as tokenViews
from api import views as apiViews

urlpatterns = [
    path('', apiViews.home, name = 'homePage'),
    path('admin/', admin.site.urls),
    path('accounts/', include("django.contrib.auth.urls")),
    path('api/search', apiViews.search, name = 'search'),
    path('api/getUser', apiViews.getUser, name = 'getUser'),
    path('api/getEvent', apiViews.getEvent, name = 'getEvent'),
    path('api/getAll', apiViews.getAll, name = 'getAll'),
    path('api/getCreatedEvents', apiViews.getAllCreated, name = 'getCreatedEvents'),
    path('api/getLikedEvents', apiViews.getLikedEvents, name = 'getLikedEvents'),
    path('api/likeEvent', apiViews.likeEvent, name = 'likeEvent'),
    path('api/unlikeEvent', apiViews.unlikeEvent, name = 'unlikeEvent'),
    path('api/toggleLikedEvent', apiViews.toggleLikedEvent, name = 'toggleLikedEvent'),
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
    path('api/claimEvent', apiViews.claimEvent, name = 'claimEvent'),
    path('api/reassignEvent', apiViews.reassignEvent, name = 'reassEvent'),
    path('api/create/org', apiViews.createOrg, name = 'newOrg'),
    path('api/confirmOrg', apiViews.confirmOrg, name = 'addCoLead'),
    path('api/claimOrg', apiViews.claimOrg, name = 'claimOrg'),
    path('api/confirmOrgClaim', apiViews.confirmOrgClaim, name = 'addCoLead'),
    path('api/getOrg', apiViews.getOrg, name = 'getOrg'),
    path('api/getUserOrgs', apiViews.getUserOrgs, name = 'usersOrgs'),
    path('api/getAllOrgs', apiViews.getAllOrgs, name = 'allOrgs'),
    path('api/getOrgEvents', apiViews.getOrgEvents, name = 'getOrgsEvents'),
    path('api/getFollowedOrgs', apiViews.getFollowedOrgs, name = 'getFollowedOrgs'),
    path('api/followOrg', apiViews.followOrg, name = 'followOrg'),
    path('api/unfollowOrg', apiViews.unfollowOrg, name = 'unfollowOrg'),
    path('api/toggleFollowedOrg', apiViews.toggleFollowedOrg, name = 'toggleFollowedOrg'),
    path('deleteAccount/', apiViews.deleteAccount, name = 'accountDeletion'),
    path('tags/', apiViews.tagManagerPage, name = 'tagManager'),
]
